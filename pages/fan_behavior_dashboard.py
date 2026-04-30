import altair as alt
import pandas as pd
import streamlit as st

from app import (
    initialize_session_state,
)
from chart_utils import x_axis, y_axis, y_tooltip
from pages.fan_intelligence_metrics import prepare_fan_intelligence_metrics


def format_currency(value: float) -> str:
    return f"${value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def format_number(value: float) -> str:
    return f"{value:,.1f}"


def format_count(value: float) -> str:
    return f"{value:,.0f}"


def format_date_range(metadata: dict) -> str | None:
    first_game = pd.to_datetime(metadata.get("first_game"), errors="coerce")
    last_game = pd.to_datetime(metadata.get("last_game"), errors="coerce")
    if pd.isna(first_game) or pd.isna(last_game):
        return None
    return (
        f"{first_game:%B} {first_game.day}, {first_game:%Y} - "
        f"{last_game:%B} {last_game.day}, {last_game:%Y}"
    )


def render_metric_card(column, label: str, value: str) -> None:
    with column.container(border=True):
        st.markdown(
            (
                "<div style='"
                "min-height:88px;"
                "position:relative;"
                "text-align:center;"
                "'>"
                "<div style='"
                "position:absolute;"
                "left:0;"
                "right:0;"
                "top:0.25rem;"
                "font-size:19px;"
                "color:#667085;"
                "line-height:1.15;"
                f"'>{label}</div>"
                "<div style='"
                "position:absolute;"
                "left:0;"
                "right:0;"
                "top:50%;"
                "transform:translateY(-50%);"
                "font-size:32px;"
                "font-weight:700;"
                "line-height:1.1;"
                "'>"
                f"{value}</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def render_kpi_row(metrics: dict) -> None:
    kpis = metrics["kpis"]
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    render_metric_card(
        col1,
        "Unique Fans",
        format_count(kpis["unique_fans"]),
    )
    render_metric_card(
        col2,
        "Total Tickets",
        format_count(kpis["total_tickets"]),
    )
    render_metric_card(
        col3,
        "Avg Revenue per Ticket",
        format_currency(kpis["avg_revenue_per_ticket"]),
    )
    render_metric_card(
        col4,
        "Multi-Game Attendees",
        format_percent(kpis["multi_game_rate"]),
    )
    render_metric_card(
        col5,
        "Merch Conversion",
        format_percent(kpis["merch_conversion_rate"]),
    )
    render_metric_card(
        col6,
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
            "Total Spend per Ticket (Ticket + Merch)",
            charts["ticket_spend_distribution"],
            "Total Spend per Ticket",
            "Fan Count",
            "#f2c94c",
            y_format=",.0f",
        )
    with row1_col2:
        render_bar_chart(
            "Revenue by Seating Section",
            charts["revenue_by_section"],
            "Seating Section Group",
            "Average Spend per Ticket",
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
            "Average Spend per Ticket",
            "#f2c94c",
            y_format="$,.0f",
        )

    render_bar_chart(
        "Average Spend by Fan Tenure",
        charts["tenure_spend_by_bin"],
        "Fan Tenure",
        "Average Spend per Ticket",
        "#5dade2",
        y_format="$,.0f",
        description=(
            "Fan tenure is the number of days between a fan's first and "
            "most recent attended game."
        ),
    )

    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        render_bar_chart(
            "Ticket Sales by Day of Week",
            charts["ticket_sales_by_day_of_week"],
            "Day of Week",
            "Tickets Sold",
            "#5dade2",
            y_format=",.0f",
            description="Single game buyers only (ticket_type = Single).",
        )
    with row3_col2:
        render_bar_chart(
            "Games Attended per Fan",
            charts["games_attended_distribution"],
            "Games Attended",
            "Fan Count",
            "#f2c94c",
            y_format=",.0f",
        )


def main() -> None:
    initialize_session_state()
    st.title("Fan Intelligence Dashboard")

    fan_master = st.session_state.get("full_fan_master")
    if fan_master is None or fan_master.empty:
        st.warning("No fan master dataset found. Build it on the main page.")
        st.stop()

    metrics = prepare_fan_intelligence_metrics(fan_master)

    date_range = format_date_range(metrics.get("metadata", {}))
    if date_range:
        st.caption(f"Games included: {date_range}")

    render_kpi_row(metrics)
    render_chart_grid(metrics)


main()
