import pandas as pd
import streamlit as st

from app import initialize_session_state, render_divider, render_page_title
from pages.fan_intelligence_metrics import prepare_fan_intelligence_metrics
from pages.render_components import (
    create_bar_chart,
    render_metric_cards,
    series_to_bar_data,
)


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


def render_kpi_row(metrics: dict) -> None:
    kpis = metrics["kpis"]
    render_metric_cards(
        [
            {
                "label": "Unique Fans",
                "value": format_count(kpis["unique_fans"]),
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
                "label": "Total Tickets",
                "value": format_count(kpis["total_tickets"]),
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
                "label": "Multi-Game Attendees",
                "value": format_percent(kpis["multi_game_rate"]),
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
                "label": "Merch Conversion",
                "value": format_percent(kpis["merch_conversion_rate"]),
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
                "label": "Avg Games Attended",
                "value": format_number(kpis["avg_games_attended"]),
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


def create_spend_per_fan_chart(chart_data: pd.Series) -> None:
    create_bar_chart(
        title="All Time $ Spent per Fan (Ticket + Merch)",
        chart_df=series_to_bar_data(chart_data, "category", "value"),
        x_axis_metric="category",
        y_axis_metric="value",
        x_axis_title="Total Spend per Ticket",
        y_axis_title="Fan Count",
        color="#f4b800",
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


def create_games_attended_chart(chart_data: pd.Series) -> None:
    create_bar_chart(
        title="Games Attended per Fan",
        chart_df=series_to_bar_data(chart_data, "category", "value"),
        x_axis_metric="category",
        y_axis_metric="value",
        x_axis_title="Games Attended",
        y_axis_title="Fan Count",
        color="#1a5c38",
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


def create_revenue_by_section_chart(chart_data: pd.Series) -> None:
    create_bar_chart(
        title="Revenue by Seating Section",
        chart_df=series_to_bar_data(chart_data, "category", "value"),
        x_axis_metric="category",
        y_axis_metric="value",
        x_axis_title="Seating Section Group",
        y_axis_title="Average Spend per Ticket",
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
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 345, "dx": -15, "dy": 20, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_merch_purchase_rate_by_section_chart(chart_data: pd.Series) -> None:
    create_bar_chart(
        title="Merchandise Purchase Rate by Section",
        chart_df=series_to_bar_data(chart_data, "category", "value"),
        x_axis_metric="category",
        y_axis_metric="value",
        x_axis_title="Seating Section Group",
        y_axis_title="Merchandise Purchase Rate",
        color="#b5530a",
        y_format=".0%",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": False, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 345, "offset": 0, "limit": 0, "overlap": False},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        bar_mark={"opacity": 1.0, "corner_radius": 0},
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 345, "dx": -15, "dy": 20, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def create_ticket_sales_by_day_chart(chart_data: pd.Series) -> None:
    create_bar_chart(
        title="Ticket Sales by Day of Week",
        chart_df=series_to_bar_data(chart_data, "category", "value"),
        x_axis_metric="category",
        y_axis_metric="value",
        x_axis_title="Day of Week",
        y_axis_title="Tickets Sold",
        color="#5dade2",
        y_format=",.0f",
        title_style={"font_size": "24px", "font_weight": "650", "color": "#000000", "font_family": "Georgia Bold", "line_height": "1.2", "margin_top": "0.75rem", "margin_bottom": "0.5rem"},
        x_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        y_axis={"grid": False, "domain": True, "domain_width": 1, "domain_color": "#000000", "ticks": True, "offset": 0},
        x_axis_bin_labels={"show": False, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 350, "offset": 0, "limit": 0, "overlap": False},
        y_axis_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 4, "angle": 0, "offset": 0},
        x_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 400, "color": "#FFFFFF", "padding": 25},
        y_axis_title_style={"show": True, "font": "Georgia Bold", "font_size": 17, "font_weight": 600, "color": "#000000", "padding": 10},
        bar_mark={"opacity": 1.0, "corner_radius": 0},
        bar_bin_labels={"show": True, "font": "Georgia Bold", "font_size": 15, "font_weight": 600, "color": "#000000", "axis_y_value": 0, "angle": 350, "dx": -5, "dy": 20, "align": "center", "baseline": "middle"},
        legend={"show": True, "label_font": "Georgia Bold", "label_font_size": 12, "label_font_weight": 400, "label_color": "#475467", "title_font": "Georgia Bold", "title_font_size": 13, "title_font_weight": 400, "title_color": "#344054"},
        view={"stroke_width": 0},
    )


def render_chart_grid(metrics: dict) -> None:
    charts = metrics["charts"]

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        create_spend_per_fan_chart(charts["ticket_spend_distribution"])
    with row1_col2:
        create_games_attended_chart(charts["games_attended_distribution"])

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        create_revenue_by_section_chart(charts["revenue_by_section"])
    with row2_col2:
        create_merch_purchase_rate_by_section_chart(charts["merch_conversion_by_section"])

    row3_col1, _ = st.columns(2)
    with row3_col1:
        create_ticket_sales_by_day_chart(charts["ticket_sales_by_day_of_week"])


def main() -> None:
    initialize_session_state()
    render_page_title("Fan Intelligence Dashboard")

    fan_master = st.session_state.get("full_fan_master")
    if fan_master is None or fan_master.empty:
        st.warning("No fan master dataset found. Build it on the main page.")
        st.stop()

    metrics = prepare_fan_intelligence_metrics(fan_master)

    date_range = format_date_range(metrics.get("metadata", {}))
    if date_range:
        st.caption(
            f"Games included: {date_range} - Data Excludes Internally Reserved Tickets"
        )

    render_kpi_row(metrics)
    render_divider()
    render_chart_grid(metrics)


main()
