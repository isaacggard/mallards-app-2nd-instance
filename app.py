import re
import sys
import time
from html import escape
from io import BytesIO
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st

from pages.render_components import render_metric_cards

SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".xlsm", ".xls", ".parquet"}
TRANSACTION_SOURCE_COLUMNS = [
    "Date",
    "Gross Sales",
    "Discounts",
    "Service Charges",
    "Partial Refunds",
    "Net Sales",
    "Card",
    "Cash",
    "Square Gift Card",
    "Other Tender",
    "Fees",
    "Total Collected",
    "Net Total",
    "Tax",
    "Tip",
    "Gift Card Sales",
    "Cash App",
    "Transaction ID",
    "Device Name",
    "Location",
    "Customer Name",
]
TICKET_SOURCE_COLUMNS = [
    "Row",
    "Seat Number",
    "Customer First",
    "Customer Last",
    "Customer Email",
    "Game Date",
    "Section",
    "Customer Phone",
    "Customer Company",
    "Customer Address",
    "Customer City",
    "Customer State",
    "Customer Zip Code",
    "Account Number",
    "Account Name",
    "Opponent",
    "Ticket Type",
    "Package Name",
    "Promo Name",
    "Scanned?",
    "Price",
    "Total",
]

DATA_TYPE_LABELS = {
    "transaction_data": "Transaction Data",
    "ticket_data": "Ticket Data",
    "survey_data": "Survey Data",
    "unknown": "Unknown",
}
SOURCE_FILE_COLUMN = "_source_file"
DATAFRAME_STATE_KEYS = {
    "transaction_data": "transaction_df",
    "ticket_data": "ticket_df",
    "survey_data": "survey_df",
    "unknown": "unknown_df",
}
LEGACY_DATA_LIST_KEYS = {
    "transaction_data": "transaction_data",
    "ticket_data": "ticket_data",
    "survey_data": "survey_data",
    "unknown": "unknown_data",
}
DATASET_TYPE_ALIASES = {
    "Transaction Data": "transaction_data",
    "Ticket Data": "ticket_data",
    "Survey Data": "survey_data",
    "Unknown": "unknown",
    "unknown_data": "unknown",
}
FAN_BEHAVIOR_METRIC_SCHEMA_VERSION = "fan_behavior_v6"
TRANSACTION_METRIC_SCHEMA_VERSION = "transaction_v9"
SURVEY_METRIC_SCHEMA_VERSION = "survey_v8"

APP_BRAND_TITLE = "Madison Mallards & Nightmares"


def _style_block(selector: str, style: dict[str, str]) -> str:
    rules = "\n".join(
        f"  {key.replace('_', '-')}: {value} !important;"
        for key, value in style.items()
    )
    return f"{selector} {{\n{rules}\n}}"


def _inline_style(style: dict[str, Any]) -> str:
    return "; ".join(
        f"{key.replace('_', '-')}: {value}"
        for key, value in style.items()
        if value is not None
    )


def app_style_css() -> str:
    caption_rules = {
        "font_size": "16px",
        "font_weight": "700",
        "color": "#000000",
        "font_family": "Georgia Bold",
        "line_height": "1.35",
    }
    sidebar_nav_selector = (
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] a, '
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] button, '
        '[data-testid="stSidebar"] nav a, '
        '[data-testid="stSidebar"] nav button, '
        '[data-testid="stSidebar"] [role="navigation"] a, '
        '[data-testid="stSidebar"] [role="navigation"] button, '
        '[data-testid="stSidebar"] [data-testid="stPageLink"] a'
    )
    sidebar_nav_child_selector = (
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] a *, '
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] button *, '
        '[data-testid="stSidebar"] nav a *, '
        '[data-testid="stSidebar"] nav button *, '
        '[data-testid="stSidebar"] [role="navigation"] a *, '
        '[data-testid="stSidebar"] [role="navigation"] button *, '
        '[data-testid="stSidebar"] [data-testid="stPageLink"] a *'
    )
    sidebar_nav_hover_selector = (
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover, '
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] button:hover, '
        '[data-testid="stSidebar"] nav a:hover, '
        '[data-testid="stSidebar"] nav button:hover, '
        '[data-testid="stSidebar"] [role="navigation"] a:hover, '
        '[data-testid="stSidebar"] [role="navigation"] button:hover, '
        '[data-testid="stSidebar"] [data-testid="stPageLink"] a:hover'
    )
    sidebar_nav_active_selector = (
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"], '
        '[data-testid="stSidebar"] [data-testid="stSidebarNav"] button[aria-current="page"], '
        '[data-testid="stSidebar"] nav a[aria-current="page"], '
        '[data-testid="stSidebar"] nav button[aria-current="page"], '
        '[data-testid="stSidebar"] [role="navigation"] a[aria-current="page"], '
        '[data-testid="stSidebar"] [role="navigation"] button[aria-current="page"], '
        '[data-testid="stSidebar"] [data-testid="stPageLink"] a[aria-current="page"], '
        '[data-testid="stSidebar"] a[aria-selected="true"], '
        '[data-testid="stSidebar"] button[aria-selected="true"]'
    )
    return "\n".join(
        [
            "<style>",
            _style_block(".stApp", {"background": "#FFFFFF"}),
            _style_block(
                '[data-testid="stAppViewContainer"]',
                {"background": "#FFFFFF"},
            ),
            _style_block(
                '[data-testid="stMain"]',
                {"background": "#FFFFFF"},
            ),
            _style_block(
                '[data-testid="stSidebar"]',
                {"background": "#AAAAAA"},
            ),
            _style_block(
                sidebar_nav_selector,
                {
                    "font_size": "16px",
                    "font_weight": "600",
                    "font_family": "Georgia Bold",
                    "color": "#000000",
                    "text_decoration": "none",
                },
            ),
            _style_block(
                sidebar_nav_child_selector,
                {
                    "font_size": "16px",
                    "font_weight": "600",
                    "font_family": "Georgia Bold",
                    "color": "inherit",
                },
            ),
            _style_block(
                sidebar_nav_hover_selector,
                {
                    "color": "#1c5b38",
                    "background": "rgba(28, 91, 56, 0.08)",
                },
            ),
            _style_block(
                sidebar_nav_active_selector,
                {
                    "color": "#1c5b38",
                    "background": "rgba(28, 91, 56, 0.10)",
                },
            ),
            _style_block(
                ".mallards-brand-title",
                {
                    "font_size": "42px",
                    "font_weight": "700",
                    "color": "#1c5b38",
                    "font_family": "Georgia Bold",
                    "margin_bottom": "-2rem",
                },
            ),
            _style_block(
                '[data-testid="stHeading"] h1',
                {
                    "font_size": "34px",
                    "font_weight": "750",
                    "color": "#000000",
                    "font_family": "Georgia Bold",
                    "line_height": "1.08",
                    "margin_bottom": "-1rem",
                },
            ),
            _style_block('[data-testid="stCaptionContainer"]', caption_rules),
            _style_block('[data-testid="stCaptionContainer"] *', caption_rules),
            "</style>",
        ]
    )


def apply_app_styles() -> None:
    st.markdown(app_style_css(), unsafe_allow_html=True)


def render_app_brand() -> None:
    apply_app_styles()
    st.markdown(
        f"<div class='mallards-brand-title'>{escape(APP_BRAND_TITLE)}</div>",
        unsafe_allow_html=True,
    )


def render_page_title(title: str) -> None:
    render_app_brand()
    st.title(title)


def render_header(text: str, style: dict[str, Any] | None = None) -> None:
    header_style = style or {
        "font_size": "30px",
        "font_weight": "700",
        "color": "#000000",
        "font_family": "Georgia Bold",
        "line_height": "1.18",
        "margin_top": "1rem",
        "margin_bottom": "0.45rem",
    }
    st.markdown(
        f"<div style='{_inline_style(header_style)}'>{escape(text)}</div>",
        unsafe_allow_html=True,
    )


def render_subheader(text: str, style: dict[str, Any] | None = None) -> None:
    subheader_style = style or {
        "font_size": "24px",
        "font_weight": "650",
        "color": "#000000",
        "font_family": "Georgia Bold",
        "line_height": "1.2",
        "margin_top": "0.75rem",
        "margin_bottom": "0.35rem",
    }
    st.markdown(
        f"<div style='{_inline_style(subheader_style)}'>{escape(text)}</div>",
        unsafe_allow_html=True,
    )


def render_divider(style: dict[str, Any] | None = None) -> None:
    divider_style = style or {
        "color": "#000000",
        "height": "2px",
        "padding_top": "1rem",
        "padding_bottom": "0.5rem",
        "margin_left": "0",
        "margin_right": "0",
    }
    wrapper_style = {
        "padding_top": divider_style["padding_top"],
        "padding_bottom": divider_style["padding_bottom"],
        "margin_left": divider_style["margin_left"],
        "margin_right": divider_style["margin_right"],
    }
    line_style = {
        "border": "0",
        "border_top": f"{divider_style['height']} solid {divider_style['color']}",
        "margin": "0",
    }
    st.markdown(
        (
            f"<div style='{_inline_style(wrapper_style)}'>"
            f"<hr style='{_inline_style(line_style)}'>"
            "</div>"
        ),
        unsafe_allow_html=True,
    )


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


def select_source_columns(
    file_name: str,
    source_columns: list[Any],
) -> list[str] | None:
    normalized_file_name = Path(file_name).name.lower()
    if is_survey_file_name(normalized_file_name):
        return None

    normalized_lookup = {
        normalize_column_name(column): column for column in source_columns
    }
    normalized_columns = set(normalized_lookup)

    transaction_columns = {"transaction id", "square gift card", "gross sales"}
    if transaction_columns.issubset(normalized_columns):
        selected = [
            normalized_lookup[normalize_column_name(column)]
            for column in TRANSACTION_SOURCE_COLUMNS
            if normalize_column_name(column) in normalized_lookup
        ]
        return selected or None

    ticket_columns = {"row", "seat number", "ticket type"}
    if ticket_columns.issubset(normalized_columns):
        selected = [
            normalized_lookup[normalize_column_name(column)]
            for column in TICKET_SOURCE_COLUMNS
            if normalize_column_name(column) in normalized_lookup
        ]
        return selected or None

    return None


def require_column(df: pd.DataFrame, column_name: str) -> str:
    column = find_column(df, [column_name])
    if not column:
        raise ValueError(f"Missing required column: {column_name}")
    return column


def maybe_column(df: pd.DataFrame, column_name: str) -> str | None:
    return find_column(df, [column_name])


def optional_series(
    df: pd.DataFrame,
    column_name: str,
    default: Any = pd.NA,
) -> pd.Series:
    column = maybe_column(df, column_name)
    if column:
        return df[column]
    return pd.Series(default, index=df.index)


def file_source_to_buffer(file_source: Any) -> Any:
    if isinstance(file_source, (bytes, bytearray, memoryview)):
        return BytesIO(file_source)
    if hasattr(file_source, "seek"):
        file_source.seek(0)
    return file_source


def read_dataset(file_name: str, file_source: Any) -> pd.DataFrame:
    extension = Path(file_name).suffix.lower()
    file_buffer = file_source_to_buffer(file_source)

    if extension == ".csv":
        header = pd.read_csv(file_buffer, nrows=0).columns.tolist()
        usecols = select_source_columns(file_name, header)
        file_buffer = file_source_to_buffer(file_source)
        return pd.read_csv(file_buffer, low_memory=False, usecols=usecols)

    if extension in {".xlsx", ".xlsm", ".xls"}:
        excel_file = pd.ExcelFile(file_buffer)
        header = excel_file.parse(sheet_name=0, nrows=0).columns.tolist()
        usecols = select_source_columns(file_name, header)
        return excel_file.parse(sheet_name=0, usecols=usecols)

    if extension == ".parquet":
        return pd.read_parquet(file_buffer)

    raise ValueError("Invalid file format")


def classify_survey_filename(file_name: str) -> str:
    file_name_lower = file_name.lower()
    exact_postgame = "postgame" in file_name_lower
    exact_postseason = "postseason" in file_name_lower

    if exact_postgame:
        return "postgame"
    if exact_postseason:
        return "postseason"
    if "post" in file_name_lower and "game" in file_name_lower:
        return "postgame"
    if "post" in file_name_lower and "season" in file_name_lower:
        return "postseason"
    return "unknown_survey"


def extract_survey_year(file_name: str) -> int | None:
    match = re.search(r"(20\d{2})", file_name)
    return int(match.group(1)) if match else None


def extract_survey_team(file_name: str) -> str:
    file_name_lower = file_name.lower()
    if (
        "night mares" in file_name_lower
        or "nightmares" in file_name_lower
        or "nm" in file_name_lower
    ):
        return "Night Mares"
    if "mallard" in file_name_lower:
        return "Mallards"
    return "Unknown"


def is_survey_file_name(file_name: str) -> bool:
    file_name_lower = file_name.lower()
    return (
        "survey" in file_name_lower
        or "postgame" in file_name_lower
        or "postseason" in file_name_lower
        or ("post" in file_name_lower and "game" in file_name_lower)
        or ("post" in file_name_lower and "season" in file_name_lower)
    )


def add_survey_metadata(
    df: pd.DataFrame,
    file_name: str,
    sheet_name: str,
) -> pd.DataFrame:
    enriched_df = df.copy()
    enriched_df["_source_file"] = file_name
    enriched_df["_source_sheet"] = sheet_name
    enriched_df["survey_type"] = classify_survey_filename(file_name)
    enriched_df["survey_year"] = extract_survey_year(file_name)
    enriched_df["team"] = extract_survey_team(file_name)
    return enriched_df


def read_survey_dataset(file_name: str, file_source: Any) -> pd.DataFrame:
    extension = Path(file_name).suffix.lower()
    file_buffer = file_source_to_buffer(file_source)

    if extension == ".csv":
        df = pd.read_csv(file_buffer, low_memory=False)
        return add_survey_metadata(df, file_name, "CSV")

    if extension in {".xlsx", ".xlsm", ".xls"}:
        excel_file = pd.ExcelFile(file_buffer)
        frames = []
        for sheet_name in excel_file.sheet_names:
            sheet_name_text = str(sheet_name)
            sheet_name_lower = sheet_name_text.lower().strip()
            if "summary" in sheet_name_lower or "average" in sheet_name_lower:
                continue

            sheet_df = excel_file.parse(sheet_name)
            if sheet_df.empty:
                continue

            sheet_df.columns = [str(column).strip() for column in sheet_df.columns]
            frames.append(add_survey_metadata(sheet_df, file_name, sheet_name_text))

        if frames:
            return pd.concat(frames, ignore_index=True, sort=False)
        return pd.DataFrame()

    return read_dataset(file_name, file_source)


def classify_dataset(df: pd.DataFrame, file_name: str) -> str:
    normalized_file_name = Path(file_name).name.lower()
    columns = {normalize_column_name(column) for column in df.columns}

    if is_survey_file_name(normalized_file_name):
        return "survey_data"

    transaction_columns = {"transaction id", "square gift card", "gross sales"}
    if transaction_columns.issubset(columns):
        return "transaction_data"

    ticket_columns = {"row", "seat number", "ticket type"}
    if ticket_columns.issubset(columns):
        return "ticket_data"

    return "unknown"


def add_source_file_column(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    if SOURCE_FILE_COLUMN in df.columns:
        df[SOURCE_FILE_COLUMN] = (
            df[SOURCE_FILE_COLUMN].astype("string").fillna(file_name)
        )
        return df

    df.insert(0, SOURCE_FILE_COLUMN, file_name)
    return df


def optimize_dataframe_for_session(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    row_count = len(df)
    category_limit = min(1_000, max(1, row_count // 4))
    for column in df.columns:
        series = df[column]
        if pd.api.types.is_integer_dtype(series):
            df[column] = pd.to_numeric(series, downcast="integer")
            continue
        if pd.api.types.is_float_dtype(series):
            df[column] = pd.to_numeric(series, downcast="float")
            continue
        if (
            pd.api.types.is_object_dtype(series)
            or pd.api.types.is_string_dtype(series)
        ):
            unique_count = series.nunique(dropna=True)
            if 0 < unique_count <= category_limit:
                df[column] = series.astype("category")
    return df


def normalize_dataset_type(dataset_type: Any) -> str:
    if dataset_type is None:
        return "unknown"
    try:
        if pd.isna(dataset_type):
            return "unknown"
    except (TypeError, ValueError):
        pass

    dataset_type_text = str(dataset_type).strip()
    return DATASET_TYPE_ALIASES.get(dataset_type_text, dataset_type_text) or "unknown"


def record_file_name(record: dict[str, Any]) -> str:
    return (
        record.get("file")
        or record.get("File")
        or record.get("name")
        or "Uploaded file"
    )


def record_dataset_type(record: dict[str, Any]) -> str:
    return normalize_dataset_type(
        record.get("dataset_type")
        or record.get("detected_type")
        or record.get("Detected Type")
        or "unknown"
    )


def record_int(record: dict[str, Any], *keys: str) -> int:
    for key in keys:
        if key in record:
            return int(record.get(key) or 0)
    return 0


def loaded_file_count(dataset_type: str) -> int:
    normalized_dataset_type = normalize_dataset_type(dataset_type)
    return sum(
        1
        for record in st.session_state.get("loaded_dataset_records", [])
        if isinstance(record, dict)
        and record_dataset_type(record) == normalized_dataset_type
    )


def append_dataframes_to_state(
    dataframes_by_type: dict[str, list[pd.DataFrame]],
) -> None:
    for dataset_type, frames in dataframes_by_type.items():
        if not frames:
            continue

        state_key = DATAFRAME_STATE_KEYS.get(dataset_type)
        if not state_key:
            continue

        existing_df = st.session_state.get(state_key, pd.DataFrame())
        new_df = pd.concat(frames, ignore_index=True, sort=False)
        if existing_df.empty:
            st.session_state[state_key] = optimize_dataframe_for_session(new_df)
        else:
            combined_df = pd.concat(
                [existing_df, new_df],
                ignore_index=True,
                sort=False,
            )
            st.session_state[state_key] = optimize_dataframe_for_session(combined_df)


def remove_source_file_from_state(file_name: str) -> None:
    for state_key in DATAFRAME_STATE_KEYS.values():
        df = st.session_state.get(state_key, pd.DataFrame())
        if df.empty or SOURCE_FILE_COLUMN not in df.columns:
            continue
        filtered_df = df[
            ~df[SOURCE_FILE_COLUMN].astype("string").eq(file_name)
        ].reset_index(drop=True)
        st.session_state[state_key] = optimize_dataframe_for_session(filtered_df)


def to_numeric_preserve_index(series: pd.Series) -> pd.Series:
    cleaned_series = (
        series.astype(str)
        .str.replace(r"[\$, ]", "", regex=True)
        .replace(["-", "", "None", "nan", "null", "<NA>"], "0")
    )
    return pd.to_numeric(cleaned_series, errors="coerce").fillna(0.0)


def clean_text_series(series: pd.Series) -> pd.Series:
    return (
        series.astype("string")
        .str.strip()
        .str.lower()
        .str.replace(r"\s+", " ", regex=True)
        .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "<na>": pd.NA})
    )


def most_common_by_group(
    df: pd.DataFrame,
    group_column: str,
    value_column: str,
    output_column: str,
) -> pd.DataFrame:
    if value_column not in df.columns:
        return pd.DataFrame(columns=[group_column, output_column])

    values = df[[group_column, value_column]].dropna()
    if values.empty:
        return pd.DataFrame(columns=[group_column, output_column])

    values[value_column] = (
        values[value_column]
        .astype("string")
        .str.strip()
        .replace({"": pd.NA, "nan": pd.NA, "none": pd.NA, "<na>": pd.NA})
    )
    values = values.dropna(subset=[value_column])
    if values.empty:
        return pd.DataFrame(columns=[group_column, output_column])

    counts = (
        values.groupby([group_column, value_column], as_index=False, observed=True)
        .size()
        .sort_values(
            [group_column, "size", value_column],
            ascending=[True, False, True],
        )
    )
    return (
        counts.drop_duplicates(group_column)[[group_column, value_column]]
        .rename(columns={value_column: output_column})
    )


def clean_email_series(series: pd.Series) -> pd.Series:
    return clean_text_series(series)


def clean_name_key_series(first_name: pd.Series, last_name: pd.Series) -> pd.Series:
    name_key = (
        first_name.fillna("").astype("string")
        + last_name.fillna("").astype("string")
    )
    name_key = (
        name_key.str.lower()
        .str.replace(r"[^a-z0-9]", "", regex=True)
        .str.strip()
        .replace("", pd.NA)
    )
    return name_key


def split_merch_customer_name(customer_name: pd.Series) -> tuple[pd.Series, pd.Series]:
    customer_name = customer_name.astype("string").str.strip()
    valid_customer_name = customer_name.mask(
        customer_name.str.lower().isin(["", "nan", "none", "<na>"]),
        pd.NA,
    )
    email_mask = valid_customer_name.str.match(
        r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$",
        na=False,
    )
    merch_email = valid_customer_name.where(email_mask).str.lower()
    merch_name = (
        valid_customer_name.where(~email_mask)
        .str.lower()
        .str.replace(r"[^a-z0-9]", "", regex=True)
        .replace("", pd.NA)
    )
    return merch_email, merch_name


def normalize_ticket_data(df: pd.DataFrame) -> pd.DataFrame:
    first_column = require_column(df, "Customer First")
    last_column = require_column(df, "Customer Last")
    email_column = require_column(df, "Customer Email")
    game_date_column = require_column(df, "Game Date")
    section_column = find_column(df, ["Section"])
    section_series = (
        df[section_column] if section_column else optional_series(df, "Row")
    )

    scanned_series = optional_series(df, "Scanned?")
    normalized_df = pd.DataFrame(
        {
            "fan_key": pd.NA,
            "email": clean_email_series(df[email_column]),
            "first_name": df[first_column].replace(
                {"None": None, "nan": None, "": None}
            ),
            "last_name": df[last_column].replace(
                {"None": None, "nan": None, "": None}
            ),
            "t_name_key": clean_name_key_series(df[first_column], df[last_column]),
            "phone": optional_series(df, "Customer Phone"),
            "company": optional_series(df, "Customer Company"),
            "address": optional_series(df, "Customer Address"),
            "city": optional_series(df, "Customer City"),
            "state": optional_series(df, "Customer State"),
            "zip": optional_series(df, "Customer Zip Code"),
            "account_number": optional_series(df, "Account Number"),
            "account_name": optional_series(df, "Account Name"),
            "game_date": pd.to_datetime(df[game_date_column], errors="coerce"),
            "opponent": optional_series(df, "Opponent"),
            "section": section_series,
            "ticket_type": optional_series(df, "Ticket Type"),
            "package": optional_series(df, "Package Name"),
            "promo": optional_series(df, "Promo Name"),
            "scanned": scanned_series,
            "scanned_flag": clean_text_series(scanned_series).eq("y").astype(int),
            "price": to_numeric_preserve_index(optional_series(df, "Price", 0.0)),
            "total": to_numeric_preserve_index(optional_series(df, "Total", 0.0)),
        }
    )
    normalized_df["fan_key"] = normalized_df["email"].combine_first(
        normalized_df["t_name_key"]
    )
    return normalized_df[normalized_df["fan_key"].notna()]


def aggregate_ticket_fans(ticket_df: pd.DataFrame) -> pd.DataFrame:
    normalized_tickets = normalize_ticket_data(ticket_df)
    if normalized_tickets.empty:
        return pd.DataFrame()

    fan_agg = (
        normalized_tickets.groupby("fan_key", as_index=False)
        .agg(
            first_name=("first_name", "first"),
            last_name=("last_name", "first"),
            email=("email", "first"),
            phone=("phone", "first"),
            company=("company", "first"),
            address=("address", "first"),
            city=("city", "first"),
            state=("state", "first"),
            zip=("zip", "first"),
            account_number=("account_number", "first"),
            account_name=("account_name", "first"),
            total_tickets=("price", "count"),
            total_ticket_spend=("price", "sum"),
            total_ticket_paid=("total", "sum"),
            games_attended=("game_date", "nunique"),
            first_game=("game_date", "min"),
            last_game=("game_date", "max"),
            opponents_seen=("opponent", "first"),
            package=("package", "first"),
            promo=("promo", "first"),
            tickets_scanned=("scanned_flag", "sum"),
            t_name_key=("t_name_key", "first"),
        )
    )
    section_mode = most_common_by_group(
        normalized_tickets,
        "fan_key",
        "section",
        "most_common_section",
    )
    ticket_type_mode = most_common_by_group(
        normalized_tickets,
        "fan_key",
        "ticket_type",
        "ticket_type",
    )
    fan_agg = fan_agg.merge(section_mode, on="fan_key", how="left")
    fan_agg = fan_agg.merge(ticket_type_mode, on="fan_key", how="left")
    fan_agg["scan_rate"] = (
        fan_agg["tickets_scanned"] / fan_agg["total_tickets"]
    ).round(3)
    return fan_agg


def normalize_transaction_data(df: pd.DataFrame) -> pd.DataFrame:
    customer_name_column = require_column(df, "Customer Name")
    date_column = require_column(df, "Date")
    merch_email, merch_join_name = split_merch_customer_name(
        df[customer_name_column]
    )

    normalized_df = pd.DataFrame(
        {
            "merch_email": merch_email,
            "merch_join_name": merch_join_name,
            "date": pd.to_datetime(df[date_column], errors="coerce"),
        }
    )

    money_columns = [
        "Gross Sales",
        "Discounts",
        "Service Charges",
        "Partial Refunds",
        "Net Sales",
        "Card",
        "Cash",
        "Square Gift Card",
        "Other Tender",
        "Fees",
        "Total Collected",
        "Net Total",
        "Tax",
        "Tip",
        "Gift Card Sales",
        "Cash App",
    ]
    for column in money_columns:
        source_column = maybe_column(df, column)
        if source_column:
            normalized_df[column] = to_numeric_preserve_index(df[source_column])

    return normalized_df


def aggregate_merch_by_key(
    merch_df: pd.DataFrame,
    key_column: str,
) -> pd.DataFrame:
    merch_keyed = merch_df[merch_df[key_column].notna()]
    if merch_keyed.empty:
        return pd.DataFrame(columns=["join_key"])

    money_columns = [
        column
        for column in [
            "Gross Sales",
            "Discounts",
            "Service Charges",
            "Partial Refunds",
            "Net Sales",
            "Card",
            "Cash",
            "Square Gift Card",
            "Other Tender",
            "Fees",
            "Total Collected",
            "Net Total",
            "Tax",
            "Tip",
            "Gift Card Sales",
            "Cash App",
        ]
        if column in merch_keyed.columns
    ]

    agg_spec = {
        column: (column, "sum")
        for column in money_columns
    }
    agg_spec.update(
        {
            "merch_total_transactions": (key_column, "size"),
            "merch_first_purchase": ("date", "min"),
            "merch_last_purchase": ("date", "max"),
        }
    )
    merch_agg = merch_keyed.groupby(key_column, as_index=False).agg(**agg_spec)

    rename_map = {
        column: f"merch_{column.lower().replace(' ', '_')}"
        for column in money_columns
    }
    rename_map[key_column] = "join_key"
    return merch_agg.rename(columns=rename_map)


def build_fan_master_dataframe(
    ticket_df: pd.DataFrame,
    transaction_df: pd.DataFrame,
) -> pd.DataFrame:
    start_time = time.time()
    fan_agg = aggregate_ticket_fans(ticket_df)
    if fan_agg.empty:
        print(f"Fan master build time: {time.time() - start_time:.2f}s")
        return fan_agg

    merch_df = normalize_transaction_data(transaction_df)
    merch_by_email = aggregate_merch_by_key(merch_df, "merch_email")
    merch_by_name = aggregate_merch_by_key(merch_df, "merch_join_name")

    pass1 = fan_agg.assign(join_key=fan_agg["email"]).merge(
        merch_by_email,
        on="join_key",
        how="left",
        indicator="_merge_p1",
    )
    matched_p1 = pass1["_merge_p1"].eq("both")
    pass1 = pass1.drop(columns=["_merge_p1"])
    pass1.loc[matched_p1, "match_method"] = "email"

    merch_columns = [column for column in merch_by_email.columns if column != "join_key"]
    unmatched = pass1.loc[~matched_p1].drop(
        columns=merch_columns,
        errors="ignore",
    )
    pass2 = unmatched.assign(join_key=unmatched["t_name_key"]).merge(
        merch_by_name,
        on="join_key",
        how="left",
    )
    merch_net_total = pass2.get("merch_net_total", pd.Series(index=pass2.index))
    matched_p2 = merch_net_total.notna()
    pass2.loc[matched_p2, "match_method"] = "name"
    pass2.loc[~matched_p2, "match_method"] = "unmatched"

    fan_master = pd.concat(
        [pass1.loc[matched_p1], pass2],
        ignore_index=True,
    ).drop(columns=["join_key"], errors="ignore")
    fan_master["match_priority"] = fan_master["match_method"].map(
        {"email": 1, "name": 2, "unmatched": 3}
    )
    fan_master = (
        fan_master.sort_values("match_priority")
        .drop_duplicates("fan_key")
        .drop(columns=["match_priority"])
        .reset_index(drop=True)
    )

    merch_money_columns = [
        column
        for column in fan_master.columns
        if column.startswith("merch_")
        and pd.api.types.is_numeric_dtype(fan_master[column])
    ]
    fan_master[merch_money_columns] = fan_master[merch_money_columns].fillna(0)
    if "merch_total_transactions" in fan_master.columns:
        fan_master["merch_total_transactions"] = (
            fan_master["merch_total_transactions"].fillna(0).astype(int)
        )
    if "merch_net_total" in fan_master.columns:
        fan_master["is_merch_buyer"] = (
            fan_master["merch_net_total"].fillna(0).gt(0).astype(int)
        )
    else:
        fan_master["is_merch_buyer"] = 0

    print(f"Fan master build time: {time.time() - start_time:.2f}s")
    return fan_master


def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def empty_detection_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=["file", "detected_type", "status"])


def default_metrics_dirty() -> dict[str, bool]:
    return {
        "fan_behavior": True,
        "transaction": True,
        "survey": True,
        "ticket": True,
    }


def ensure_metric_state_initialized() -> None:
    if "fan_behavior_metrics" not in st.session_state:
        st.session_state.fan_behavior_metrics = None
    if "transaction_metrics" not in st.session_state:
        st.session_state.transaction_metrics = None
    if "survey_metrics" not in st.session_state:
        st.session_state.survey_metrics = None
    if "ticket_metrics" not in st.session_state:
        st.session_state.ticket_metrics = None

    if "metrics_dirty" not in st.session_state or not isinstance(
        st.session_state.metrics_dirty,
        dict,
    ):
        st.session_state.metrics_dirty = default_metrics_dirty()
        return

    for key, value in default_metrics_dirty().items():
        st.session_state.metrics_dirty.setdefault(key, value)


def migrate_legacy_session_storage() -> None:
    records = st.session_state.get("loaded_dataset_records", [])
    if not records:
        for dataset_type, list_key in LEGACY_DATA_LIST_KEYS.items():
            for index, frame in enumerate(st.session_state.get(list_key, []), 1):
                records.append(
                    {
                        "file": (
                            f"Existing "
                            f"{DATA_TYPE_LABELS.get(dataset_type, 'Unknown')} "
                            f"{index}"
                        ),
                        "dataset_type": dataset_type,
                        "data": frame,
                    }
                )

    normalized_records = []
    legacy_frames_by_type = {
        dataset_type: [] for dataset_type in DATAFRAME_STATE_KEYS
    }

    for record in records:
        if not isinstance(record, dict):
            continue

        file_name = record_file_name(record)
        dataset_type = record_dataset_type(record)
        data = record.get("data")

        if isinstance(data, pd.DataFrame):
            add_source_file_column(data, file_name)
            legacy_frames_by_type.setdefault(dataset_type, []).append(data)
            row_count = len(data)
            column_count = len(data.columns)
        else:
            row_count = record_int(record, "rows", "Rows")
            column_count = record_int(record, "columns", "Columns")

        normalized_records.append(
            {
                "file": file_name,
                "dataset_type": dataset_type,
                "rows": row_count,
                "columns": column_count,
            }
        )

    for dataset_type, frames in legacy_frames_by_type.items():
        state_key = DATAFRAME_STATE_KEYS.get(dataset_type)
        if not state_key or not frames:
            continue
        if st.session_state.get(state_key, pd.DataFrame()).empty:
            migrated_df = pd.concat(
                frames,
                ignore_index=True,
                sort=False,
            )
            st.session_state[state_key] = optimize_dataframe_for_session(migrated_df)

    st.session_state.loaded_dataset_records = normalized_records
    st.session_state.loaded_files = {
        record_file_name(record)
        for record in normalized_records
        if isinstance(record, dict)
    }
    for list_key in LEGACY_DATA_LIST_KEYS.values():
        st.session_state[list_key] = []


def initialize_session_state() -> None:
    if "loaded_files" not in st.session_state:
        st.session_state.loaded_files = set()
    if "last_upload_batch" not in st.session_state:
        st.session_state.last_upload_batch = tuple()
    if "upload_widget_version" not in st.session_state:
        st.session_state.upload_widget_version = 0
    if "detected_files" not in st.session_state:
        st.session_state.detected_files = empty_detection_frame()
    if "loaded_dataset_records" not in st.session_state:
        st.session_state.loaded_dataset_records = []

    if "transaction_df" not in st.session_state:
        st.session_state.transaction_df = pd.DataFrame()
    if "ticket_df" not in st.session_state:
        st.session_state.ticket_df = pd.DataFrame()
    if "survey_df" not in st.session_state:
        st.session_state.survey_df = pd.DataFrame()
    if "unknown_df" not in st.session_state:
        st.session_state.unknown_df = pd.DataFrame()

    migrate_legacy_session_storage()

    if "message" not in st.session_state:
        st.session_state.message = "Please upload one or more files"
    if "full_fan_master" not in st.session_state:
        st.session_state.full_fan_master = None
    if "fan_master_rows" not in st.session_state:
        st.session_state.fan_master_rows = 0
    if "fan_master_match_rate" not in st.session_state:
        st.session_state.fan_master_match_rate = "0.00%"
    if "fan_master_message" not in st.session_state:
        st.session_state.fan_master_message = (
            "Build the dashboard after loading ticket and transaction data"
        )
    ensure_metric_state_initialized()


def invalidate_all_metrics() -> None:
    ensure_metric_state_initialized()
    st.session_state.fan_behavior_metrics = None
    st.session_state.transaction_metrics = None
    st.session_state.survey_metrics = None
    st.session_state.ticket_metrics = None
    st.session_state.metrics_dirty = default_metrics_dirty()
    clear_metric_cache("prepare_fan_behavior_metrics")
    clear_metric_cache("prepare_transaction_insights_metrics")
    clear_metric_cache("prepare_survey_analysis_metrics")


def clear_metric_cache(function_name: str) -> None:
    metrics_module = sys.modules.get("metrics")
    if metrics_module is None:
        return

    cached_function = getattr(metrics_module, function_name, None)
    if hasattr(cached_function, "clear"):
        cached_function.clear()


def invalidate_transaction_metrics() -> None:
    ensure_metric_state_initialized()
    st.session_state.transaction_metrics = None
    st.session_state.fan_behavior_metrics = None
    st.session_state.metrics_dirty["transaction"] = True
    st.session_state.metrics_dirty["fan_behavior"] = True
    clear_metric_cache("prepare_transaction_insights_metrics")
    clear_metric_cache("prepare_fan_behavior_metrics")


def invalidate_ticket_metrics() -> None:
    ensure_metric_state_initialized()
    st.session_state.ticket_metrics = None
    st.session_state.fan_behavior_metrics = None
    st.session_state.metrics_dirty["ticket"] = True
    st.session_state.metrics_dirty["fan_behavior"] = True
    clear_metric_cache("prepare_fan_behavior_metrics")


def invalidate_survey_metrics() -> None:
    ensure_metric_state_initialized()
    st.session_state.survey_metrics = None
    st.session_state.metrics_dirty["survey"] = True
    clear_metric_cache("prepare_survey_analysis_metrics")


def invalidate_fan_behavior_metrics() -> None:
    ensure_metric_state_initialized()
    st.session_state.fan_behavior_metrics = None
    st.session_state.metrics_dirty["fan_behavior"] = True
    clear_metric_cache("prepare_fan_behavior_metrics")


def ensure_transaction_metrics() -> dict:
    ensure_metric_state_initialized()
    if st.session_state.transaction_df.empty:
        return {}

    metric_schema_version = (
        st.session_state.transaction_metrics
        or {}
    ).get("metadata", {}).get("schema_version")
    if (
        st.session_state.transaction_metrics is None
        or st.session_state.metrics_dirty.get("transaction", True)
        or metric_schema_version != TRANSACTION_METRIC_SCHEMA_VERSION
    ):
        from metrics import prepare_transaction_insights_metrics

        st.session_state.transaction_metrics = prepare_transaction_insights_metrics(
            st.session_state.transaction_df
        )
        st.session_state.metrics_dirty["transaction"] = False

    return st.session_state.transaction_metrics


def ensure_fan_behavior_metrics() -> dict:
    ensure_metric_state_initialized()
    fan_master = st.session_state.get("full_fan_master")
    if fan_master is None or fan_master.empty:
        return {}

    metric_schema_version = (
        st.session_state.fan_behavior_metrics
        or {}
    ).get("metadata", {}).get("schema_version")
    if (
        st.session_state.fan_behavior_metrics is None
        or st.session_state.metrics_dirty.get("fan_behavior", True)
        or metric_schema_version != FAN_BEHAVIOR_METRIC_SCHEMA_VERSION
    ):
        from metrics import prepare_fan_behavior_metrics

        st.session_state.fan_behavior_metrics = prepare_fan_behavior_metrics(
            fan_master
        )
        st.session_state.metrics_dirty["fan_behavior"] = False

    return st.session_state.fan_behavior_metrics


def ensure_survey_metrics() -> dict:
    ensure_metric_state_initialized()
    if st.session_state.survey_df.empty:
        return {}

    metric_schema_version = (
        st.session_state.survey_metrics
        or {}
    ).get("metadata", {}).get("schema_version")
    if (
        st.session_state.survey_metrics is None
        or st.session_state.metrics_dirty.get("survey", True)
        or metric_schema_version != SURVEY_METRIC_SCHEMA_VERSION
    ):
        from metrics import prepare_survey_analysis_metrics

        st.session_state.survey_metrics = prepare_survey_analysis_metrics(
            st.session_state.survey_df
        )
        st.session_state.metrics_dirty["survey"] = False

    return st.session_state.survey_metrics


def ensure_ticket_metrics() -> dict:
    ensure_metric_state_initialized()
    if st.session_state.ticket_df.empty:
        return {}

    if (
        st.session_state.ticket_metrics is None
        or st.session_state.metrics_dirty.get("ticket", True)
    ):
        st.session_state.ticket_metrics = {
            "kpis": {
                "ticket_rows": len(st.session_state.ticket_df),
                "ticket_files": loaded_file_count("ticket_data"),
            },
            "charts": {},
            "metadata": {
                "built_at": time.time(),
                "source_rows": len(st.session_state.ticket_df),
            },
        }
        st.session_state.metrics_dirty["ticket"] = False

    return st.session_state.ticket_metrics


def reset_fan_master_state(status_message: str) -> None:
    st.session_state.full_fan_master = None
    st.session_state.fan_master_rows = 0
    st.session_state.fan_master_match_rate = "0.00%"
    st.session_state.fan_master_message = status_message
    invalidate_fan_behavior_metrics()


def add_loaded_dataset_record(
    file_name: str,
    dataset_type: str,
    row_count: int,
    column_count: int,
) -> None:
    st.session_state.loaded_dataset_records.append(
        {
            "file": file_name,
            "dataset_type": normalize_dataset_type(dataset_type),
            "rows": row_count,
            "columns": column_count,
        }
    )
    st.session_state.loaded_files.add(file_name)


def invalidate_metrics_for_dataset_type(dataset_type: str) -> None:
    if dataset_type == "transaction_data":
        invalidate_transaction_metrics()
        return
    if dataset_type == "ticket_data":
        invalidate_ticket_metrics()
        return
    if dataset_type == "survey_data":
        invalidate_survey_metrics()


def loaded_files_frame() -> pd.DataFrame:
    rows = []
    for record in st.session_state.loaded_dataset_records:
        if not isinstance(record, dict):
            continue

        dataset_type = record_dataset_type(record)
        file_name = record_file_name(record)
        rows.append(
            {
                "File": file_name,
                "Detected Type": DATA_TYPE_LABELS.get(dataset_type, "Unknown"),
                "Rows": record_int(record, "rows", "Rows"),
                "Columns": record_int(record, "columns", "Columns"),
            }
        )

    return pd.DataFrame(rows, columns=["File", "Detected Type", "Rows", "Columns"])


def remove_loaded_file(file_name: str) -> None:
    records = st.session_state.loaded_dataset_records
    removed_records = [
        record
        for record in records
        if isinstance(record, dict)
        and record_file_name(record) == file_name
    ]
    if not removed_records:
        st.session_state.message = "Select a loaded file to remove"
        return

    removed_types = {
        record_dataset_type(record)
        for record in removed_records
    }
    st.session_state.loaded_dataset_records = [
        record
        for record in records
        if not isinstance(record, dict)
        or record_file_name(record) != file_name
    ]
    st.session_state.loaded_files = {
        record_file_name(record)
        for record in st.session_state.loaded_dataset_records
        if isinstance(record, dict)
    }
    remove_source_file_from_state(file_name)

    for dataset_type in removed_types:
        invalidate_metrics_for_dataset_type(dataset_type)

    if {"transaction_data", "ticket_data"} & removed_types:
        reset_fan_master_state("Data removed. Build the dashboard to refresh results")

    append_detection_rows(
        [
            {
                "file": file_name,
                "detected_type": "Removed",
                "status": "Removed from session",
            }
        ]
    )
    st.session_state.message = f"Removed {file_name}"


def append_detection_rows(rows: list[dict[str, str]]) -> None:
    if not rows:
        return

    rows_df = pd.DataFrame(rows)
    if st.session_state.detected_files.empty:
        st.session_state.detected_files = rows_df
        return

    st.session_state.detected_files = pd.concat(
        [st.session_state.detected_files, rows_df],
        ignore_index=True,
    )


def process_uploaded_files(uploaded_files: list[Any]) -> bool:
    if not uploaded_files:
        st.session_state.message = "Please upload one or more files"
        return False

    detection_rows = []
    loaded_dataframes_by_type = {
        dataset_type: [] for dataset_type in DATAFRAME_STATE_KEYS
    }
    loaded_any_file = False
    duplicate_found = False
    fan_master_input_changed = False

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        extension = Path(file_name).suffix.lower()

        if file_name in st.session_state.loaded_files:
            duplicate_found = True
            detection_rows.append(
                {
                    "file": file_name,
                    "detected_type": "Duplicate",
                    "status": "Already loaded",
                }
            )
            continue

        if extension not in SUPPORTED_EXTENSIONS:
            detection_rows.append(
                {
                    "file": file_name,
                    "detected_type": "Unsupported",
                    "status": "Invalid file format",
                }
            )
            continue

        file_size = getattr(uploaded_file, "size", None)
        if file_size is not None and file_size == 0:
            detection_rows.append(
                {
                    "file": file_name,
                    "detected_type": "Empty",
                    "status": "Empty dataset",
                }
            )
            continue

        try:
            if is_survey_file_name(file_name):
                loaded_data = read_survey_dataset(file_name, uploaded_file)
            else:
                loaded_data = read_dataset(file_name, uploaded_file)
        except pd.errors.EmptyDataError:
            detection_rows.append(
                {
                    "file": file_name,
                    "detected_type": "Empty",
                    "status": "Empty dataset",
                }
            )
            continue
        except Exception as error:
            print(f"Unable to read {file_name}: {error}")
            detection_rows.append(
                {
                    "file": file_name,
                    "detected_type": "Unreadable",
                    "status": "Unable to read file",
                }
            )
            continue

        if loaded_data.empty:
            detection_rows.append(
                {
                    "file": file_name,
                    "detected_type": "Empty",
                    "status": "Empty dataset",
                }
            )
            continue

        detected_type = normalize_dataset_type(classify_dataset(loaded_data, file_name))
        add_source_file_column(loaded_data, file_name)
        if detected_type == "transaction_data":
            invalidate_transaction_metrics()
            fan_master_input_changed = True
        elif detected_type == "ticket_data":
            invalidate_ticket_metrics()
            fan_master_input_changed = True
        elif detected_type == "survey_data":
            invalidate_survey_metrics()

        loaded_rows = len(loaded_data)
        loaded_columns = len(loaded_data.columns)
        if detected_type == "unknown":
            loaded_data = pd.DataFrame({SOURCE_FILE_COLUMN: [file_name] * loaded_rows})

        optimize_dataframe_for_session(loaded_data)
        loaded_dataframes_by_type.setdefault(detected_type, []).append(loaded_data)
        add_loaded_dataset_record(
            file_name,
            detected_type,
            loaded_rows,
            loaded_columns,
        )
        loaded_any_file = True
        detection_label = DATA_TYPE_LABELS.get(detected_type, "Unknown")
        detection_rows.append(
            {
                "file": file_name,
                "detected_type": detection_label,
                "status": "Loaded",
            }
        )
        print(f"Detected dataset type for {file_name}: {detected_type}")

    append_detection_rows(detection_rows)

    if loaded_any_file:
        append_dataframes_to_state(loaded_dataframes_by_type)
        if fan_master_input_changed:
            reset_fan_master_state(
                "New data loaded. Build the dashboard to refresh results"
            )
        st.session_state.message = "Datasets processed successfully"
    elif duplicate_found:
        st.session_state.message = "Duplicate uploads ignored"
    else:
        st.session_state.message = "No valid datasets were loaded"

    return True


def build_fan_master_from_session() -> None:
    if st.session_state.ticket_df.empty or st.session_state.transaction_df.empty:
        reset_fan_master_state(
            "Load ticket and transaction data before building the fan master dataset"
        )
        return

    try:
        fan_master = build_fan_master_dataframe(
            st.session_state.ticket_df,
            st.session_state.transaction_df,
        )
    except ValueError as error:
        reset_fan_master_state(str(error))
        return

    total_rows = len(fan_master)
    matched_rows = (
        int(fan_master["is_merch_buyer"].sum())
        if total_rows and "is_merch_buyer" in fan_master.columns
        else 0
    )
    match_rate = matched_rows / total_rows if total_rows else 0

    optimize_dataframe_for_session(fan_master)
    st.session_state.full_fan_master = fan_master
    st.session_state.fan_master_rows = total_rows
    st.session_state.fan_master_match_rate = f"{match_rate:.2%}"
    st.session_state.fan_master_message = "Dashboard built successfully"
    invalidate_fan_behavior_metrics()
    ensure_fan_behavior_metrics()


def render_upload_section() -> None:
    uploaded_files = st.file_uploader(
        "Upload datasets:",
        type=["csv", "xlsx", "xlsm", "xls", "parquet"],
        accept_multiple_files=True,
        key=f"dataset_uploader_{st.session_state.upload_widget_version}",
    )
    uploaded_files = uploaded_files or []

    if uploaded_files:
        current_upload_batch = tuple(
            (uploaded_file.name, uploaded_file.size)
            for uploaded_file in uploaded_files
        )
        if current_upload_batch != st.session_state.last_upload_batch:
            processed = process_uploaded_files(uploaded_files)
            if processed:
                st.session_state.last_upload_batch = tuple()
                st.session_state.upload_widget_version += 1
                st.rerun()
    else:
        st.session_state.last_upload_batch = tuple()
        if not st.session_state.loaded_files:
            st.session_state.message = "Please upload one or more files"

    st.info(st.session_state.message)
    render_summary_section()
    render_loaded_files_section()


def render_loaded_files_section() -> None:
    st.subheader("Detected Dataset Types")
    loaded_file_df = loaded_files_frame()
    if loaded_file_df.empty:
        st.caption("No files have been ingested yet.")
        return

    st.caption("Select a loaded file below if you need to remove it.")
    selection = st.dataframe(
        loaded_file_df,
        use_container_width=True,
        hide_index=True,
        key="loaded_files_table",
        on_select="rerun",
        selection_mode="single-row",
    )
    selected_rows = selection.selection.rows
    selected_file = (
        loaded_file_df.iloc[selected_rows[0]]["File"] if selected_rows else None
    )

    remove_col, detail_col = st.columns([1, 3])
    if remove_col.button(
        "Remove Selected File",
        disabled=selected_file is None,
        key="remove_loaded_file",
    ):
        remove_loaded_file(selected_file)
        st.rerun()

    if selected_file:
        detail_col.caption(f"Selected: {selected_file}")


def render_summary_section() -> None:
    st.header("Ingested File Summary")
    summary_items = [
        (
            "Transaction",
            loaded_file_count("transaction_data"),
            len(st.session_state.transaction_df),
        ),
        (
            "Ticket",
            loaded_file_count("ticket_data"),
            len(st.session_state.ticket_df),
        ),
        (
            "Survey",
            loaded_file_count("survey_data"),
            len(st.session_state.survey_df),
        ),
        ("Unknown", loaded_file_count("unknown"), len(st.session_state.unknown_df)),
    ]
    render_metric_cards(
        [
            {
                "label": f"{label} files",
                "value": f"{file_count:,}",
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
            }
            for label, file_count, row_count in summary_items
        ],
        st.columns(4),
    )


def build_dashboard_from_session() -> list[str]:
    built_items = []
    can_build_fan_master = (
        not st.session_state.ticket_df.empty
        and not st.session_state.transaction_df.empty
    )

    if can_build_fan_master:
        build_fan_master_from_session()
        if st.session_state.full_fan_master is not None:
            built_items.append("fan master")
    elif st.session_state.full_fan_master is None:
        reset_fan_master_state(
            "Load ticket and transaction data before building the fan master dataset"
        )

    if not st.session_state.transaction_df.empty:
        ensure_transaction_metrics()
        built_items.append("transaction metrics")
    if not st.session_state.ticket_df.empty:
        ensure_ticket_metrics()
        built_items.append("ticket metrics")
    if not st.session_state.survey_df.empty:
        ensure_survey_metrics()
        built_items.append("survey metrics")

    fan_master = st.session_state.get("full_fan_master")
    if fan_master is not None and not fan_master.empty:
        ensure_fan_behavior_metrics()
        built_items.append("fan behavior metrics")

    return built_items


def render_fan_master_section() -> None:
    st.header("Build Dashboard")

    if st.button("Build Dashboard", type="primary", key="build_dashboard"):
        with st.spinner("Building dashboard outputs..."):
            built_items = build_dashboard_from_session()
        if built_items:
            st.success("Dashboard built successfully")
        else:
            st.info("Upload data before building dashboard outputs.")

    st.write(st.session_state.fan_master_message)

    fan_master = st.session_state.full_fan_master
    if fan_master is None or fan_master.empty:
        return

    st.download_button(
        "Download Fan Master CSV",
        data=dataframe_to_csv_bytes(fan_master),
        file_name="full_fan_master.csv",
        mime="text/csv",
        key="download_fan_master_csv",
    )


def render_dashboard_page() -> None:
    initialize_session_state()

    render_page_title("Data Ingestion")
    render_upload_section()
    render_fan_master_section()


def main() -> None:
    st.set_page_config(
        page_title="Mallards Data Ingestion",
        layout="wide",
    )
    initialize_session_state()

    navigation = st.navigation(
        [
            st.Page("pages/dashboard.py", title="Data Ingestion"),
            st.Page(
                "pages/fan_behavior_dashboard.py",
                title="Fan Behavior Dashboard",
            ),
            st.Page(
                "pages/transaction_insights.py",
                title="Transaction Insights",
            ),
            st.Page("pages/survey_analysis.py", title="Survey Analysis"),
        ],
        position="sidebar",
    )
    navigation.run()


if __name__ == "__main__":
    main()
