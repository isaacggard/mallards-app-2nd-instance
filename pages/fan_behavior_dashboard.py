import altair as alt
import pandas as pd
import streamlit as st

from app import (
    ensure_fan_behavior_metrics,
    initialize_session_state,
    render_metric_card,
)
from chart_utils import x_axis, y_axis, y_tooltip


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def format_number(value: float) -> str:
    return f"{value:,.1f}"


def render_kpi_row(metrics: dict) -> None:
    kpis = metrics["kpis"]
    col1, col2, col3, col4, col5 = st.columns(5)
    render_metric_card(
        col1,
        "Avg Revenue per Fan",
        format_currency(kpis["avg_revenue_per_fan"]),
    )
    render_metric_card(
        col2,
        "% Multi-Game Attendees",
        format_percent(kpis["multi_game_rate"]),
    )
    render_metric_card(
        col3,
        "Avg Spend per Game",
        format_currency(kpis["avg_spend_per_game_per_fan"]),
    )
    render_metric_card(
        col4,
        "Merch Conversion",
        format_percent(kpis["merch_conversion_rate"]),
    )
    render_metric_card(
        col5,
        "Avg Games Attended",
        format_number(kpis["avg_games_attended"]),
    )


def render_bar_chart(
    title: str,
    chart_data: pd.Series,
    x_axis_title: str,
    y_axis_title: str,
    color: str,
    label_angle: int = 0,
    y_format: str | None = None,
    description: str | None = None,
) -> None:
    st.subheader(title)
    if description:
        st.caption(description)
    if chart_data.empty:
        st.caption("No chart data available.")
        return

    chart_df = chart_data.reset_index()
    chart_df.columns = ["category", "value"]
    chart_df["category"] = chart_df["category"].astype(str)
    chart = (
        alt.Chart(chart_df)
        .mark_bar(color=color)
        .encode(
            x=alt.X(
                "category:N",
                title=x_axis_title,
                sort=None,
                axis=x_axis(label_angle),
            ),
            y=alt.Y(
                "value:Q",
                title=y_axis_title,
                axis=y_axis(y_format),
            ),
            tooltip=[
                alt.Tooltip("category:N", title=x_axis_title),
                y_tooltip("value:Q", y_axis_title, y_format),
            ],
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_chart_grid(metrics: dict) -> None:
    charts = metrics["charts"]

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        render_bar_chart(
            "Total Spend per Fan (Ticket + Merch)",
            charts["fan_spend_distribution"],
            "Total Spend per Fan",
            "Fan Count",
            "#f2c94c",
            y_format=",.0f",
        )
    with row1_col2:
        render_bar_chart(
            "Revenue by Seating Section",
            charts["revenue_by_section"],
            "Seating Section Group",
            "Average Spend",
            "#5dade2",
            label_angle=-35,
            y_format="$,.0f",
        )

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        render_bar_chart(
            "Merchandise Purchase Rate by Seating Section",
            charts["merch_conversion_by_section"],
            "Seating Section Group",
            "Merchandise Purchase Rate",
            "#5dade2",
            label_angle=-35,
            y_format=".0%",
        )
    with row2_col2:
        render_bar_chart(
            "Average Spend: Merchandise Buyers vs Non-Buyers",
            charts["average_spend_by_merch_buyer"],
            "Merchandise Buyer Status",
            "Average Spend",
            "#f2c94c",
            y_format="$,.0f",
        )

    render_bar_chart(
        "Average Spend by Fan Tenure",
        charts["tenure_spend_by_bin"],
        "Fan Tenure",
        "Average Spend per Game",
        "#5dade2",
        y_format="$,.0f",
        description=(
            "Fan tenure is the number of days between a fan's first and "
            "most recent attended game."
        ),
    )


def main() -> None:
    initialize_session_state()
    st.title("Fan Behavior Dashboard")

    fan_master = st.session_state.get("full_fan_master")
    if fan_master is None or fan_master.empty:
        st.warning("No fan master dataset found. Build it on the main page.")
        st.stop()

    metrics = ensure_fan_behavior_metrics()
    if not metrics:
        st.warning("Fan behavior metrics are not available yet.")
        st.stop()

    render_kpi_row(metrics)
    render_chart_grid(metrics)


main()
