from html import escape
from typing import Any

import altair as alt
import pandas as pd
import streamlit as st


AXIS_FRAME_STYLE_KEYS = {
    "grid": "grid",
    "domain": "domain",
    "domain_width": "domainWidth",
    "domain_color": "domainColor",
    "ticks": "ticks",
    "offset": "offset",
    "translate": "translate",
}

AXIS_BIN_LABEL_STYLE_KEYS = {
    **AXIS_FRAME_STYLE_KEYS,
    "show": "labels",
    "font": "labelFont",
    "font_family": "labelFont",
    "font_size": "labelFontSize",
    "font_weight": "labelFontWeight",
    "color": "labelColor",
    "padding": "labelPadding",
    "angle": "labelAngle",
    "offset": "labelOffset",
    "align": "labelAlign",
    "baseline": "labelBaseline",
    "limit": "labelLimit",
    "overlap": "labelOverlap",
}

AXIS_TITLE_STYLE_KEYS = {
    **AXIS_FRAME_STYLE_KEYS,
    "font": "titleFont",
    "font_family": "titleFont",
    "font_size": "titleFontSize",
    "font_weight": "titleFontWeight",
    "color": "titleColor",
    "padding": "titlePadding",
    "angle": "titleAngle",
    "x": "titleX",
    "y": "titleY",
    "align": "titleAlign",
    "anchor": "titleAnchor",
    "baseline": "titleBaseline",
}

BAR_MARK_STYLE_KEYS = {
    "opacity": "opacity",
    "corner_radius": "cornerRadius",
    "stroke": "stroke",
    "stroke_width": "strokeWidth",
}

LINE_MARK_STYLE_KEYS = {
    "opacity": "opacity",
    "stroke_width": "strokeWidth",
    "point": "point",
    "interpolate": "interpolate",
}

BAR_BIN_LABEL_MARK_KEYS = {
    "font": "font",
    "font_family": "font",
    "font_size": "fontSize",
    "font_weight": "fontWeight",
    "color": "color",
    "angle": "angle",
    "x": "x",
    "y": "y",
    "dx": "dx",
    "dy": "dy",
    "align": "align",
    "baseline": "baseline",
}


def inline_style(style: dict[str, Any]) -> str:
    return "; ".join(
        f"{key.replace('_', '-')}: {value}"
        for key, value in style.items()
        if value is not None
    )


def mapped_kwargs(style: dict[str, Any], key_map: dict[str, str]) -> dict[str, Any]:
    return {
        target_key: style[source_key]
        for source_key, target_key in key_map.items()
        if style.get(source_key) is not None
    }


def render_text_title(title: str, style: dict[str, Any]) -> None:
    st.markdown(
        f"<div style='{inline_style(style)}'>{escape(title)}</div>",
        unsafe_allow_html=True,
    )


def render_metric_card(
    column: Any,
    label: str,
    value: str,
    *,
    card_style: dict[str, Any],
    label_style: dict[str, Any],
    value_style: dict[str, Any],
    detail: str | None = None,
    detail_style: dict[str, Any] | None = None,
) -> None:
    detail_html = ""
    if detail and detail_style:
        detail_html = (
            f"<div style='{inline_style(detail_style)}'>{escape(detail)}</div>"
        )

    with column:
        st.markdown(
            (
                f"<div style='{inline_style(card_style)}'>"
                f"<div style='{inline_style(label_style)}'>{escape(label)}</div>"
                f"<div style='{inline_style(value_style)}'>{escape(value)}</div>"
                f"{detail_html}"
                "</div>"
            ),
            unsafe_allow_html=True,
        )


def render_metric_cards(card_specs: list[dict[str, Any]], columns: list[Any]) -> None:
    for column, card in zip(columns, card_specs):
        render_metric_card(column, **card)


def series_to_bar_data(
    chart_data: pd.Series,
    x_axis_metric: str,
    y_axis_metric: str,
) -> pd.DataFrame:
    chart_df = chart_data.reset_index()
    chart_df.columns = [x_axis_metric, y_axis_metric]
    chart_df[x_axis_metric] = chart_df[x_axis_metric].astype(str)
    return chart_df


def altair_axis(
    axis_style: dict[str, Any],
    bin_label_style: dict[str, Any],
    title_style: dict[str, Any],
    number_format: str | None = None,
) -> alt.Axis:
    kwargs = mapped_kwargs(axis_style, AXIS_FRAME_STYLE_KEYS)
    kwargs.update(mapped_kwargs(bin_label_style, AXIS_BIN_LABEL_STYLE_KEYS))
    kwargs.update(mapped_kwargs(title_style, AXIS_TITLE_STYLE_KEYS))
    if not title_style.get("show", True):
        kwargs["title"] = None
    if number_format:
        kwargs["format"] = number_format
    return alt.Axis(**kwargs)


def y_tooltip(column: str, title: str, number_format: str | None = None) -> alt.Tooltip:
    if number_format:
        return alt.Tooltip(column, title=title, format=number_format)
    return alt.Tooltip(column, title=title)


def bar_bin_label_chart(
    chart_df: pd.DataFrame,
    x_axis_metric: str,
    label_style: dict[str, Any],
):
    if not label_style.get("show", False):
        return None

    label_df = chart_df[[x_axis_metric]].drop_duplicates().copy()
    label_df["__bar_bin_label_axis_y"] = label_style.get("axis_y_value", 0)
    text_metric = label_style.get("text_metric", x_axis_metric)
    return (
        alt.Chart(label_df)
        .mark_text(**mapped_kwargs(label_style, BAR_BIN_LABEL_MARK_KEYS))
        .encode(
            x=alt.X(f"{x_axis_metric}:N", sort=None),
            y=alt.Y("__bar_bin_label_axis_y:Q"),
            text=alt.Text(f"{text_metric}:N"),
        )
    )


def style_altair_chart(
    chart,
    *,
    legend: dict[str, Any],
    view: dict[str, Any],
):
    configured_chart = chart.configure_view(strokeWidth=view["stroke_width"])
    if legend.get("show", True):
        return configured_chart.configure_legend(
            labelFont=legend["label_font"],
            titleFont=legend["title_font"],
            labelColor=legend["label_color"],
            titleColor=legend["title_color"],
            labelFontSize=legend["label_font_size"],
            titleFontSize=legend["title_font_size"],
            labelFontWeight=legend["label_font_weight"],
            titleFontWeight=legend["title_font_weight"],
        )
    return configured_chart.configure_legend(disable=True)


def create_bar_chart(
    *,
    title: str,
    chart_df: pd.DataFrame,
    x_axis_metric: str,
    y_axis_metric: str,
    x_axis_title: str,
    y_axis_title: str,
    title_style: dict[str, Any],
    x_axis: dict[str, Any],
    y_axis: dict[str, Any],
    x_axis_bin_labels: dict[str, Any],
    y_axis_bin_labels: dict[str, Any],
    x_axis_title_style: dict[str, Any],
    y_axis_title_style: dict[str, Any],
    bar_mark: dict[str, Any],
    bar_bin_labels: dict[str, Any],
    legend: dict[str, Any],
    view: dict[str, Any],
    color: str | None = None,
    colors: list[str] | None = None,
    color_metric: str | None = None,
    color_title: str | None = None,
    y_format: str | None = None,
    x_offset_metric: str | None = None,
    description: str | None = None,
) -> None:
    render_text_title(title, title_style)
    if description:
        st.caption(description)
    if chart_df.empty:
        st.caption("No chart data available.")
        return

    mark_kwargs = mapped_kwargs(bar_mark, BAR_MARK_STYLE_KEYS)
    if color:
        mark_kwargs["color"] = color

    tooltip = [
        alt.Tooltip(f"{x_axis_metric}:N", title=x_axis_title),
        y_tooltip(f"{y_axis_metric}:Q", y_axis_title, y_format),
    ]
    encoding: dict[str, Any] = {
        "x": alt.X(
            f"{x_axis_metric}:N",
            title=x_axis_title,
            sort=None,
            axis=altair_axis(x_axis, x_axis_bin_labels, x_axis_title_style),
        ),
        "y": alt.Y(
            f"{y_axis_metric}:Q",
            title=y_axis_title,
            axis=altair_axis(
                y_axis,
                y_axis_bin_labels,
                y_axis_title_style,
                y_format,
            ),
        ),
        "tooltip": tooltip,
    }

    if color_metric:
        color_kwargs: dict[str, Any] = {
            "title": color_title or color_metric.replace("_", " ").title(),
        }
        if colors:
            color_kwargs["scale"] = alt.Scale(range=colors)
        encoding["color"] = alt.Color(
            f"{color_metric}:N",
            **color_kwargs,
        )
        tooltip.append(
            alt.Tooltip(
                f"{color_metric}:N",
                title=color_title or color_metric.replace("_", " ").title(),
            )
        )
    if x_offset_metric:
        encoding["xOffset"] = alt.XOffset(f"{x_offset_metric}:N")

    chart = alt.Chart(chart_df).mark_bar(**mark_kwargs).encode(**encoding)
    label_chart = bar_bin_label_chart(chart_df, x_axis_metric, bar_bin_labels)
    if label_chart is not None:
        chart = chart + label_chart

    st.altair_chart(
        style_altair_chart(chart, legend=legend, view=view),
        use_container_width=True,
    )


def create_line_chart(
    *,
    title: str,
    chart_df: pd.DataFrame,
    x_axis_metric: str,
    y_axis_metric: str,
    x_axis_title: str,
    y_axis_title: str,
    x_axis_type: str,
    title_style: dict[str, Any],
    x_axis: dict[str, Any],
    y_axis: dict[str, Any],
    x_axis_bin_labels: dict[str, Any],
    y_axis_bin_labels: dict[str, Any],
    x_axis_title_style: dict[str, Any],
    y_axis_title_style: dict[str, Any],
    line_mark: dict[str, Any],
    legend: dict[str, Any],
    view: dict[str, Any],
    color: str | None = None,
    y_format: str | None = None,
    x_sort: Any = None,
    x_tooltip_metric: str | None = None,
    x_tooltip_type: str | None = None,
) -> None:
    render_text_title(title, title_style)
    if chart_df.empty:
        st.caption("No chart data available.")
        return

    mark_kwargs = mapped_kwargs(line_mark, LINE_MARK_STYLE_KEYS)
    if color:
        mark_kwargs["color"] = color

    chart = (
        alt.Chart(chart_df)
        .mark_line(**mark_kwargs)
        .encode(
            x=alt.X(
                f"{x_axis_metric}:{x_axis_type}",
                title=x_axis_title,
                sort=x_sort if x_sort is not None else alt.Undefined,
                axis=altair_axis(x_axis, x_axis_bin_labels, x_axis_title_style),
            ),
            y=alt.Y(
                f"{y_axis_metric}:Q",
                title=y_axis_title,
                axis=altair_axis(
                    y_axis,
                    y_axis_bin_labels,
                    y_axis_title_style,
                    y_format,
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    f"{x_tooltip_metric or x_axis_metric}:{x_tooltip_type or x_axis_type}",
                    title=x_axis_title,
                ),
                y_tooltip(f"{y_axis_metric}:Q", y_axis_title, y_format),
            ],
        )
    )

    st.altair_chart(
        style_altair_chart(chart, legend=legend, view=view),
        use_container_width=True,
    )
