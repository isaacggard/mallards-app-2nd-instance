import altair as alt
import pandas as pd
import streamlit as st

from app import ensure_transaction_metrics, initialize_session_state, render_page_title
from pages.render_components import (
    create_bar_chart,
    create_line_chart,
    render_metric_cards,
)


def currency(value: float, round_over_100: bool = False) -> str:
    if round_over_100 and abs(value) >= 100:
        return f"${value:,.0f}"
    return f"${value:,.2f}"


def percent(value: float) -> str:
    return f"{value:.1%}"


def normalize_column_name(column: object) -> str:
    return " ".join(str(column).strip().lower().split())


def source_column(df: pd.DataFrame, column: str) -> pd.Series:
    lookup = {normalize_column_name(col): col for col in df.columns}
    resolved = lookup.get(normalize_column_name(column))
    if resolved:
        return df[resolved]
    return pd.Series(0.0, index=df.index)


def numeric_sum(df: pd.DataFrame | None, column: str) -> float:
    if df is None or df.empty:
        return 0.0
    return float(pd.to_numeric(source_column(df, column), errors="coerce").fillna(0).sum())


def render_kpis(metrics: dict, fan_master: pd.DataFrame | None) -> None:
    kpis = metrics["kpis"]
    food_bev_pct = float(kpis["food_bev_revenue_pct"])
    merch_pct = max(0.0, 1 - food_bev_pct)
    render_metric_cards(
        [
            {
                "label": "Total Revenue",
                "value": currency(float(kpis["total_revenue"]), round_over_100=True),
                "card_style": {
                    "min_height": "70px",
                    "padding": "0.4rem 0.4rem",
                    "border": "3px solid rgba(49, 51, 63, 0.2)",
                    "border_radius": "8px",
                    "background": "#ffffff",
                    "position": "relative",
                    "text_align": "center",
                    "font_family": "Georgia Bold",
                    "box_sizing": "border-box",
                    "margin_bottom": "0.5rem",
                },
                "label_style": {
                    "font_size": "19px",
                    "font_weight": "600",
                    "color": "#000000",
                    "line_height": "1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "0.3rem",
                },
                "value_style": {
                    "font_size": "32px",
                    "font_weight": "700",
                    "color": "#000000",
                    "line_height": "1.1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "50%",
                    "transform": "translateY(-25%)",
                    "white_space": "normal",
                },
            },
            {
                "label": "Avg Transaction Value",
                "value": currency(float(kpis["avg_transaction_value"])),
                "card_style": {
                    "min_height": "70px",
                    "padding": "0.4rem 0.4rem",
                    "border": "3px solid rgba(49, 51, 63, 0.2)",
                    "border_radius": "8px",
                    "background": "#ffffff",
                    "position": "relative",
                    "text_align": "center",
                    "font_family": "Georgia Bold",
                    "box_sizing": "border-box",
                    "margin_bottom": "0.5rem",
                },
                "label_style": {
                    "font_size": "19px",
                    "font_weight": "600",
                    "color": "#000000",
                    "line_height": "1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "0.3rem",
                },
                "value_style": {
                    "font_size": "32px",
                    "font_weight": "700",
                    "color": "#000000",
                    "line_height": "1.1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "50%",
                    "transform": "translateY(-25%)",
                    "white_space": "normal",
                },
            },
            {
                "label": "F&B / Merch Revenue",
                "value": f"{percent(food_bev_pct)} / {percent(merch_pct)}",
                "card_style": {
                    "min_height": "70px",
                    "padding": "0.4rem 0.4rem",
                    "border": "3px solid rgba(49, 51, 63, 0.2)",
                    "border_radius": "8px",
                    "background": "#ffffff",
                    "position": "relative",
                    "text_align": "center",
                    "font_family": "Georgia Bold",
                    "box_sizing": "border-box",
                    "margin_bottom": "0.5rem",
                },
                "label_style": {
                    "font_size": "19px",
                    "font_weight": "600",
                    "color": "#000000",
                    "line_height": "1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "0.3rem",
                },
                "value_style": {
                    "font_size": "32px",
                    "font_weight": "700",
                    "color": "#000000",
                    "line_height": "1.1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "50%",
                    "transform": "translateY(-25%)",
                    "white_space": "normal",
                },
            },
            {
                "label": "Ticket Revenue",
                "value": currency(numeric_sum(fan_master, "total_ticket_spend"), round_over_100=True),
                "card_style": {
                    "min_height": "70px",
                    "padding": "0.4rem 0.4rem",
                    "border": "3px solid rgba(49, 51, 63, 0.2)",
                    "border_radius": "8px",
                    "background": "#ffffff",
                    "position": "relative",
                    "text_align": "center",
                    "font_family": "Georgia Bold",
                    "box_sizing": "border-box",
                    "margin_bottom": "0.5rem",
                },
                "label_style": {
                    "font_size": "19px",
                    "font_weight": "600",
                    "color": "#000000",
                    "line_height": "1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "0.3rem",
                },
                "value_style": {
                    "font_size": "32px",
                    "font_weight": "700",
                    "color": "#000000",
                    "line_height": "1.1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "50%",
                    "transform": "translateY(-25%)",
                    "white_space": "normal",
                },
            },
            {
                "label": "Merch Revenue",
                "value": currency(numeric_sum(fan_master, "merch_net_total"), round_over_100=True),
                "card_style": {
                    "min_height": "70px",
                    "padding": "0.4rem 0.4rem",
                    "border": "3px solid rgba(49, 51, 63, 0.2)",
                    "border_radius": "8px",
                    "background": "#ffffff",
                    "position": "relative",
                    "text_align": "center",
                    "font_family": "Georgia Bold",
                    "box_sizing": "border-box",
                    "margin_bottom": "0.5rem",
                },
                "label_style": {
                    "font_size": "19px",
                    "font_weight": "600",
                    "color": "#000000",
                    "line_height": "1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "0.3rem",
                },
                "value_style": {
                    "font_size": "32px",
                    "font_weight": "700",
                    "color": "#000000",
                    "line_height": "1.1",
                    "position": "absolute",
                    "left": "0.45rem",
                    "right": "0.45rem",
                    "top": "50%",
                    "transform": "translateY(-25%)",
                    "white_space": "normal",
                },
            },
        ],
        st.columns(5),
    )


def filter_by_year(chart_df: pd.DataFrame, key: str) -> pd.DataFrame:
    if chart_df.empty or "year" not in chart_df.columns:
        return chart_df

    years = sorted(
        int(year)
        for year in pd.to_numeric(chart_df["year"], errors="coerce").dropna().unique()
    )
    options = ["All Years"] + [str(year) for year in years]
    selected_year = st.selectbox("Year", options, key=key)
    if selected_year == "All Years":
        return chart_df
    return chart_df[pd.to_numeric(chart_df["year"], errors="coerce").eq(int(selected_year))]


def create_yearly_revenue_trend_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Yearly Revenue Trend",
        chart_df=chart_df,
        x_axis_metric="year",
        y_axis_metric="net_sales",
        x_axis_title="Year",
        y_axis_title="Net Sales",
        color="#5dade2",
        y_format="$,.0f",
        title_style={
            "font_size": "24px",
            "font_weight": "650",
            "color": "#000000",
            "font_family": "Georgia Bold",
            "line_height": "1.2",
            "margin_top": "0.75rem",
            "margin_bottom": "0.5rem",
        },
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": False, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        bar_mark={"opacity": 1.0, "corner_radius": 0},
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 0, "dx": 0, "dy": 25, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_cumulative_revenue_chart(chart_df: pd.DataFrame) -> None:
    create_line_chart(
        title="Cumulative Revenue Over Time",
        chart_df=chart_df,
        x_axis_metric="date",
        y_axis_metric="cumulative_net_sales",
        x_axis_title="Date",
        y_axis_title="Cumulative Net Sales",
        x_axis_type="T",
        color="#5dade2",
        y_format="$,.0f",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        line_mark={"opacity": 1.0, "stroke_width": 2, "point": False},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_transaction_trend_chart(chart_df: pd.DataFrame) -> None:
    filtered_df = filter_by_year(chart_df, "transaction_trend_year")
    if not filtered_df.empty:
        filtered_df = filtered_df.copy()
        filtered_df["date_label"] = (
            pd.to_datetime(filtered_df["date"], errors="coerce")
            .dt.strftime("%b %d, %Y")
            .str.replace(" 0", " ", regex=False)
        )

    create_line_chart(
        title="Transaction Trend Analysis",
        chart_df=filtered_df,
        x_axis_metric="date_label",
        y_axis_metric="transaction_count",
        x_axis_title="Date",
        y_axis_title="Transactions per Day",
        x_axis_type="N",
        color="#f4b800",
        y_format=",.0f",
        x_sort=alt.EncodingSortField(field="date", order="ascending"),
        x_tooltip_metric="date",
        x_tooltip_type="T",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        line_mark={"opacity": 1.0, "stroke_width": 2, "point": True},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_daily_revenue_chart(chart_df: pd.DataFrame) -> None:
    filtered_df = filter_by_year(chart_df, "daily_revenue_year")
    if not filtered_df.empty:
        filtered_df = filtered_df.copy()
        filtered_df["date_label"] = (
            pd.to_datetime(filtered_df["date"], errors="coerce")
            .dt.strftime("%b %d, %Y")
            .str.replace(" 0", " ", regex=False)
        )

    create_line_chart(
        title="Daily Revenue Analysis",
        chart_df=filtered_df,
        x_axis_metric="date_label",
        y_axis_metric="net_sales",
        x_axis_title="Date",
        y_axis_title="Daily Net Sales",
        x_axis_type="N",
        color="#f2c94c",
        y_format="$,.0f",
        x_sort=alt.EncodingSortField(field="date", order="ascending"),
        x_tooltip_metric="date",
        x_tooltip_type="T",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        line_mark={"opacity": 1.0, "stroke_width": 2, "point": False},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_revenue_by_stand_location_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Revenue by Stand Location",
        chart_df=chart_df,
        x_axis_metric="stand_location",
        y_axis_metric="net_sales",
        x_axis_title="Stand Location",
        y_axis_title="Net Sales",
        color="#f2c94c",
        y_format="$,.0f",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": False, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 345, "offset": 0, "limit": 0, "overlap": False},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        bar_mark={"opacity": 1.0, "corner_radius": 0},
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 345, "dx": -15, "dy": 30, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_avg_transaction_size_by_stand_location_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Avg Transaction Size by Stand Location",
        chart_df=chart_df,
        x_axis_metric="stand_location",
        y_axis_metric="avg_transaction_value",
        x_axis_title="Stand Location",
        y_axis_title="Average Transaction Size",
        color="#5dade2",
        y_format="$,.0f",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": False, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 345, "offset": 0, "limit": 0, "overlap": False},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        bar_mark={"opacity": 1.0, "corner_radius": 0},
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 345, "dx": -15, "dy": 30, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_revenue_by_day_of_week_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Revenue by Day of Week",
        chart_df=chart_df,
        x_axis_metric="day_of_week",
        y_axis_metric="net_sales",
        x_axis_title="Day of Week",
        y_axis_title="Net Sales",
        color="#f2c94c",
        y_format="$,.0f",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": False, "font": "Georgia Bold", "font_size": 16, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 340, "offset": 0, "limit": 0, "overlap": False},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        bar_mark={"opacity": 1.0, "corner_radius": 0},
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 16, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 340, "dx": -10, "dy": 20, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_transaction_size_distribution_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Transaction Size Distribution",
        chart_df=chart_df,
        x_axis_metric="sales_range",
        y_axis_metric="count",
        x_axis_title="Transaction Size",
        y_axis_title="Transaction Count",
        color="#5dade2",
        y_format=",.0f",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": False, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        bar_mark={"opacity": 1.0, "corner_radius": 0},
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 0, "dx": 0, "dy": 25, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def render_chart_grid(metrics: dict) -> None:
    charts = metrics["charts"]

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        create_yearly_revenue_trend_chart(charts["yearly_revenue"])
    with row1_col2:
        create_cumulative_revenue_chart(charts["cumulative_revenue"])

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        create_transaction_trend_chart(charts["transaction_trend_analysis"])
    with row2_col2:
        create_daily_revenue_chart(charts["daily_revenue_analysis"])

    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        create_revenue_by_stand_location_chart(charts["stand_revenue"])
    with row3_col2:
        create_avg_transaction_size_by_stand_location_chart(charts["device_efficiency"])

    row4_col1, row4_col2 = st.columns(2)
    with row4_col1:
        create_revenue_by_day_of_week_chart(charts["revenue_by_day_of_week"])
    with row4_col2:
        create_transaction_size_distribution_chart(charts["transaction_size_distribution"])


def main() -> None:
    initialize_session_state()
    render_page_title("Food, Beverage, & Merchandise Insights")

    transaction_df = st.session_state.get("transaction_df")
    if transaction_df is None or transaction_df.empty:
        st.warning(
            "No transaction data found. Please upload transaction files on the "
            "Data Ingestion page."
        )
        st.stop()

    metrics = ensure_transaction_metrics()
    if not metrics:
        st.warning("Transaction metrics are not available yet.")
        st.stop()

    render_kpis(metrics, st.session_state.get("full_fan_master"))
    render_chart_grid(metrics)


main()
