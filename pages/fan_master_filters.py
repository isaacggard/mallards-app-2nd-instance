import pandas as pd


EXCLUDED_FAN_MASTER_PHONES = {"608-246-4277"}


def filter_excluded_ticket_phones(ticket_df: pd.DataFrame) -> pd.DataFrame:
    phone_column = "Customer Phone"
    if ticket_df.empty or phone_column not in ticket_df.columns:
        return ticket_df

    keep_rows = ~ticket_df[phone_column].astype("string").str.strip().isin(
        EXCLUDED_FAN_MASTER_PHONES
    )
    if keep_rows.all():
        return ticket_df
    return ticket_df.loc[keep_rows]


def install_fan_master_filters(app_module) -> None:
    current_normalizer = app_module.normalize_ticket_data
    if getattr(current_normalizer, "_fan_master_phone_filter", False):
        return

    def normalize_ticket_data_with_filters(ticket_df: pd.DataFrame) -> pd.DataFrame:
        return current_normalizer(filter_excluded_ticket_phones(ticket_df))

    normalize_ticket_data_with_filters._fan_master_phone_filter = True
    app_module.normalize_ticket_data = normalize_ticket_data_with_filters
