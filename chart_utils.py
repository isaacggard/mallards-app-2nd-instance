import altair as alt


ANGLED_LABEL_ANGLE = -28
X_AXIS_LABEL_FONT_SIZE = 12
X_AXIS_TITLE_FONT_SIZE = 12
Y_AXIS_LABEL_FONT_SIZE = 13
Y_AXIS_TITLE_FONT_SIZE = 14


def x_axis(label_angle: int = 0) -> alt.Axis:
    angle = ANGLED_LABEL_ANGLE if label_angle < 0 else label_angle
    kwargs = {
        "labelAngle": angle,
        "labelFontSize": X_AXIS_LABEL_FONT_SIZE,
        "titleFontSize": X_AXIS_TITLE_FONT_SIZE,
    }
    if angle:
        kwargs["labelLimit"] = 0
        kwargs["labelOverlap"] = False
    return alt.Axis(**kwargs)


def y_axis(y_format: str | None = None) -> alt.Axis:
    kwargs = {
        "labelFontSize": Y_AXIS_LABEL_FONT_SIZE,
        "titleFontSize": Y_AXIS_TITLE_FONT_SIZE,
    }
    if y_format:
        kwargs["format"] = y_format
    return alt.Axis(**kwargs)


def y_tooltip(column: str, title: str, y_format: str | None = None) -> alt.Tooltip:
    if y_format:
        return alt.Tooltip(column, title=title, format=y_format)
    return alt.Tooltip(column, title=title)
