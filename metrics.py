import re
import time
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


# =============================================================================
# Shared Metric Helpers
# =============================================================================
def normalize_column_name(column: Any) -> str:
    return " ".join(str(column).strip().lower().split())


def find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    normalized_lookup = {
        normalize_column_name(column): column for column in df.columns
    }
    for candidate in candidates:
        normalized_candidate = normalize_column_name(candidate)
        if normalized_candidate in normalized_lookup:
            return normalized_lookup[normalized_candidate]
    return None


def to_numeric_preserve_index(series: pd.Series) -> pd.Series:
    cleaned_series = (
        series.astype(str)
        .str.replace(r"[\$, ]", "", regex=True)
        .replace(["-", "", "None", "nan", "null", "<NA>"], "0")
    )
    return pd.to_numeric(cleaned_series, errors="coerce").fillna(0.0)


def empty_chart(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


# =============================================================================
# Transaction Insights Page Metrics
# =============================================================================
REQUIRED_TRANSACTION_COLUMNS = {
    "date": ["Date"],
    "time": ["Time"],
    "net_sales": ["Net Sales"],
    "location": ["Location"],
    "device_name": ["Device Name"],
    "transaction_id": ["Transaction ID"],
    "partial_refunds": ["Partial Refunds"],
}
TRANSACTION_METRIC_SCHEMA_VERSION = "transaction_v5"
DAY_ORDER = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
STAND_LOCATION_ORDER = [
    "Short Hops Beer",
    "Backstop Brews",
    "Festival Concessions",
    "Let's Get Fried",
    "TDS Concessions",
    "Merchandise Store",
    "Sweet Treats",
]


def clean_device_name(device_series: pd.Series) -> pd.Series:
    clean_device = (
        device_series.astype("string")
        .fillna("unknown")
        .str.lower()
        .str.replace(r"\d+", "", regex=True)
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    return clean_device.replace("", "unknown").fillna("unknown")


def map_stand_location(device_series: pd.Series) -> pd.Series:
    device_text = clean_device_name(device_series)
    stand_location = pd.Series(pd.NA, index=device_series.index, dtype="string")
    stand_location = stand_location.mask(
        device_text.str.contains(r"short\s*hops|shorthops", regex=True, na=False),
        "Short Hops Beer",
    )
    stand_location = stand_location.mask(
        device_text.str.contains(r"backstop\s*(?:beer|brew)", regex=True, na=False),
        "Backstop Brews",
    )
    stand_location = stand_location.mask(
        device_text.str.contains("festival", na=False),
        "Festival Concessions",
    )
    stand_location = stand_location.mask(
        device_text.str.contains(r"lets\s*get\s*fried", regex=True, na=False),
        "Let's Get Fried",
    )
    stand_location = stand_location.mask(
        device_text.str.contains(r"\btds\b", regex=True, na=False),
        "TDS Concessions",
    )
    stand_location = stand_location.mask(
        device_text.str.contains(r"merch\s*store|team\s*store", regex=True, na=False),
        "Merchandise Store",
    )
    stand_location = stand_location.mask(
        device_text.str.contains(r"sweet\s*treats", regex=True, na=False),
        "Sweet Treats",
    )
    return stand_location


def classify_location(location_series: pd.Series) -> pd.Series:
    location_text = location_series.astype("string").fillna("").str.lower()
    food_mask = location_text.str.contains(
        r"food|f&b|f\s+and\s+b|bev|beverage|concession|stand",
        regex=True,
        na=False,
    )
    merch_mask = location_text.str.contains(
        r"merch|store",
        regex=True,
        na=False,
    )
    location_type = pd.Series("Other", index=location_series.index, dtype="string")
    location_type = location_type.mask(food_mask, "Food & Beverage")
    location_type = location_type.mask(~food_mask & merch_mask, "Merchandise")
    return location_type


def build_yearly_revenue(df: pd.DataFrame) -> pd.DataFrame:
    yearly = (
        df.dropna(subset=["year"])
        .groupby("year", as_index=False, observed=True)["net_sales"]
        .sum()
        .sort_values("year")
    )
    return yearly if not yearly.empty else empty_chart(["year", "net_sales"])


def build_stand_revenue(df: pd.DataFrame) -> pd.DataFrame:
    stand_revenue = (
        df.dropna(subset=["stand_location"])
        .groupby("stand_location", as_index=False, observed=True)["net_sales"]
        .sum()
    )
    stand_revenue = stand_revenue.sort_values("net_sales", ascending=False)
    return (
        stand_revenue
        if not stand_revenue.empty
        else empty_chart(["stand_location", "net_sales"])
    )


def build_transaction_size_distribution(df: pd.DataFrame) -> pd.DataFrame:
    sales = df.loc[df["net_sales"].ge(0), "net_sales"].dropna()
    if sales.empty:
        return empty_chart(["sales_range", "count"])

    bin_edges = [0, 25, 50, 75, 100, 200, np.inf]
    labels = ["$0-$25", "$25-$50", "$50-$75", "$75-$100", "$100-$200", "$200+"]
    sales_bins = pd.cut(
        sales,
        bins=bin_edges,
        labels=labels,
        include_lowest=True,
    )
    distribution = (
        sales_bins.value_counts(sort=False)
        .rename_axis("sales_range")
        .reset_index(name="count")
    )
    distribution["sales_range"] = distribution["sales_range"].astype(str)
    return distribution


def build_revenue_by_day_of_week(df: pd.DataFrame) -> pd.DataFrame:
    day_revenue = (
        df.dropna(subset=["weekday_number"])
        .groupby(["weekday_number", "day_of_week"], as_index=False, observed=True)[
            "net_sales"
        ]
        .sum()
        .sort_values("weekday_number")
        .drop(columns=["weekday_number"])
    )
    return (
        day_revenue
        if not day_revenue.empty
        else empty_chart(["day_of_week", "net_sales"])
    )


def build_device_efficiency(df: pd.DataFrame) -> pd.DataFrame:
    device_efficiency = (
        df.dropna(subset=["stand_location"])
        .groupby("stand_location", as_index=False, observed=True)
        .agg(
            avg_transaction_value=("net_sales", "mean"),
            transaction_count=("net_sales", "size"),
            total_revenue=("net_sales", "sum"),
        )
    )
    device_efficiency["stand_location"] = pd.Categorical(
        device_efficiency["stand_location"],
        categories=STAND_LOCATION_ORDER,
        ordered=True,
    )
    device_efficiency = (
        device_efficiency.sort_values(
            "avg_transaction_value",
            ascending=False,
        ).drop(columns=["total_revenue"])
    )
    return (
        device_efficiency
        if not device_efficiency.empty
        else empty_chart(
            ["stand_location", "avg_transaction_value", "transaction_count"]
        )
    )


def build_cumulative_revenue(df: pd.DataFrame) -> pd.DataFrame:
    cumulative = (
        df.dropna(subset=["transaction_date"])
        .groupby("transaction_date", as_index=False, observed=True)["net_sales"]
        .sum()
        .sort_values("transaction_date")
        .rename(columns={"transaction_date": "date"})
    )
    if cumulative.empty:
        return empty_chart(["date", "cumulative_net_sales"])

    cumulative["cumulative_net_sales"] = cumulative["net_sales"].cumsum()
    return cumulative[["date", "cumulative_net_sales"]]


@st.cache_data(show_spinner=False)
def prepare_transaction_insights_metrics(transaction_df: pd.DataFrame) -> dict:
    resolved_columns = {
        key: find_column(transaction_df, candidates)
        for key, candidates in REQUIRED_TRANSACTION_COLUMNS.items()
    }
    row_index = transaction_df.index

    df = pd.DataFrame(
        {
            "date_raw": (
                transaction_df[resolved_columns["date"]]
                if resolved_columns["date"]
                else pd.Series(pd.NA, index=row_index)
            ),
            "time_raw": (
                transaction_df[resolved_columns["time"]]
                if resolved_columns["time"]
                else pd.Series(pd.NA, index=row_index)
            ),
            "net_sales": (
                transaction_df[resolved_columns["net_sales"]]
                if resolved_columns["net_sales"]
                else pd.Series(0.0, index=row_index)
            ),
            "location": (
                transaction_df[resolved_columns["location"]]
                if resolved_columns["location"]
                else pd.Series("unknown", index=row_index)
            ),
            "device_name": (
                transaction_df[resolved_columns["device_name"]]
                if resolved_columns["device_name"]
                else pd.Series("unknown", index=row_index)
            ),
            "transaction_id": (
                transaction_df[resolved_columns["transaction_id"]]
                if resolved_columns["transaction_id"]
                else pd.Series(pd.NA, index=row_index)
            ),
            "partial_refunds": (
                transaction_df[resolved_columns["partial_refunds"]]
                if resolved_columns["partial_refunds"]
                else pd.Series(0.0, index=row_index)
            ),
        }
    )

    df["transaction_datetime"] = pd.to_datetime(df["date_raw"], errors="coerce")
    df["transaction_date"] = df["transaction_datetime"].dt.normalize()
    df["net_sales"] = to_numeric_preserve_index(df["net_sales"])
    df["partial_refunds"] = to_numeric_preserve_index(df["partial_refunds"])
    df["location"] = (
        df["location"]
        .astype("string")
        .fillna("unknown")
        .str.strip()
        .replace("", "unknown")
    )
    df["clean_device"] = clean_device_name(df["device_name"])
    df["stand_location"] = map_stand_location(df["device_name"])

    time_text = df["time_raw"].astype("string")
    time_24h = pd.to_datetime(time_text, format="%H:%M:%S", errors="coerce")
    time_24h_short = pd.to_datetime(time_text, format="%H:%M", errors="coerce")
    time_12h = pd.to_datetime(time_text, format="%I:%M:%S %p", errors="coerce")
    df["hour"] = (
        time_24h.dt.hour
        .fillna(time_24h_short.dt.hour)
        .fillna(time_12h.dt.hour)
    )
    numeric_time = pd.to_numeric(df["time_raw"], errors="coerce")
    excel_hour = numeric_time.mul(24).floordiv(1).mod(24).where(
        numeric_time.between(0, 1)
    )
    df["hour"] = df["hour"].fillna(excel_hour)
    df["hour"] = df["hour"].fillna(df["transaction_datetime"].dt.hour)

    df["year"] = df["transaction_date"].dt.year
    df["weekday_number"] = df["transaction_date"].dt.dayofweek
    df["day_of_week"] = df["weekday_number"].map(
        {index: day for index, day in enumerate(DAY_ORDER)}
    )
    df["location_type"] = classify_location(df["location"])

    total_revenue = float(df["net_sales"].sum())
    avg_transaction_value = float(df["net_sales"].mean()) if len(df) else 0.0
    active_days = int(df["transaction_date"].nunique())
    transaction_count = (
        int(df["transaction_id"].notna().sum())
        if resolved_columns["transaction_id"]
        else len(df)
    )
    if not transaction_count:
        transaction_count = len(df)

    known_food_stand = (
        df["stand_location"].notna()
        & df["stand_location"].ne("Merchandise Store")
    )
    food_revenue = float(
        df.loc[
            df["location_type"].eq("Food & Beverage") | known_food_stand,
            "net_sales",
        ].sum()
    )

    return {
        "kpis": {
            "total_revenue": total_revenue,
            "avg_transaction_value": avg_transaction_value,
            "transactions_per_day": (
                transaction_count / active_days if active_days else 0.0
            ),
            "food_bev_revenue_pct": (
                food_revenue / total_revenue if total_revenue else 0.0
            ),
            "revenue_per_active_day": (
                total_revenue / active_days if active_days else 0.0
            ),
        },
        "charts": {
            "yearly_revenue": build_yearly_revenue(df),
            "stand_revenue": build_stand_revenue(df),
            "transaction_size_distribution": build_transaction_size_distribution(df),
            "revenue_by_day_of_week": build_revenue_by_day_of_week(df),
            "device_efficiency": build_device_efficiency(df),
            "cumulative_revenue": build_cumulative_revenue(df),
        },
        "metadata": {
            "built_at": time.time(),
            "source_rows": len(transaction_df),
            "schema_version": TRANSACTION_METRIC_SCHEMA_VERSION,
        },
    }


# =============================================================================
# Fan Behavior Dashboard Page Metrics
# =============================================================================
FAN_BEHAVIOR_METRIC_SCHEMA_VERSION = "fan_behavior_v6"
FAN_WORKING_COLUMNS = [
    "fan_key",
    "merch_net_total",
    "total_ticket_paid",
    "first_game",
    "last_game",
    "games_attended",
    "is_merch_buyer",
    "most_common_section",
]


def source_column(df: pd.DataFrame, column: str) -> pd.Series:
    if column in df.columns:
        return df[column]
    return pd.Series(pd.NA, index=df.index)


def safe_divide(numerator: float, denominator: int | float) -> float:
    if not denominator:
        return 0.0
    return numerator / denominator


def prepare_fan_metric_layer(full_fan_master: pd.DataFrame) -> pd.DataFrame:
    working_df = pd.DataFrame(
        {column: source_column(full_fan_master, column) for column in FAN_WORKING_COLUMNS}
    )

    for column in ["merch_net_total", "total_ticket_paid"]:
        working_df[column] = pd.to_numeric(
            working_df[column],
            errors="coerce",
        ).fillna(0.0)

    for column in ["games_attended", "is_merch_buyer"]:
        working_df[column] = pd.to_numeric(
            working_df[column],
            errors="coerce",
        ).fillna(0.0)
    working_df["first_game"] = pd.to_datetime(working_df["first_game"], errors="coerce")
    working_df["last_game"] = pd.to_datetime(working_df["last_game"], errors="coerce")
    working_df["total_spend"] = (
        working_df["merch_net_total"] + working_df["total_ticket_paid"]
    )
    working_df["tenure_days"] = (
        working_df["last_game"] - working_df["first_game"]
    ).dt.days
    working_df["tenure_days"] = working_df["tenure_days"].fillna(0.0)
    working_df["section_group"] = build_section_group(working_df["most_common_section"])
    return working_df


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
    grouped = grouped.mask(
        section_text.str.contains("duck blind", na=False),
        "Duck Blind",
    )
    grouped = grouped.mask(
        section_text.str.contains("arch", na=False),
        "Arch Solar Suites",
    )
    return grouped


def build_fan_spend_distribution(df: pd.DataFrame) -> pd.Series:
    spend = df.loc[df["total_spend"].ge(0), "total_spend"].dropna()
    if spend.empty:
        return pd.Series(dtype="int64")

    bin_edges = [0, 20, 50, 100, 200, 500, np.inf]
    labels = ["$0-$20", "$20-$50", "$50-$100", "$100-$200", "$200-$500", "$500+"]
    bins = pd.cut(
        spend,
        bins=bin_edges,
        labels=labels,
        include_lowest=True,
    )
    grouped = bins.value_counts(sort=False).rename("fan_count")
    return grouped


def build_revenue_by_section(df: pd.DataFrame) -> pd.Series:
    section_order = [
        "100 Level",
        "200 Level",
        "Other",
        "Duck Blind",
        "General Admission",
        "Arch Solar Suites",
    ]
    grouped = (
        df.groupby("section_group", observed=False)["total_spend"]
        .mean()
        .reindex(section_order)
        .dropna()
    )
    return grouped.rename("avg_spend")


def build_merch_conversion_by_section(df: pd.DataFrame) -> pd.Series:
    section_order = [
        "100 Level",
        "200 Level",
        "Other",
        "Duck Blind",
        "General Admission",
        "Arch Solar Suites",
    ]
    return (
        df.groupby("section_group", observed=False)["is_merch_buyer"]
        .mean()
        .reindex(section_order)
        .dropna()
        .rename("merch_conversion_rate")
    )


def build_average_spend_by_merch_buyer(df: pd.DataFrame) -> pd.Series:
    grouped = df.groupby("is_merch_buyer", observed=True)["total_spend"].mean()
    grouped.index = grouped.index.map({0.0: "Non-Buyer", 1.0: "Buyer"})
    return grouped.rename("avg_spend")


def build_tenure_spend_by_bin(df: pd.DataFrame) -> pd.Series:
    tenure_df = df[["tenure_days", "total_spend", "games_attended"]].dropna()
    if tenure_df.empty:
        return pd.Series(dtype="float64")

    tenure_df["spend_per_game"] = (
        tenure_df["total_spend"] / tenure_df["games_attended"]
    ).replace([np.inf, -np.inf], np.nan)
    tenure_df = tenure_df.dropna(subset=["spend_per_game"])
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
    tenure_df["tenure_bin"] = pd.cut(
        tenure_df["tenure_days"],
        bins=bins,
        labels=labels,
    )
    return (
        tenure_df.groupby("tenure_bin", observed=False)["spend_per_game"]
        .mean()
        .rename("avg_spend_per_game")
    )


@st.cache_data(show_spinner=False)
def prepare_fan_behavior_metrics(full_fan_master: pd.DataFrame) -> dict:
    df = prepare_fan_metric_layer(full_fan_master)
    spend_per_game = (
        df["total_spend"] / df["games_attended"]
    ).replace([np.inf, -np.inf], 0)
    unique_fans = df["fan_key"].nunique()

    return {
        "kpis": {
            "avg_revenue_per_fan": safe_divide(df["total_spend"].sum(), unique_fans),
            "multi_game_rate": df["games_attended"].gt(1).mean(),
            "avg_spend_per_game_per_fan": spend_per_game.fillna(0).mean(),
            "merch_conversion_rate": df["is_merch_buyer"].mean(),
            "avg_games_attended": df["games_attended"].mean(),
        },
        "charts": {
            "fan_spend_distribution": build_fan_spend_distribution(df),
            "revenue_by_section": build_revenue_by_section(df),
            "merch_conversion_by_section": build_merch_conversion_by_section(df),
            "average_spend_by_merch_buyer": build_average_spend_by_merch_buyer(df),
            "tenure_spend_by_bin": build_tenure_spend_by_bin(df),
        },
        "metadata": {
            "built_at": time.time(),
            "source_rows": len(full_fan_master),
            "schema_version": FAN_BEHAVIOR_METRIC_SCHEMA_VERSION,
        },
    }


# =============================================================================
# Survey Analysis Page Metrics
# =============================================================================
SURVEY_METRIC_SCHEMA_VERSION = "survey_v5"
TOPIC_RULES = [
    (
        "Food & Beverage",
        [
            "food",
            "beverage",
            "concession",
            "stand",
            "drink",
            "beer",
            "soda",
            "fries",
            "menu",
            "line",
        ],
    ),
    (
        "Checkout & Tech",
        ["mashgin", "automated checkout", "checkout", "device", "kiosk", "app"],
    ),
    (
        "Entertainment & On-Field",
        ["on-field", "presentation", "music", "promotion", "promotional", "announcer", "between innings", "entertainment"],
    ),
    (
        "Cleanliness & Facilities",
        ["clean", "cleanliness", "restroom", "bathroom", "trash", "facility"],
    ),
    ("Staff & Service", ["staff", "employee", "security", "service", "usher"]),
    ("Value & Pricing", ["price", "cost", "value", "expensive", "affordable"]),
    ("Seating & Comfort", ["seat", "seating", "view", "shade", "comfort"]),
    ("Parking & Access", ["parking", "gate", "entry", "entrance", "traffic"]),
    (
        "Brand & Marketing",
        ["hear about", "facebook", "instagram", "email", "marketing", "brand"],
    ),
    (
        "Overall Experience",
        ["overall", "rank your experience", "fan experience", "better fan"],
    ),
]

META_ALIASES = {
    "timestamp": ["Timestamp", "Submitted At", "submitted_at", "created_at"],
    "email": ["Email", "Email Address", "Email address", "email"],
    "first_name": ["First Name", "first name", "FirstName"],
    "last_name": ["Last Name", "last name", "LastName"],
    "zip_code": ["Your ZIP Code", "What is your Zip Code?", "Zip Code", "ZIP"],
    "phone": ["Phone Number", "Phone", "phone"],
    "gender": ["Gender", "gender"],
    "age": ["How old are you?", "Age", "age"],
    "game_date": [
        "What was the date of the game you attended?",
        "What was the date of game you attended?",
        "Date of the game",
        "Date of game",
        "Game Date",
    ],
}

INTERNAL_COLUMNS = {
    "_source_file",
    "_source_sheet",
    "_response_id",
    "survey_type",
    "survey_year",
    "team",
}
IGNORE_QUESTION_SUBSTRINGS = ["agree to share your info", "by checking this box"]
SURVEY_TYPE_LABELS = {
    "postgame": "Postgame",
    "postseason": "Postseason",
    "unknown_survey": "Unknown",
}


def classify_survey_filename(filename: str) -> str:
    filename_lower = str(filename).lower()
    exact_postgame = "postgame" in filename_lower
    exact_postseason = "postseason" in filename_lower

    if exact_postgame:
        return "postgame"
    if exact_postseason:
        return "postseason"
    if "post" in filename_lower and "game" in filename_lower:
        return "postgame"
    if "post" in filename_lower and "season" in filename_lower:
        return "postseason"
    return "unknown_survey"


def extract_year(filename: str) -> int | None:
    match = re.search(r"(20\d{2})", str(filename))
    return int(match.group(1)) if match else None


def extract_team(filename: str) -> str:
    filename_lower = str(filename).lower()
    if (
        "night mares" in filename_lower
        or "nightmares" in filename_lower
        or "nm" in filename_lower
    ):
        return "Night Mares"
    if "mallard" in filename_lower:
        return "Mallards"
    return "Unknown"


def question_to_topic(question: str) -> str:
    question_lower = str(question).lower()
    for topic, keywords in TOPIC_RULES:
        if any(keyword in question_lower for keyword in keywords):
            return topic
    return "Other"


def question_is_ignored(question: str) -> bool:
    question_lower = str(question).lower()
    return any(fragment in question_lower for fragment in IGNORE_QUESTION_SUBSTRINGS)


def normalize_response_text(responses: pd.Series) -> pd.Series:
    normalized = responses.astype("string").str.strip()
    return normalized.replace(
        {
            "": pd.NA,
            "nan": pd.NA,
            "None": pd.NA,
            "none": pd.NA,
            "<NA>": pd.NA,
        }
    )


def numeric_from_response(responses: pd.Series) -> pd.Series:
    text = responses.astype("string").str.extract(
        r"(-?\d+(?:\.\d+)?)",
        expand=False,
    )
    return pd.to_numeric(text, errors="coerce").astype("float64")


def guess_question_kind(question: str, responses: pd.Series) -> str:
    question_lower = str(question).lower()
    clean_responses = normalize_response_text(responses).dropna()

    if any(term in question_lower for term in ["wait", "minutes", "how long"]):
        return "duration"

    text_terms = [
        "comment",
        "comments",
        "improve",
        "explain",
        "ideas",
        "feedback",
        "what are some",
        "change",
    ]
    avg_length = (
        clean_responses.astype("string").str.len().mean()
        if len(clean_responses)
        else 0
    )
    if any(term in question_lower for term in text_terms) or avg_length >= 28:
        return "text"

    numeric_values = numeric_from_response(clean_responses)
    numeric_ratio = numeric_values.notna().mean() if len(clean_responses) else 0.0

    non_rating_numeric_terms = [
        "zip",
        "postal",
        "phone",
        "income",
        "household",
        "age",
        "date",
        "birthday",
    ]
    if any(term in question_lower for term in non_rating_numeric_terms):
        if numeric_ratio >= 0.7:
            return "other"

    numeric_max = numeric_values.abs().max() if numeric_values.notna().any() else 0.0
    rating_terms = [
        "rank",
        "rate",
        "scale",
        "1-10",
        "1 to 10",
        "experience",
    ]
    if any(term in question_lower for term in rating_terms):
        return "rating"
    if numeric_ratio >= 0.7 and numeric_max <= 100:
        return "rating"

    if len(clean_responses):
        normalized = clean_responses.astype("string").str.lower().str.strip()
        choice_ratio = normalized.isin(["yes", "no", "y", "n", "true", "false"]).mean()
        if choice_ratio >= 0.85:
            return "choice"

    return "other"


@st.cache_resource
def get_sentiment_analyzer() -> SentimentIntensityAnalyzer:
    return SentimentIntensityAnalyzer()


def sentiment_label(compound: float) -> str:
    if compound >= 0.05:
        return "Positive"
    if compound <= -0.05:
        return "Negative"
    return "Neutral"


def standardize_meta_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    normalized_lookup = {
        str(column).strip().lower(): column for column in df.columns
    }

    for canonical, aliases in META_ALIASES.items():
        if canonical in df.columns:
            continue
        for alias in aliases:
            match = normalized_lookup.get(str(alias).strip().lower())
            if match:
                rename_map[match] = canonical
                break
        if canonical == "game_date" and canonical not in rename_map.values():
            for normalized_column, original_column in normalized_lookup.items():
                if (
                    "date of the game" in normalized_column
                    or "date of game" in normalized_column
                ):
                    rename_map[original_column] = canonical
                    break

    return df.rename(columns=rename_map)


def ensure_source_metadata(df: pd.DataFrame) -> pd.DataFrame:
    working_df = df.copy()
    if "_source_file" not in working_df.columns:
        working_df["_source_file"] = "Uploaded survey"
    if "_source_sheet" not in working_df.columns:
        working_df["_source_sheet"] = "Unknown"

    source_file = working_df["_source_file"].astype("string").fillna("Uploaded survey")
    filename_survey_type = source_file.map(classify_survey_filename)
    filename_team = source_file.map(extract_team)
    filename_year = source_file.map(extract_year)

    if "survey_type" not in working_df.columns:
        working_df["survey_type"] = filename_survey_type
    else:
        working_df["survey_type"] = (
            working_df["survey_type"]
            .astype("string")
            .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA})
            .fillna(filename_survey_type)
        )

    if "team" not in working_df.columns:
        working_df["team"] = filename_team
    else:
        working_df["team"] = (
            working_df["team"]
            .astype("string")
            .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA})
            .fillna(filename_team)
        )

    if "survey_year" not in working_df.columns:
        working_df["survey_year"] = filename_year
    else:
        working_df["survey_year"] = pd.to_numeric(
            working_df["survey_year"],
            errors="coerce",
        ).fillna(pd.Series(filename_year, index=working_df.index))

    return working_df


def combine_survey_input(survey_frames_or_df) -> pd.DataFrame:
    if isinstance(survey_frames_or_df, list):
        frames = [frame for frame in survey_frames_or_df if not frame.empty]
        if not frames:
            return pd.DataFrame()
        return pd.concat(frames, ignore_index=True, sort=False)
    return survey_frames_or_df


def build_survey_long(survey_df: pd.DataFrame) -> pd.DataFrame:
    if survey_df.empty:
        return pd.DataFrame()

    wide = survey_df.copy()
    wide.columns = [str(column).strip() for column in wide.columns]
    wide = standardize_meta_columns(wide)
    wide = ensure_source_metadata(wide)
    wide["_response_id"] = (
        wide["_source_file"].astype("string").fillna("Uploaded survey")
        + "|"
        + wide["_source_sheet"].astype("string").fillna("Unknown")
        + "|"
        + pd.Series(wide.index, index=wide.index).astype("string")
    )

    meta_columns = [
        column
        for column in [
            "survey_type",
            "team",
            "survey_year",
            "_source_file",
            "_source_sheet",
            "_response_id",
            "timestamp",
            "email",
            "first_name",
            "last_name",
            "zip_code",
            "phone",
            "gender",
            "age",
            "game_date",
        ]
        if column in wide.columns
    ]

    meta_set = set(meta_columns).union(INTERNAL_COLUMNS)
    question_columns = [
        column
        for column in wide.columns
        if column not in meta_set
        and not str(column).startswith("_")
        and not question_is_ignored(column)
        and normalize_response_text(wide[column]).notna().any()
    ]
    if not question_columns:
        return pd.DataFrame()

    long_df = wide.melt(
        id_vars=meta_columns,
        value_vars=question_columns,
        var_name="question",
        value_name="response_raw",
    )
    long_df["response_raw"] = normalize_response_text(long_df["response_raw"])
    long_df = long_df[long_df["response_raw"].notna()].reset_index(drop=True)

    if "timestamp" in long_df.columns:
        long_df["timestamp"] = pd.to_datetime(long_df["timestamp"], errors="coerce")
    else:
        long_df["timestamp"] = pd.NaT
    if "email" not in long_df.columns:
        long_df["email"] = pd.NA
    if "game_date" in long_df.columns:
        long_df["game_date"] = pd.to_datetime(long_df["game_date"], errors="coerce")
    else:
        long_df["game_date"] = pd.NaT

    kind_map = {
        question: guess_question_kind(question, wide[question])
        for question in question_columns
    }
    topic_map = {question: question_to_topic(question) for question in question_columns}

    long_df["question_kind"] = long_df["question"].map(kind_map).fillna("other")
    long_df["topic"] = long_df["question"].map(topic_map).fillna("Other")
    long_df["response_text"] = long_df["response_raw"].where(
        long_df["question_kind"].eq("text"),
        "",
    )
    long_df["value_num"] = np.nan

    numeric_mask = long_df["question_kind"].isin(["rating", "duration"])
    long_df.loc[numeric_mask, "value_num"] = numeric_from_response(
        long_df.loc[numeric_mask, "response_raw"]
    )
    rating_mask = long_df["question_kind"].eq("rating")
    long_df.loc[
        rating_mask & ~long_df["value_num"].between(0, 10),
        "value_num",
    ] = np.nan

    choice_mask = long_df["question_kind"].eq("choice")
    if choice_mask.any():
        normalized_choice = (
            long_df.loc[choice_mask, "response_raw"]
            .astype("string")
            .str.lower()
            .str.strip()
        )
        choice_values = normalized_choice.map(
            {
                "yes": 1.0,
                "y": 1.0,
                "true": 1.0,
                "no": 0.0,
                "n": 0.0,
                "false": 0.0,
            }
        )
        long_df.loc[choice_mask, "value_num"] = choice_values

    long_df["sentiment_compound"] = np.nan
    long_df["sentiment_label"] = pd.NA
    long_df["sentiment_index"] = np.nan

    text_mask = long_df["question_kind"].eq("text") & long_df["response_text"].astype(
        "string"
    ).str.strip().ne("")
    if text_mask.any():
        analyzer = get_sentiment_analyzer()
        text_values = long_df.loc[text_mask, "response_text"].astype(str).tolist()
        compounds = [
            analyzer.polarity_scores(text).get("compound", 0.0)
            for text in text_values
        ]
        long_df.loc[text_mask, "sentiment_compound"] = compounds
        long_df.loc[text_mask, "sentiment_label"] = [
            sentiment_label(compound) for compound in compounds
        ]
        long_df.loc[text_mask, "sentiment_index"] = (
            long_df.loc[text_mask, "sentiment_compound"].astype(float) + 1.0
        ) * 5.0

    output_columns = [
        "survey_type",
        "team",
        "survey_year",
        "_source_file",
        "_source_sheet",
        "_response_id",
        "timestamp",
        "game_date",
        "email",
        "question",
        "response_raw",
        "question_kind",
        "topic",
        "response_text",
        "value_num",
        "sentiment_compound",
        "sentiment_label",
        "sentiment_index",
    ]
    return long_df[output_columns]


def response_level_frame(long_df: pd.DataFrame) -> pd.DataFrame:
    if long_df.empty:
        return pd.DataFrame()
    response_columns = [
        "_response_id",
        "survey_type",
        "survey_year",
        "team",
        "_source_file",
        "_source_sheet",
        "timestamp",
        "game_date",
    ]
    return long_df.drop_duplicates("_response_id")[
        [column for column in response_columns if column in long_df.columns]
    ]


def survey_year_labels(series: pd.Series) -> pd.Series:
    return (
        pd.to_numeric(series, errors="coerce")
        .astype("Int64")
        .astype("string")
        .replace("<NA>", "Unknown")
    )


def label_survey_types(series: pd.Series) -> pd.Series:
    return series.astype("string").map(SURVEY_TYPE_LABELS).fillna("Unknown")


def empty_survey_metrics(source_rows: int, long_rows: int = 0) -> dict:
    return {
        "kpis": {
            "total_survey_responses": 0,
            "avg_numeric_rating": 0.0,
            "overall_sentiment_index": 0.0,
            "negative_response_rate": 0.0,
            "postgame_response_mix": 0.0,
        },
        "charts": {
            "responses_by_team_year": empty_chart(
                ["team", "survey_year", "survey_type", "response_count"]
            ),
            "rating_by_team_year": empty_chart(
                ["team", "survey_year", "team_year", "avg_rating", "response_count"]
            ),
            "sentiment_by_team_year": empty_chart(
                ["team", "survey_year", "sentiment_index", "response_count"]
            ),
            "topic_rating_by_year": empty_chart(
                [
                    "team",
                    "survey_year",
                    "topic",
                    "year_topic",
                    "avg_rating",
                    "response_count",
                ]
            ),
            "topic_sentiment_by_year": empty_chart(
                [
                    "team",
                    "survey_year",
                    "topic",
                    "year_topic",
                    "sentiment_index",
                    "negative_rate",
                    "response_count",
                ]
            ),
            "negative_rate_by_topic": empty_chart(["topic", "negative_rate"]),
            "top_opportunity_areas": empty_chart(
                ["topic", "negative_rate", "response_count", "opportunity_score"]
            ),
            "topic_text_summary": empty_chart(
                [
                    "team",
                    "survey_year",
                    "topic",
                    "sentiment_index",
                    "negative_rate",
                    "response_count",
                ]
            ),
        },
        "recent_postgame": {
            "summary": {
                "label": "No postgame survey found",
                "team": "Unknown",
                "survey_year": "Unknown",
                "response_count": 0,
                "avg_rating": 0.0,
                "sentiment_index": 0.0,
                "negative_rate": 0.0,
            },
            "topic_rating": empty_chart(["topic", "avg_rating", "response_count"]),
            "topic_sentiment": empty_chart(
                ["topic", "sentiment_index", "negative_rate", "response_count"]
            ),
            "negative_comments": empty_chart(["topic", "question", "comment"]),
            "positive_comments": empty_chart(["topic", "question", "comment"]),
        },
        "postgame_pulses": [],
        "short_answer_center": {
            "options": empty_chart(["event_key", "survey_label"]),
            "comments": empty_chart(
                [
                    "event_key",
                    "survey_label",
                    "topic",
                    "question",
                    "comment",
                    "sentiment_label",
                    "sentiment_index",
                ]
            ),
        },
        "metadata": {
            "built_at": time.time(),
            "source_rows": source_rows,
            "long_rows": long_rows,
            "teams": [],
            "years": [],
            "schema_version": SURVEY_METRIC_SCHEMA_VERSION,
        },
    }


def short_comment(text: str, limit: int = 220) -> str:
    return re.sub(r"\s+", " ", str(text)).strip()


def build_comment_examples(
    text_rows: pd.DataFrame,
    sentiment: str,
    limit: int = 5,
) -> pd.DataFrame:
    if text_rows.empty:
        return empty_chart(["topic", "question", "comment"])

    comments = text_rows[
        text_rows["sentiment_label"].eq(sentiment)
        & text_rows["response_text"].astype("string").str.strip().ne("")
    ].copy()
    if comments.empty:
        return empty_chart(["topic", "question", "comment"])

    comments = comments.sort_values(
        "sentiment_compound",
        ascending=sentiment == "Negative",
    ).head(limit)
    comments["comment"] = comments["response_text"].map(short_comment)
    return comments[["topic", "question", "comment"]]


def build_recent_postgame_metrics(long_df: pd.DataFrame) -> dict:
    postgame = long_df[long_df["survey_type"].eq("postgame")].copy()
    if postgame.empty:
        return empty_survey_metrics(0)["recent_postgame"]

    game_date = pd.to_datetime(postgame["game_date"], errors="coerce").dt.normalize()
    response_timestamp = pd.to_datetime(
        postgame["timestamp"],
        errors="coerce",
    ).dt.normalize()
    survey_year = pd.to_numeric(postgame["survey_year"], errors="coerce")
    valid_game_date = game_date.notna() & game_date.dt.year.eq(survey_year)
    postgame["_event_date"] = game_date.where(valid_game_date).fillna(
        response_timestamp
    )

    if postgame["_event_date"].notna().any():
        latest_date = postgame["_event_date"].max()
        recent = postgame[postgame["_event_date"].eq(latest_date)].copy()
        if hasattr(latest_date, "strftime"):
            label = f"{latest_date:%B} {latest_date.day}, {latest_date:%Y}"
        else:
            label = str(latest_date)
    else:
        sort_columns = ["survey_year", "_source_file", "_source_sheet"]
        recent_key = (
            postgame[sort_columns]
            .drop_duplicates()
            .sort_values(sort_columns, na_position="last")
            .tail(1)
        )
        if recent_key.empty:
            recent = postgame
            label = "Latest postgame survey"
        else:
            key = recent_key.iloc[0]
            recent = postgame[
                postgame["survey_year"].eq(key["survey_year"])
                & postgame["_source_file"].eq(key["_source_file"])
                & postgame["_source_sheet"].eq(key["_source_sheet"])
            ].copy()
            label = str(key["_source_sheet"])

    recent_responses = response_level_frame(recent)
    recent_rating = recent[
        recent["question_kind"].eq("rating") & recent["value_num"].notna()
    ]
    recent_text = recent[
        recent["question_kind"].eq("text") & recent["sentiment_index"].notna()
    ]

    response_count = (
        int(recent_responses["_response_id"].nunique())
        if not recent_responses.empty
        else 0
    )
    avg_rating = (
        float(recent_rating["value_num"].mean()) if not recent_rating.empty else 0.0
    )
    sentiment_index = (
        float(recent_text["sentiment_index"].mean()) if not recent_text.empty else 0.0
    )
    negative_rate = (
        float(recent_text["sentiment_label"].eq("Negative").mean())
        if not recent_text.empty
        else 0.0
    )

    topic_rating = (
        recent_rating.groupby("topic", as_index=False, observed=True)
        .agg(avg_rating=("value_num", "mean"), response_count=("value_num", "count"))
        .sort_values("avg_rating", ascending=False)
        if not recent_rating.empty
        else empty_chart(["topic", "avg_rating", "response_count"])
    )
    topic_sentiment = (
        recent_text.assign(
            is_negative=recent_text["sentiment_label"].eq("Negative").astype(float)
        )
        .groupby("topic", as_index=False, observed=True)
        .agg(
            sentiment_index=("sentiment_index", "mean"),
            negative_rate=("is_negative", "mean"),
            response_count=("response_text", "count"),
        )
        .sort_values("sentiment_index", ascending=False)
        if not recent_text.empty
        else empty_chart(["topic", "sentiment_index", "negative_rate", "response_count"])
    )

    first_response = recent_responses.iloc[0] if not recent_responses.empty else {}
    return {
        "summary": {
            "label": label,
            "team": str(first_response.get("team", "Unknown")),
            "survey_year": str(first_response.get("survey_year", "Unknown")),
            "source_file": str(first_response.get("_source_file", "Unknown")),
            "source_sheet": str(first_response.get("_source_sheet", "Unknown")),
            "response_count": response_count,
            "avg_rating": avg_rating,
            "sentiment_index": sentiment_index,
            "negative_rate": negative_rate,
        },
        "topic_rating": topic_rating,
        "topic_sentiment": topic_sentiment,
        "negative_comments": build_comment_examples(recent_text, "Negative"),
        "positive_comments": build_comment_examples(recent_text, "Positive"),
    }


def survey_event_frame(
    long_df: pd.DataFrame,
    survey_type: str | None = None,
) -> pd.DataFrame:
    events = long_df.copy()
    if survey_type:
        events = events[events["survey_type"].eq(survey_type)].copy()
    if events.empty:
        return events

    game_date = pd.to_datetime(events["game_date"], errors="coerce").dt.normalize()
    response_timestamp = pd.to_datetime(
        events["timestamp"],
        errors="coerce",
    ).dt.normalize()
    survey_year = pd.to_numeric(events["survey_year"], errors="coerce")
    valid_game_date = game_date.notna() & game_date.dt.year.eq(survey_year)
    events["_event_date"] = game_date.where(valid_game_date).fillna(
        response_timestamp
    )
    event_date_label = events["_event_date"].dt.strftime("%Y-%m-%d").fillna(
        "unknown-date"
    )
    events["_event_key"] = (
        event_date_label
        + "|"
        + events["survey_type"].astype("string").fillna("unknown_survey")
        + "|"
        + events["team"].astype("string").fillna("Unknown")
        + "|"
        + events["_source_file"].astype("string").fillna("Unknown file")
    )
    return events


def postgame_event_frame(long_df: pd.DataFrame) -> pd.DataFrame:
    return survey_event_frame(long_df, "postgame")


def postgame_option_label(event_df: pd.DataFrame) -> str:
    responses = response_level_frame(event_df)
    first_response = responses.iloc[0] if not responses.empty else {}
    team = str(first_response.get("team", "Unknown"))
    event_date = event_df["_event_date"].dropna()
    if not event_date.empty:
        date_value = event_date.max()
        label = f"{date_value:%B} {date_value.day}, {date_value:%Y}"
    else:
        label = str(first_response.get("survey_year", "Unknown year"))
    return f"{label} - {team}"


def build_postgame_pulse_collection(long_df: pd.DataFrame) -> list[dict]:
    postgame = postgame_event_frame(long_df)
    if postgame.empty:
        return []

    event_order = (
        postgame[["_event_key", "_event_date", "_source_file", "_source_sheet"]]
        .drop_duplicates("_event_key")
        .sort_values(
            ["_event_date", "_source_file", "_source_sheet"],
            ascending=[False, True, True],
            na_position="last",
        )
    )
    pulses = []
    for event_key in event_order["_event_key"]:
        event_df = postgame[postgame["_event_key"].eq(event_key)]
        pulse = build_recent_postgame_metrics(event_df)
        option_label = postgame_option_label(event_df)
        pulse["summary"]["event_key"] = str(event_key)
        pulse["summary"]["option_label"] = option_label
        pulses.append(pulse)
    return pulses


def survey_result_option_label(event_df: pd.DataFrame) -> str:
    responses = response_level_frame(event_df)
    first_response = responses.iloc[0] if not responses.empty else {}
    team = str(first_response.get("team", "Unknown"))
    survey_type = SURVEY_TYPE_LABELS.get(
        str(first_response.get("survey_type", "unknown_survey")),
        "Unknown",
    )
    event_date = event_df["_event_date"].dropna()
    if not event_date.empty:
        date_value = event_date.max()
        label = f"{date_value:%B} {date_value.day}, {date_value:%Y}"
    else:
        label = str(first_response.get("survey_year", "Unknown year"))
    return f"{label} - {team} - {survey_type}"


def build_short_answer_center(long_df: pd.DataFrame) -> dict:
    text_rows = long_df[
        long_df["question_kind"].eq("text")
        & long_df["response_text"].astype("string").str.strip().ne("")
    ]
    if text_rows.empty:
        return {
            "options": empty_chart(["event_key", "survey_label"]),
            "comments": empty_chart(
                [
                    "event_key",
                    "survey_label",
                    "topic",
                    "question",
                    "comment",
                    "sentiment_label",
                    "sentiment_index",
                ]
            ),
        }

    event_rows = survey_event_frame(text_rows)
    if event_rows.empty:
        return {
            "options": empty_chart(["event_key", "survey_label"]),
            "comments": empty_chart(
                [
                    "event_key",
                    "survey_label",
                    "topic",
                    "question",
                    "comment",
                    "sentiment_label",
                    "sentiment_index",
                ]
            ),
        }

    event_order = (
        event_rows[["_event_key", "_event_date", "_source_file"]]
        .drop_duplicates("_event_key")
        .sort_values(
            ["_event_date", "_source_file"],
            ascending=[False, True],
            na_position="last",
        )
    )
    options = []
    for event_key in event_order["_event_key"]:
        event_df = event_rows[event_rows["_event_key"].eq(event_key)]
        options.append(
            {
                "event_key": str(event_key),
                "survey_label": survey_result_option_label(event_df),
            }
        )
    options_df = pd.DataFrame(options)

    label_map = dict(zip(options_df["event_key"], options_df["survey_label"]))
    comments = event_rows[
        [
            "_event_key",
            "topic",
            "question",
            "response_text",
            "sentiment_label",
            "sentiment_index",
        ]
    ].copy()
    comments["event_key"] = comments["_event_key"].astype(str)
    comments["survey_label"] = comments["event_key"].map(label_map)
    comments["comment"] = comments["response_text"].map(short_comment)
    comments = comments[
        [
            "event_key",
            "survey_label",
            "topic",
            "question",
            "comment",
            "sentiment_label",
            "sentiment_index",
        ]
    ].sort_values(["survey_label", "topic", "sentiment_label", "question"])
    return {"options": options_df, "comments": comments}


def build_topic_text_summary(text_chart: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "team",
        "survey_year",
        "topic",
        "sentiment_index",
        "negative_rate",
        "response_count",
    ]
    if text_chart.empty:
        return empty_chart(columns)

    base = text_chart.assign(
        is_negative=text_chart["sentiment_label"].eq("Negative").astype(float)
    )

    def aggregate(group_columns: list[str]) -> pd.DataFrame:
        grouped = (
            base.groupby(group_columns, as_index=False, observed=True)
            .agg(
                sentiment_index=("sentiment_index", "mean"),
                negative_rate=("is_negative", "mean"),
                response_count=("response_text", "count"),
            )
        )
        if "team" not in grouped.columns:
            grouped["team"] = "All Teams"
        if "survey_year" not in grouped.columns:
            grouped["survey_year"] = "All Years"
        return grouped[columns]

    frames = [
        aggregate(["team", "survey_year", "topic"]),
        aggregate(["team", "topic"]),
        aggregate(["survey_year", "topic"]),
        aggregate(["topic"]),
    ]
    return pd.concat(frames, ignore_index=True).sort_values(
        ["survey_year", "team", "topic"]
    )


@st.cache_data(show_spinner=False)
def prepare_survey_analysis_metrics(survey_frames_or_df) -> dict:
    survey_df = combine_survey_input(survey_frames_or_df)
    long_df = build_survey_long(survey_df)
    if long_df.empty:
        return empty_survey_metrics(len(survey_df))

    responses = response_level_frame(long_df)
    rating_rows = long_df[
        long_df["question_kind"].eq("rating") & long_df["value_num"].notna()
    ]
    text_rows = long_df[
        long_df["question_kind"].eq("text") & long_df["sentiment_index"].notna()
    ]

    total_responses = (
        int(responses["_response_id"].nunique()) if not responses.empty else 0
    )
    avg_numeric_rating = (
        float(rating_rows["value_num"].mean()) if not rating_rows.empty else 0.0
    )
    sentiment_index = (
        float(text_rows["sentiment_index"].mean()) if not text_rows.empty else 0.0
    )
    negative_response_rate = (
        float(text_rows["sentiment_label"].eq("Negative").mean())
        if not text_rows.empty
        else 0.0
    )
    postgame_response_mix = (
        float(responses["survey_type"].eq("postgame").mean())
        if not responses.empty
        else 0.0
    )

    responses_chart = responses.copy()
    responses_chart["survey_year"] = survey_year_labels(
        responses_chart["survey_year"]
    )
    responses_chart["survey_type"] = label_survey_types(
        responses_chart["survey_type"]
    )

    responses_by_team_year = (
        responses_chart.groupby(
            ["team", "survey_year", "survey_type"],
            as_index=False,
            observed=True,
        )["_response_id"]
        .nunique()
        .rename(columns={"_response_id": "response_count"})
        .sort_values(["survey_year", "team", "survey_type"])
        if not responses_chart.empty
        else empty_chart(["team", "survey_year", "survey_type", "response_count"])
    )

    rating_chart = rating_rows.copy()
    if not rating_chart.empty:
        rating_chart["survey_year"] = survey_year_labels(rating_chart["survey_year"])

    text_chart = text_rows.copy()
    if not text_chart.empty:
        text_chart["survey_year"] = survey_year_labels(text_chart["survey_year"])

    rating_by_team_year = (
        rating_chart.groupby(["team", "survey_year"], as_index=False, observed=True)
        .agg(avg_rating=("value_num", "mean"), response_count=("value_num", "count"))
        .sort_values(["survey_year", "team"])
        if not rating_chart.empty
        else empty_chart(
            ["team", "survey_year", "team_year", "avg_rating", "response_count"]
        )
    )
    if not rating_by_team_year.empty:
        rating_by_team_year["team_year"] = (
            rating_by_team_year["survey_year"].astype(str)
            + " "
            + rating_by_team_year["team"].astype(str)
        )

    sentiment_by_team_year = (
        text_chart.groupby(["team", "survey_year"], as_index=False, observed=True)
        .agg(
            sentiment_index=("sentiment_index", "mean"),
            response_count=("response_text", "count"),
        )
        .sort_values(["survey_year", "team"])
        if not text_chart.empty
        else empty_chart(["team", "survey_year", "sentiment_index", "response_count"])
    )

    topic_rating_by_year = (
        rating_chart.groupby(
            ["team", "survey_year", "topic"],
            as_index=False,
            observed=True,
        )
        .agg(avg_rating=("value_num", "mean"), response_count=("value_num", "count"))
        .sort_values(["survey_year", "team", "topic"])
        if not rating_chart.empty
        else empty_chart(
            [
                "team",
                "survey_year",
                "topic",
                "year_topic",
                "avg_rating",
                "response_count",
            ]
        )
    )
    if not rating_chart.empty:
        overall_topic_rating = (
            rating_chart.groupby(["survey_year", "topic"], as_index=False, observed=True)
            .agg(
                avg_rating=("value_num", "mean"),
                response_count=("value_num", "count"),
            )
            .assign(team="All Teams")
        )
        topic_rating_by_year = pd.concat(
            [topic_rating_by_year, overall_topic_rating],
            ignore_index=True,
        )
    if not topic_rating_by_year.empty:
        topic_rating_by_year["year_topic"] = (
            topic_rating_by_year["survey_year"].astype(str)
            + " "
            + topic_rating_by_year["topic"].astype(str)
        )

    topic_sentiment_by_year = (
        text_chart.assign(
            is_negative=text_chart["sentiment_label"].eq("Negative").astype(float)
        )
        .groupby(["team", "survey_year", "topic"], as_index=False, observed=True)
        .agg(
            sentiment_index=("sentiment_index", "mean"),
            negative_rate=("is_negative", "mean"),
            response_count=("response_text", "count"),
        )
        .sort_values(["survey_year", "team", "topic"])
        if not text_chart.empty
        else empty_chart(
            [
                "team",
                "survey_year",
                "topic",
                "year_topic",
                "sentiment_index",
                "negative_rate",
                "response_count",
            ]
        )
    )
    if not text_chart.empty:
        overall_topic_sentiment = (
            text_chart.assign(
                is_negative=text_chart["sentiment_label"].eq("Negative").astype(float)
            )
            .groupby(["survey_year", "topic"], as_index=False, observed=True)
            .agg(
                sentiment_index=("sentiment_index", "mean"),
                negative_rate=("is_negative", "mean"),
                response_count=("response_text", "count"),
            )
            .assign(team="All Teams")
        )
        topic_sentiment_by_year = pd.concat(
            [topic_sentiment_by_year, overall_topic_sentiment],
            ignore_index=True,
        )
    if not topic_sentiment_by_year.empty:
        topic_sentiment_by_year["year_topic"] = (
            topic_sentiment_by_year["survey_year"].astype(str)
            + " "
            + topic_sentiment_by_year["topic"].astype(str)
        )

    topic_text_summary = build_topic_text_summary(text_chart)

    negative_rate_by_topic = (
        text_rows.assign(
            is_negative=text_rows["sentiment_label"].eq("Negative").astype(float)
        )
        .groupby("topic", as_index=False, observed=True)["is_negative"]
        .mean()
        .rename(columns={"is_negative": "negative_rate"})
        .sort_values("negative_rate", ascending=False)
        if not text_rows.empty
        else empty_chart(["topic", "negative_rate"])
    )

    if not text_rows.empty:
        opportunity = (
            text_rows.assign(
                is_negative=text_rows["sentiment_label"].eq("Negative").astype(float)
            )
            .groupby("topic", as_index=False, observed=True)
            .agg(
                negative_rate=("is_negative", "mean"),
                response_count=("response_text", "count"),
            )
        )
        opportunity["opportunity_score"] = opportunity["negative_rate"] * np.log1p(
            opportunity["response_count"]
        )
        opportunity = opportunity.sort_values(
            "opportunity_score",
            ascending=False,
        ).head(10)
    else:
        opportunity = empty_chart(
            ["topic", "negative_rate", "response_count", "opportunity_score"]
        )

    teams = sorted(
        [team for team in responses_chart["team"].dropna().astype(str).unique()]
    )
    years = sorted(
        [year for year in responses_chart["survey_year"].dropna().astype(str).unique()]
    )

    postgame_pulses = build_postgame_pulse_collection(long_df)
    short_answer_center = build_short_answer_center(long_df)

    return {
        "kpis": {
            "total_survey_responses": total_responses,
            "avg_numeric_rating": avg_numeric_rating,
            "overall_sentiment_index": sentiment_index,
            "negative_response_rate": negative_response_rate,
            "postgame_response_mix": postgame_response_mix,
        },
        "charts": {
            "responses_by_team_year": responses_by_team_year,
            "rating_by_team_year": rating_by_team_year,
            "sentiment_by_team_year": sentiment_by_team_year,
            "topic_rating_by_year": topic_rating_by_year,
            "topic_sentiment_by_year": topic_sentiment_by_year,
            "negative_rate_by_topic": negative_rate_by_topic,
            "top_opportunity_areas": opportunity,
            "topic_text_summary": topic_text_summary,
        },
        "recent_postgame": (
            postgame_pulses[0]
            if postgame_pulses
            else build_recent_postgame_metrics(long_df)
        ),
        "postgame_pulses": postgame_pulses,
        "short_answer_center": short_answer_center,
        "metadata": {
            "built_at": time.time(),
            "source_rows": len(survey_df),
            "long_rows": len(long_df),
            "teams": teams,
            "years": years,
            "schema_version": SURVEY_METRIC_SCHEMA_VERSION,
        },
    }
