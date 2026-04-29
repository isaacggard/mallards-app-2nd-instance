import altair as alt
import pandas as pd
import streamlit as st

from app import ensure_transaction_metrics, initialize_session_state, render_metric_card
from chart_utils import x_axis, y_axis, y_tooltip


def currency(value: float) -> str:
    return f"${value:,.2f}"


def percent(value: float) -> str:
    return f"{value:.1%}"


def render_kpis(metrics: dict) -> None:
    kpis = metrics["kpis"]
    kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
    render_metric_card(kpi1, "Total Revenue", currency(float(kpis["total_revenue"])))
    render_metric_card(
        kpi2,
        "Avg Transaction Value",
        currency(float(kpis["avg_transaction_value"])),
    )
    render_metric_card(
        kpi3,
        "Transactions per Day",
        f"{float(kpis['transactions_per_day']):,.1f}",
    )
    render_metric_card(
        kpi4,
        "% Revenue from Food & Beverage",
        percent(float(kpis["food_bev_revenue_pct"])),
    )
    render_metric_card(
        kpi5,
        "Revenue per Active Day",
        currency(float(kpis["revenue_per_active_day"])),
    )


def render_bar_chart(
    title: str,
    chart_df: pd.DataFrame,
    x_column: str,
    y_column: str,
    x_axis_title: str,
    y_axis_title: str,
    color: str = "#5dade2",
    label_angle: int = 0,
    y_format: str | None = None,
) -> None:
    st.subheader(title)
    if chart_df.empty:
        st.caption("No chart data available.")
        return

    chart = (
        alt.Chart(chart_df)
        .mark_bar(color=color)
        .encode(
            x=alt.X(
                f"{x_column}:N",
                title=x_axis_title,
                sort=None,
                axis=x_axis(label_angle),
            ),
            y=alt.Y(
                f"{y_column}:Q",
                title=y_axis_title,
                axis=y_axis(y_format),
            ),
            tooltip=[
                alt.Tooltip(f"{x_column}:N", title=x_axis_title),
                y_tooltip(f"{y_column}:Q", y_axis_title, y_format),
            ],
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_line_chart(
    title: str,
    chart_df: pd.DataFrame,
    x_column: str,
    y_column: str,
    x_axis_title: str,
    y_axis_title: str,
    color: str = "#5dade2",
    y_format: str | None = None,
) -> None:
    st.subheader(title)
    if chart_df.empty:
        st.caption("No chart data available.")
        return

    chart = (
        alt.Chart(chart_df)
        .mark_line(color=color)
        .encode(
            x=alt.X(
                f"{x_column}:T",
                title=x_axis_title,
                axis=x_axis(0),
            ),
            y=alt.Y(
                f"{y_column}:Q",
                title=y_axis_title,
                axis=y_axis(y_format),
            ),
            tooltip=[
                alt.Tooltip(f"{x_column}:T", title=x_axis_title),
                y_tooltip(f"{y_column}:Q", y_axis_title, y_format),
            ],
        )
    )
    st.altair_chart(chart, use_container_width=True)


def render_chart_grid(metrics: dict) -> None:
    charts = metrics["charts"]

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        render_bar_chart(
            "Yearly Revenue Trend",
            charts["yearly_revenue"],
            "year",
            "net_sales",
            "Year",
            "Net Sales",
            "#5dade2",
            y_format="$,.0f",
        )
    with row1_col2:
        render_bar_chart(
            "Revenue by Stand Location",
            charts["stand_revenue"],
            "stand_location",
            "net_sales",
            "Stand Location",
            "Net Sales",
            "#f2c94c",
            label_angle=-35,
            y_format="$,.0f",
        )

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        render_bar_chart(
            "Transaction Size Distribution",
            charts["transaction_size_distribution"],
            "sales_range",
            "count",
            "Transaction Size",
            "Transaction Count",
            "#5dade2",
            y_format=",.0f",
        )
    with row2_col2:
        render_bar_chart(
            "Revenue by Day of Week",
            charts["revenue_by_day_of_week"],
            "day_of_week",
            "net_sales",
            "Day of Week",
            "Net Sales",
            "#f2c94c",
            label_angle=-35,
            y_format="$,.0f",
        )

    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        render_bar_chart(
            "Device Efficiency: Avg Transaction Size by Stand Location",
            charts["device_efficiency"],
            "stand_location",
            "avg_transaction_value",
            "Stand Location",
            "Average Transaction Size",
            "#5dade2",
            label_angle=-35,
            y_format="$,.0f",
        )
    with row3_col2:
        render_line_chart(
            "Cumulative Revenue Over Time",
            charts["cumulative_revenue"],
            "date",
            "cumulative_net_sales",
            "Date",
            "Cumulative Net Sales",
            "#5dade2",
            y_format="$,.0f",
        )


def main() -> None:
    initialize_session_state()
    st.title("Transaction Insights")

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

    render_kpis(metrics)
    render_chart_grid(metrics)


main()
