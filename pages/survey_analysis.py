import altair as alt
import pandas as pd
import streamlit as st

from app import ensure_survey_metrics, initialize_session_state, render_metric_card
from chart_utils import x_axis, y_axis, y_tooltip


ALL_TEAMS = "All Teams"
ALL_YEARS = "All Years"


def format_number(value: int | float) -> str:
    return f"{value:,.0f}"


def format_score(value: float) -> str:
    return f"{value:,.2f}"


def format_percent(value: float) -> str:
    return f"{value:.1%}"


def render_kpis(metrics: dict) -> None:
    kpis = metrics["kpis"]
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    render_metric_card(
        kpi1,
        "Total Survey Responses",
        format_number(kpis["total_survey_responses"]),
    )
    render_metric_card(
        kpi2,
        "Average Numeric Rating",
        format_score(kpis["avg_numeric_rating"]),
    )
    render_metric_card(
        kpi3,
        "Short-Answer Sentiment",
        format_score(kpis["overall_sentiment_index"]),
    )
    render_metric_card(
        kpi4,
        "Negative Response Rate",
        format_percent(kpis["negative_response_rate"]),
    )
    st.caption(
        "Average Numeric Rating uses survey questions answered with numbers. "
        "Short-Answer Sentiment uses VADER on written comments and converts "
        "the result to a 0-10 score, where 5 is neutral."
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


def filter_topic_team_year(
    chart_df: pd.DataFrame,
    selected_team: str,
    selected_year: str,
) -> pd.DataFrame:
    filtered = chart_df
    if "team" in filtered.columns:
        filtered = filtered[filtered["team"].astype(str).eq(selected_team)]
    if selected_year != ALL_YEARS and "survey_year" in filtered.columns:
        filtered = filtered[filtered["survey_year"].astype(str).eq(selected_year)]
    return filtered


def filter_topic_summary(
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


def render_bar_chart(
    title: str,
    chart_df: pd.DataFrame,
    x_column: str,
    y_column: str,
    x_axis_title: str,
    y_axis_title: str,
    *,
    color_column: str | None = None,
    color_title: str | None = None,
    color: str = "#5dade2",
    label_angle: int = 0,
    y_format: str | None = None,
    x_offset_column: str | None = None,
) -> None:
    st.subheader(title)
    if chart_df.empty:
        st.caption("No chart data available.")
        return

    encoding = {
        "x": alt.X(
            f"{x_column}:N",
            title=x_axis_title,
            sort=None,
            axis=x_axis(label_angle),
        ),
        "y": alt.Y(
            f"{y_column}:Q",
            title=y_axis_title,
            axis=y_axis(y_format),
        ),
        "tooltip": [
            alt.Tooltip(f"{x_column}:N", title=x_axis_title),
            y_tooltip(f"{y_column}:Q", y_axis_title, y_format),
        ],
    }
    if color_column:
        encoding["color"] = alt.Color(
            f"{color_column}:N",
            title=color_title or color_column.replace("_", " ").title(),
        )
        encoding["tooltip"].append(
            alt.Tooltip(
                f"{color_column}:N",
                title=color_title or color_column.replace("_", " ").title(),
            )
        )
    if x_offset_column:
        encoding["xOffset"] = alt.XOffset(f"{x_offset_column}:N")

    if color_column:
        chart = alt.Chart(chart_df).mark_bar()
    else:
        chart = alt.Chart(chart_df).mark_bar(color=color)
    chart = chart.encode(**encoding)

    st.altair_chart(chart, use_container_width=True)


def render_comment_list(title: str, comments: pd.DataFrame) -> None:
    st.subheader(title)
    if comments.empty:
        st.caption("No comments available.")
        return

    for row in comments.itertuples(index=False):
        with st.container(border=True):
            question = getattr(row, "question", "")
            if question:
                st.caption(f"{row.topic} | {question}")
            else:
                st.caption(str(row.topic))
            st.write(str(row.comment))


def selected_postgame_pulse(metrics: dict) -> dict:
    pulses = metrics.get("postgame_pulses") or []
    if not pulses:
        return metrics["recent_postgame"]

    options = [pulse["summary"]["option_label"] for pulse in pulses]
    if st.session_state.get("postgame_pulse_day") not in options:
        st.session_state.postgame_pulse_day = options[0]

    selected_label = st.selectbox(
        "Postgame survey day",
        options,
        key="postgame_pulse_day",
    )
    return pulses[options.index(selected_label)]


def render_recent_postgame(metrics: dict) -> None:
    st.header("Postgame Pulse")
    st.caption(
        "Select an individual postgame survey for a fast readout of numerical "
        "ratings and written-comment sentiment. The default selection is the "
        "most recent postgame survey."
    )
    recent = selected_postgame_pulse(metrics)
    summary = recent["summary"]

    with st.container(border=True):
        st.subheader(summary["label"])

        col1, col2, col3, col4 = st.columns(4)
        render_metric_card(
            col1,
            "Responses",
            format_number(summary["response_count"]),
        )
        render_metric_card(
            col2,
            "Average Rating",
            format_score(summary["avg_rating"]),
        )
        render_metric_card(
            col3,
            "Short-Answer Sentiment",
            format_score(summary["sentiment_index"]),
        )
        render_metric_card(
            col4,
            "Negative Rate",
            format_percent(summary["negative_rate"]),
        )

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        render_bar_chart(
            "Latest Ratings by Category",
            recent["topic_rating"],
            "topic",
            "avg_rating",
            "Survey Category",
            "Average Rating",
            color="#f2c94c",
            label_angle=-35,
        )
    with row1_col2:
        render_bar_chart(
            "Latest Short-Answer Sentiment by Category",
            recent["topic_sentiment"],
            "topic",
            "sentiment_index",
            "Survey Category",
            "Sentiment Score (0-10)",
            color="#5dade2",
            label_angle=-35,
        )

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        render_comment_list("Recent Positive Comments", recent["positive_comments"])
    with row2_col2:
        render_comment_list("Recent Opportunity Comments", recent["negative_comments"])


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
    st.header("Historical Survey Performance")
    st.caption(
        "Use team and year selections to compare category ratings, sentiment, "
        "and response volume across seasons."
    )
    selected_team, selected_year = render_filters(metrics)
    charts = metrics["charts"]

    response_volume = filter_team_year(
        charts["responses_by_team_year"],
        selected_team,
        selected_year,
    )
    rating_by_team_year = filter_team_year(
        charts["rating_by_team_year"],
        selected_team,
        selected_year,
    )
    topic_rating = filter_topic_team_year(
        charts["topic_rating_by_year"],
        selected_team,
        selected_year,
    )
    topic_sentiment = filter_topic_team_year(
        charts["topic_sentiment_by_year"],
        selected_team,
        selected_year,
    )
    topic_text_summary = filter_topic_summary(
        charts["topic_text_summary"],
        selected_team,
        selected_year,
    )
    negative_rate_by_topic = topic_text_summary.sort_values(
        "negative_rate",
        ascending=False,
    )
    sentiment_by_topic = topic_text_summary.sort_values(
        "sentiment_index",
        ascending=False,
    )

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        render_bar_chart(
            "Response Volume by Team and Year",
            response_volume,
            "survey_year",
            "response_count",
            "Survey Year",
            "Survey Responses",
            color_column="team" if selected_team == ALL_TEAMS else "survey_type",
            color_title="Team" if selected_team == ALL_TEAMS else "Survey Type",
            y_format=",.0f",
        )
    with row1_col2:
        render_bar_chart(
            "Average Rating by Team and Year",
            rating_by_team_year,
            "team_year",
            "avg_rating",
            "Survey Year and Team",
            "Average Rating",
            color_column="team" if selected_team == ALL_TEAMS else None,
            color_title="Team",
            color="#f2c94c",
            label_angle=-35,
        )

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        render_bar_chart(
            "Category Rating Year over Year",
            topic_rating,
            "topic",
            "avg_rating",
            "Survey Category",
            "Average Rating",
            color_column="survey_year",
            color_title="Survey Year",
            label_angle=-35,
            x_offset_column="survey_year",
        )
    with row2_col2:
        render_bar_chart(
            "Category Short-Answer Sentiment Year over Year",
            topic_sentiment,
            "topic",
            "sentiment_index",
            "Survey Category",
            "Sentiment Score (0-10)",
            color_column="survey_year",
            color_title="Survey Year",
            label_angle=-35,
            x_offset_column="survey_year",
        )

    row3_col1, row3_col2 = st.columns(2)
    with row3_col1:
        render_bar_chart(
            "Negative Rate by Category",
            negative_rate_by_topic,
            "topic",
            "negative_rate",
            "Survey Category",
            "Negative Response Rate",
            color="#5dade2",
            label_angle=-35,
            y_format=".0%",
        )
    with row3_col2:
        render_bar_chart(
            "Sentiment by Category",
            sentiment_by_topic,
            "topic",
            "sentiment_index",
            "Survey Category",
            "Sentiment Score (0-10)",
            color="#f2c94c",
            label_angle=-35,
        )

    render_bar_chart(
        "Top Opportunity Areas",
        charts["top_opportunity_areas"],
        "topic",
        "opportunity_score",
        "Survey Category",
        "Opportunity Score",
        color="#f2c94c",
        label_angle=-35,
    )


def render_short_answer_center(metrics: dict) -> None:
    st.header("Short Answer Center")
    st.caption(
        "Select a survey result to review every written response for that survey. "
        "Use the filters to move quickly between topics and sentiment groups."
    )
    center = metrics.get("short_answer_center", {})
    options_df = center.get("options", pd.DataFrame())
    comments = center.get("comments", pd.DataFrame())
    if options_df.empty or comments.empty:
        st.caption("No short-answer comments available.")
        return

    options = options_df["survey_label"].astype(str).tolist()
    if st.session_state.get("short_answer_survey_result") not in options:
        st.session_state.short_answer_survey_result = options[0]

    selected_label = st.selectbox(
        "Survey result",
        options,
        key="short_answer_survey_result",
    )
    selected_key = options_df.loc[
        options_df["survey_label"].astype(str).eq(selected_label),
        "event_key",
    ].iloc[0]
    selected_comments = comments[comments["event_key"].eq(selected_key)]

    topic_options = ["All Topics"] + sorted(
        selected_comments["topic"].dropna().astype(str).unique().tolist()
    )
    sentiment_options = ["All Sentiment"] + sorted(
        selected_comments["sentiment_label"].dropna().astype(str).unique().tolist()
    )

    filter_col1, filter_col2 = st.columns(2)
    with filter_col1:
        selected_topic = st.selectbox(
            "Topic",
            topic_options,
            key="short_answer_topic_filter",
        )
    with filter_col2:
        selected_sentiment = st.selectbox(
            "Sentiment",
            sentiment_options,
            key="short_answer_sentiment_filter",
        )

    filtered = selected_comments
    if selected_topic != "All Topics":
        filtered = filtered[filtered["topic"].astype(str).eq(selected_topic)]
    if selected_sentiment != "All Sentiment":
        filtered = filtered[
            filtered["sentiment_label"].astype(str).eq(selected_sentiment)
        ]

    st.caption(f"{len(filtered):,} comments shown")
    for question, question_comments in filtered.groupby("question", sort=True):
        with st.expander(
            f"{question} ({len(question_comments):,} replies)",
            expanded=True,
        ):
            for row in question_comments.itertuples(index=False):
                with st.container(border=True):
                    st.caption(
                        f"{row.topic} | {row.sentiment_label} | "
                        f"Sentiment {float(row.sentiment_index):.2f}/10"
                    )
                    st.write(str(row.comment))


def main() -> None:
    initialize_session_state()
    st.title("Survey Analysis")

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
    render_recent_postgame(metrics)
    render_historical_analysis(metrics)
    render_short_answer_center(metrics)


main()
