import pandas as pd
import streamlit as st

from app import (
    ensure_survey_metrics,
    initialize_session_state,
    render_divider,
    render_header,
    render_page_title,
    render_subheader,
)
from pages.render_components import create_bar_chart, render_metric_cards


ALL_TEAMS = "All Teams"
ALL_YEARS = "All Years"
SENTIMENT_ORDER = ["Negative", "Neutral", "Positive"]


def format_number(value: int | float) -> str:
    return f"{value:,.0f}"


def format_score(value: float) -> str:
    return f"{value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def render_kpis(metrics: dict) -> None:
    kpis = metrics["kpis"]
    render_metric_cards(
        [
            {
                "label": "Total Survey Responses",
                "value": format_number(kpis["total_survey_responses"]),
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
                "label": "Average Sentiment",
                "value": format_score(kpis["average_sentiment"]),
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
                "label": "Negative Response Rate",
                "value": format_percent(kpis["negative_response_rate"]),
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
        st.columns(3),
    )


def filter_team_year(
    chart_df: pd.DataFrame,
    selected_team: str,
    selected_year: str,
) -> pd.DataFrame:
    filtered = chart_df
    if selected_team != ALL_TEAMS and "team" in filtered.columns:
        filtered = filtered[filtered["team"].astype(str).eq(selected_team)]
    if selected_year != ALL_YEARS and "survey_year" in filtered.columns:
        filtered = filtered[filtered["survey_year"].astype(str).eq(selected_year)]
    return filtered


def filter_exact_team_year(
    chart_df: pd.DataFrame,
    selected_team: str,
    selected_year: str,
) -> pd.DataFrame:
    filtered = chart_df
    if "team" in filtered.columns:
        filtered = filtered[filtered["team"].astype(str).eq(selected_team)]
    if "survey_year" in filtered.columns:
        filtered = filtered[filtered["survey_year"].astype(str).eq(selected_year)]
    return filtered


def create_response_sentiment_distribution_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Response Sentiment Distribution",
        chart_df=chart_df,
        x_axis_metric="sentiment_label",
        y_axis_metric="response_count",
        x_axis_title="Sentiment",
        y_axis_title="Response Count",
        color="#1c5b38",
        y_format=",.0f",
        title_style={
            "font_size": "24px",
            "font_weight": "650",
            "color": "#000000",
            "font_family": "Georgia Bold",
            "line_height": "1.2",
            "margin_top": "0.75rem",
            "margin_bottom": "0.5rem",
        },
        x_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        y_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        x_axis_bin_labels={
            "show": False,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 0,
            "offset": 0,
        },
        y_axis_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 0,
            "offset": 0,
        },
        x_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 400,
            "color": "#FFFFFF",
            "padding": 25,
        },
        y_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 10,
        },
        bar_mark={
            "opacity": 1.0,
            "corner_radius": 0,
        },
        bar_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "axis_y_value": 0,
            "angle": 0,
            "dx": 0,
            "dy": 25,
            "align": "center",
            "baseline": "middle",
        },
        legend={
            "show": True,
            "label_font": "Georgia Bold",
            "label_font_size": 12,
            "label_font_weight": 400,
            "label_color": "#475467",
            "title_font": "Georgia Bold",
            "title_font_size": 13,
            "title_font_weight": 400,
            "title_color": "#344054",
        },
        view={"stroke_width": 0},
    )


def create_response_sentiment_by_category_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Response Sentiment by Question Category",
        chart_df=chart_df,
        x_axis_metric="topic",
        y_axis_metric="sentiment_score",
        x_axis_title="Survey Category",
        y_axis_title="Sentiment (0-10)",
        color="#f2c94c",
        title_style={
            "font_size": "24px",
            "font_weight": "650",
            "color": "#000000",
            "font_family": "Georgia Bold",
            "line_height": "1.2",
            "margin_top": "0.75rem",
            "margin_bottom": "0.5rem",
        },
        x_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        y_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        x_axis_bin_labels={
            "show": False,
            "font": "Georgia Bold",
            "font_size": 16,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 350,
            "offset": 0,
            "limit": 0,
            "overlap": False,
        },
        y_axis_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 0,
            "offset": 0,
        },
        x_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 400,
            "color": "#FFFFFF",
            "padding": 25,
        },
        y_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 10,
        },
        bar_mark={
            "opacity": 1.0,
            "corner_radius": 0,
        },
        bar_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 16,
            "font_weight": 600,
            "color": "#000000",
            "axis_y_value": 0,
            "angle": 350,
            "dx": 0,
            "dy": 25,
            "align": "center",
            "baseline": "middle",
        },
        legend={
            "show": True,
            "label_font": "Georgia Bold",
            "label_font_size": 12,
            "label_font_weight": 400,
            "label_color": "#475467",
            "title_font": "Georgia Bold",
            "title_font_size": 13,
            "title_font_weight": 400,
            "title_color": "#344054",
        },
        view={"stroke_width": 0},
    )


def create_negative_rate_by_category_chart(chart_df: pd.DataFrame) -> None:
    create_bar_chart(
        title="Negative Rate by Category",
        chart_df=chart_df,
        x_axis_metric="topic",
        y_axis_metric="negative_rate",
        x_axis_title="Survey Category",
        y_axis_title="Negative Response Rate",
        color="#5dade2",
        y_format=".0%",
        title_style={
            "font_size": "24px",
            "font_weight": "650",
            "color": "#000000",
            "font_family": "Georgia Bold",
            "line_height": "1.2",
            "margin_top": "0.75rem",
            "margin_bottom": "0.5rem",
        },
        x_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        y_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        x_axis_bin_labels={
            "show": False,
            "font": "Georgia Bold",
            "font_size": 16,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 345,
            "offset": 0,
            "limit": 0,
            "overlap": False,
        },
        y_axis_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 0,
            "offset": 0,
        },
        x_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 400,
            "color": "#FFFFFF",
            "padding": 25,
        },
        y_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 10,
        },
        bar_mark={
            "opacity": 1.0,
            "corner_radius": 0,
        },
        bar_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 16,
            "font_weight": 600,
            "color": "#000000",
            "axis_y_value": 0,
            "angle": 345,
            "dx": -10,
            "dy": 25,
            "align": "center",
            "baseline": "middle",
        },
        legend={
            "show": True,
            "label_font": "Georgia Bold",
            "label_font_size": 12,
            "label_font_weight": 400,
            "label_color": "#475467",
            "title_font": "Georgia Bold",
            "title_font_size": 13,
            "title_font_weight": 400,
            "title_color": "#344054",
        },
        view={"stroke_width": 0},
    )


def create_average_sentiment_by_team_year_chart(
    chart_df: pd.DataFrame,
    color_metric: str | None,
) -> None:
    create_bar_chart(
        title="Average Sentiment by Team and Year",
        chart_df=chart_df,
        x_axis_metric="team_year",
        y_axis_metric="sentiment_score",
        x_axis_title="Team and Survey Year",
        y_axis_title="Sentiment (0-10)",
        color="#f2c94c",
        colors=["#f1b915", "#4cbfad", "#224433", "#e67e73", "#8e7cc3", "#6aa6a1"],
        color_metric=color_metric,
        color_title="Team",
        title_style={
            "font_size": "24px",
            "font_weight": "650",
            "color": "#000000",
            "font_family": "Georgia Bold",
            "line_height": "1.2",
            "margin_top": "0.75rem",
            "margin_bottom": "0.5rem",
        },
        x_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        y_axis={
            "grid": False,
            "domain": True,
            "domain_width": 1,
            "domain_color": "#000000",
            "ticks": True,
            "offset": 0,
        },
        x_axis_bin_labels={
            "show": False,
            "font": "Georgia Bold",
            "font_size": 16,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 345,
            "offset": 0,
            "limit": 0,
            "overlap": False,
        },
        y_axis_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 4,
            "angle": 0,
            "offset": 0,
        },
        x_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 400,
            "color": "#FFFFFF",
            "padding": 25,
        },
        y_axis_title_style={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 17,
            "font_weight": 600,
            "color": "#000000",
            "padding": 10,
        },
        bar_mark={
            "opacity": 1.0,
            "corner_radius": 0,
        },
        bar_bin_labels={
            "show": True,
            "font": "Georgia Bold",
            "font_size": 16,
            "font_weight": 600,
            "color": "#000000",
            "axis_y_value": 0,
            "angle": 345,
            "dx": -10,
            "dy": 25,
            "align": "center",
            "baseline": "middle",
        },
        legend={
            "show": True,
            "label_font": "Georgia Bold",
            "label_font_size": 12,
            "label_font_weight": 400,
            "label_color": "#475467",
            "title_font": "Georgia Bold",
            "title_font_size": 13,
            "title_font_weight": 400,
            "title_color": "#344054",
        },
        view={"stroke_width": 0},
    )


def selected_postgame_pulse(metrics: dict) -> dict:
    pulses = metrics.get("postgame_pulses") or []
    if not pulses:
        return metrics["recent_postgame"]

    options = [pulse["summary"]["option_label"] for pulse in pulses]
    if st.session_state.get("postgame_pulse_day") not in options:
        st.session_state.postgame_pulse_day = options[0]

    selected_label = st.selectbox(
        "Select a Postgame Survey:",
        options,
        key="postgame_pulse_day",
    )
    return pulses[options.index(selected_label)]


def render_postgame_short_answers(recent: dict) -> None:
    render_subheader("Written Responses")
    comments = recent.get("short_answer_comments", pd.DataFrame())
    if comments.empty:
        st.caption("No short-answer comments available for this postgame survey.")
        return

    topic_options = ["All Topics"] + sorted(
        comments["topic"].dropna().astype(str).unique().tolist()
    )
    available_sentiments = [
        sentiment
        for sentiment in SENTIMENT_ORDER
        if comments["sentiment_label"].astype(str).eq(sentiment).any()
    ]
    sentiment_options = ["All Sentiment"] + available_sentiments

    if st.session_state.get("postgame_topic_filter") not in topic_options:
        st.session_state.postgame_topic_filter = "All Topics"
    if st.session_state.get("postgame_sentiment_filter") not in sentiment_options:
        st.session_state.postgame_sentiment_filter = "All Sentiment"

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_topic = st.selectbox(
            "Topic",
            topic_options,
            key="postgame_topic_filter",
        )
    with filter_col2:
        selected_sentiment = st.selectbox(
            "Sentiment",
            sentiment_options,
            key="postgame_sentiment_filter",
        )

    filtered = comments
    if selected_topic != "All Topics":
        filtered = filtered[filtered["topic"].astype(str).eq(selected_topic)]
    if selected_sentiment != "All Sentiment":
        filtered = filtered[
            filtered["sentiment_label"].astype(str).eq(selected_sentiment)
        ]

    st.caption(f"{len(filtered):,} comments shown")
    if filtered.empty:
        return

    for question, question_comments in filtered.groupby("question", sort=True):
        with st.expander(
            f"{question} ({len(question_comments):,} replies)",
            expanded=False,
        ):
            for row in question_comments.itertuples(index=False):
                with st.container(border=True):
                    st.caption(
                        f"{row.topic} | {row.sentiment_label} | "
                        f"Sentiment {float(row.sentiment_index):.2f}/10"
                    )
                    st.write(str(row.comment))


def render_recent_postgame(metrics: dict) -> None:
    render_header("Postgame Pulse")
    st.caption(
        "Select an individual postgame survey for a fast readout of numerical "
        "ratings and written-comment sentiment."
    )
    recent = selected_postgame_pulse(metrics)
    summary = recent["summary"]

    render_metric_cards(
        [
            {
                "label": "Responses",
                "value": format_number(summary["response_count"]),
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
                "label": "Average Sentiment",
                "value": format_score(summary["average_sentiment"]),
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
                "label": "Negative Rate",
                "value": format_percent(summary["negative_rate"]),
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
        st.columns(3),
    )

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        create_response_sentiment_distribution_chart(recent["sentiment_distribution"])
    with row1_col2:
        create_response_sentiment_by_category_chart(recent["sentiment_by_category"])

    render_postgame_short_answers(recent)


def render_filters(metrics: dict) -> tuple[str, str]:
    metadata = metrics.get("metadata", {})
    team_options = [ALL_TEAMS] + metadata.get("teams", [])
    year_options = [ALL_YEARS] + metadata.get("years", [])

    if st.session_state.get("survey_team_filter") not in team_options:
        st.session_state.survey_team_filter = ALL_TEAMS
    if st.session_state.get("survey_year_filter") not in year_options:
        st.session_state.survey_year_filter = ALL_YEARS

    col1, col2 = st.columns(2)
    with col1:
        selected_team = st.selectbox(
            "Team",
            team_options,
            key="survey_team_filter",
        )
    with col2:
        selected_year = st.selectbox(
            "Survey Year",
            year_options,
            key="survey_year_filter",
        )
    return selected_team, selected_year


def render_historical_analysis(metrics: dict) -> None:
    render_header("Historical Survey Performance")
    st.caption(
        "Use team and year selections to compare sentiment across survey responses."
    )
    selected_team, selected_year = render_filters(metrics)
    charts = metrics["charts"]

    sentiment_distribution = filter_exact_team_year(
        charts["historical_sentiment_distribution"],
        selected_team,
        selected_year,
    )
    sentiment_by_category = filter_exact_team_year(
        charts["historical_sentiment_by_category"],
        selected_team,
        selected_year,
    ).sort_values("sentiment_score", ascending=False)
    negative_rate_by_category = filter_exact_team_year(
        charts["historical_negative_rate_by_category"],
        selected_team,
        selected_year,
    ).sort_values("negative_rate", ascending=False)
    average_sentiment = filter_team_year(
        charts["average_sentiment_by_team_year"],
        selected_team,
        selected_year,
    ).sort_values(["team", "survey_year"])

    if not average_sentiment.empty:
        average_sentiment = average_sentiment.copy()
        average_sentiment["team_year"] = (
            average_sentiment["team"].astype(str)
            + " "
            + average_sentiment["survey_year"].astype(str)
        )

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        create_response_sentiment_distribution_chart(sentiment_distribution)
    with row1_col2:
        create_response_sentiment_by_category_chart(sentiment_by_category)

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        create_negative_rate_by_category_chart(negative_rate_by_category)
    with row2_col2:
        create_average_sentiment_by_team_year_chart(
            average_sentiment,
            color_metric="team" if selected_team == ALL_TEAMS else None,
        )


def main() -> None:
    initialize_session_state()
    render_page_title("Survey Sentiment Analyzer")

    survey_df = st.session_state.get("survey_df")
    if survey_df is None or survey_df.empty:
        st.warning(
            "No survey data found. Please upload survey files on the Data "
            "Ingestion page."
        )
        st.stop()

    metrics = ensure_survey_metrics()
    if not metrics:
        st.warning("Survey metrics are not available yet.")
        st.stop()
    render_kpis(metrics)
    render_divider()
    render_recent_postgame(metrics)
    render_divider()
    render_historical_analysis(metrics)


main()
