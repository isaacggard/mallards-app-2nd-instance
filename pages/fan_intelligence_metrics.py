import numpy as np
import pandas as pd
import streamlit as st


DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
FAN_WORKING_COLUMNS = [
    "fan_key",
    "merch_net_total",
    "total_ticket_spend",
    "total_tickets",
    "first_game",
    "last_game",
    "games_attended",
    "is_merch_buyer",
    "most_common_section",
    "ticket_type",
]
SECTION_ORDER = [
    "100 Level",
    "200 Level",
    "Other",
    "Duck Blind",
    "General Admission",
    "Arch Solar Suites",
]


def normalize_column_name(column: object) -> str:
    return " ".join(str(column).strip().lower().split())


def find_column(df: pd.DataFrame, column: str) -> str | None:
    lookup = {normalize_column_name(col): col for col in df.columns}
    return lookup.get(normalize_column_name(column))


def source_column(df: pd.DataFrame, column: str) -> pd.Series:
    resolved = find_column(df, column)
    if resolved:
        return df[resolved]
    return pd.Series(pd.NA, index=df.index)


def safe_divide(numerator: float, denominator: float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def build_section_group(section_series: pd.Series) -> pd.Series:
    section_text = section_series.astype("string").str.lower().str.strip()
    numeric_section = pd.to_numeric(
        section_text.str.extract(r"(\d{3})", expand=False),
        errors="coerce",
    )

    grouped = pd.Series("Other", index=section_series.index, dtype="string")
    grouped = grouped.mask(numeric_section.between(100, 199).fillna(False), "100 Level")
    grouped = grouped.mask(numeric_section.between(200, 299).fillna(False), "200 Level")
    grouped = grouped.mask(
        section_text.str.contains(r"general admission|\bga\b", regex=True, na=False),
        "General Admission",
    )
    grouped = grouped.mask(section_text.str.contains("duck blind", na=False), "Duck Blind")
    grouped = grouped.mask(
        section_text.str.contains("arch", na=False),
        "Arch Solar Suites",
    )
    return grouped


def prepare_fan_layer(full_fan_master: pd.DataFrame) -> pd.DataFrame:
    df = pd.DataFrame(
        {column: source_column(full_fan_master, column) for column in FAN_WORKING_COLUMNS}
    )
    for column in ["merch_net_total", "total_ticket_spend", "total_tickets"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)
    for column in ["games_attended", "is_merch_buyer"]:
        df[column] = pd.to_numeric(df[column], errors="coerce").fillna(0.0)

    df["first_game"] = pd.to_datetime(df["first_game"], errors="coerce")
    df["last_game"] = pd.to_datetime(df["last_game"], errors="coerce")
    df["total_spend"] = df["merch_net_total"] + df["total_ticket_spend"]
    df["spend_per_ticket"] = (df["total_spend"] / df["total_tickets"]).replace(
        [np.inf, -np.inf],
        np.nan,
    )
    df["tenure_days"] = (df["last_game"] - df["first_game"]).dt.days.fillna(0.0)
    df["section_group"] = build_section_group(df["most_common_section"])
    df["ticket_type_clean"] = df["ticket_type"].astype("string").str.strip().str.lower()
    return df


def weighted_spend_per_ticket(df: pd.DataFrame) -> float:
    return safe_divide(float(df["total_spend"].sum()), float(df["total_tickets"].sum()))


def weighted_spend_by_group(
    df: pd.DataFrame,
    group_column: str,
    name: str = "avg_spend_per_ticket",
    group_order: list[str] | None = None,
) -> pd.Series:
    grouped = df.groupby(group_column, observed=False).agg(
        total_spend=("total_spend", "sum"),
        total_tickets=("total_tickets", "sum"),
    )
    if grouped.empty:
        return pd.Series(dtype="float64", name=name)

    result = (grouped["total_spend"] / grouped["total_tickets"]).replace(
        [np.inf, -np.inf],
        np.nan,
    )
    if group_order is not None:
        result = result.reindex(group_order)
    return result.dropna().rename(name)


def build_ticket_spend_distribution(df: pd.DataFrame) -> pd.Series:
    spend = df.loc[
        df["spend_per_ticket"].ge(0) & df["spend_per_ticket"].notna(),
        "spend_per_ticket",
    ]
    if spend.empty:
        return pd.Series(dtype="int64")

    bin_edges = [0, 10, 20, 35, 50, 75, 100, np.inf]
    labels = [
        "$0-$10",
        "$10-$20",
        "$20-$35",
        "$35-$50",
        "$50-$75",
        "$75-$100",
        "$100+",
    ]
    return pd.cut(spend, bins=bin_edges, labels=labels, include_lowest=True).value_counts(
        sort=False,
    ).rename("fan_count")


def build_tenure_spend_by_bin(df: pd.DataFrame) -> pd.Series:
    tenure_df = df[["tenure_days", "total_spend", "total_tickets"]].dropna().copy()
    if tenure_df.empty:
        return pd.Series(dtype="float64")

    bins = [-0.1, 30, 90, 180, 365, 730, np.inf]
    labels = [
        "0-30 Days",
        "31-90 Days",
        "91-180 Days",
        "181-365 Days",
        "1-2 Years",
        "2+ Years",
    ]
    tenure_df["tenure_bin"] = pd.cut(tenure_df["tenure_days"], bins=bins, labels=labels)
    return weighted_spend_by_group(tenure_df, "tenure_bin")


def build_ticket_sales_by_day_of_week(df: pd.DataFrame) -> pd.Series:
    single_game = df[
        df["ticket_type_clean"].eq("single") & df["first_game"].notna()
    ].copy()
    if single_game.empty:
        return pd.Series(dtype="float64")

    single_game["weekday_number"] = single_game["first_game"].dt.dayofweek
    single_game["day_of_week"] = single_game["weekday_number"].map(
        {index: day for index, day in enumerate(DAY_ORDER)}
    )
    return (
        single_game.groupby(["weekday_number", "day_of_week"], observed=True)[
            "total_tickets"
        ]
        .sum()
        .sort_index(level="weekday_number")
        .droplevel("weekday_number")
        .rename("total_tickets")
    )


def build_games_attended_distribution(df: pd.DataFrame) -> pd.Series:
    games = df.loc[df["games_attended"].gt(0), "games_attended"].round().astype("int64")
    if games.empty:
        return pd.Series(dtype="int64")
    return games.value_counts(sort=False).sort_index().rename("fan_count")


@st.cache_data(show_spinner=False, max_entries=1)
def prepare_fan_intelligence_metrics(full_fan_master: pd.DataFrame) -> dict:
    df = prepare_fan_layer(full_fan_master)
    unique_fans = int(df["fan_key"].nunique())
    total_tickets = float(df["total_tickets"].sum())

    return {
        "kpis": {
            "unique_fans": unique_fans,
            "total_tickets": int(total_tickets),
            "avg_revenue_per_ticket": weighted_spend_per_ticket(df),
            "multi_game_rate": df["games_attended"].gt(1).mean(),
            "merch_conversion_rate": df["is_merch_buyer"].mean(),
            "avg_games_attended": df["games_attended"].mean(),
        },
        "charts": {
            "ticket_spend_distribution": build_ticket_spend_distribution(df),
            "revenue_by_section": weighted_spend_by_group(
                df,
                "section_group",
                group_order=SECTION_ORDER,
            ),
            "merch_conversion_by_section": (
                df.groupby("section_group", observed=False)["is_merch_buyer"]
                .mean()
                .reindex(SECTION_ORDER)
                .dropna()
                .rename("merch_conversion_rate")
            ),
            "average_spend_by_merch_buyer": weighted_spend_by_group(
                df,
                "is_merch_buyer",
            ).rename(index={0.0: "Non-Buyer", 1.0: "Buyer"}),
            "tenure_spend_by_bin": build_tenure_spend_by_bin(df),
            "ticket_sales_by_day_of_week": build_ticket_sales_by_day_of_week(df),
            "games_attended_distribution": build_games_attended_distribution(df),
        },
        "metadata": {
            "first_game": df["first_game"].min(),
            "last_game": df["last_game"].max(),
        },
    }
