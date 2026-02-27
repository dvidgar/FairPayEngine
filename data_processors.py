from typing import List, Tuple

from constants import *
import pandas as pd
from typing import List
from unidecode import unidecode


# -------------POINTAGES PROCESSING FUNCTIONS----------------


def add_pointages(paths: List[str]) -> pd.DataFrame:
    """Reads the pointage files and concatenates them into a single DataFrame."""
    dfs = []
    for path in paths:
        dfs.append(
            pd.read_csv(path, sep=";", encoding="latin-1", na_values=["-  ", ""])
        )
    return pd.concat(dfs, ignore_index=True)


def clean_pointages(df: pd.DataFrame) -> pd.DataFrame:
    """Fixes the dataset data format"""
    # remove all whitespace of the column names
    df.columns = df.columns.str.replace(" ", "")
    # drop unused columns
    df = df.drop(
        columns=[
            col
            for col in [
                "Unnamed:21",
                "Justificación.1",
                "Sentido.1",
                "Justificación.2",
                "Sentido.2",
                "Marcaje.2",
                "Justificación.3",
                "Sentido.3",
                "Marcaje.3",
                "Departamento",
                "Justificación",
                "Sentido",
            ]
            if col in df.columns
        ]
    )
    # drop rows where Marcaje and Marcaje.1 are both NaN
    df = df.dropna(subset=[MARCAJE, MARCAJE_1], how="all")
    # consolidate name and surname
    df[NOMBRE_COMPLETO] = (df[NOMBRE] + " " + df[APELLIDOS]).apply(unidecode)
    # replace multiple spaces with a single space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r"\s+", " ", regex=True)
    # remove the last space if the name end in a space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.strip()
    # df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r'\s+$', '', regex=True)
    # convert columns to datetime
    df[SERVICE_START] = df[MARCAJE].apply(
        lambda x: (
            pd.to_datetime(x, errors="coerce", format="%H:%M") if pd.notna(x) else x
        )
    )
    df[SERVICE_END] = df[MARCAJE_1].apply(
        lambda x: (
            pd.to_datetime(x, errors="coerce", format="%H:%M") if pd.notna(x) else x
        )
    )
    # adjust the service_start and service_end to the closest time in service_start and service_end
    df = adjust_pointages_to_scheduled_times(df)
    # fix the split services midnight problem
    df = combine_split_services(df)

    return df


def adjust_pointages_to_scheduled_times(df: pd.DataFrame) -> pd.DataFrame:
    """Adjusts pointage times to the nearest scheduled service times and calculates duration."""
    # adjust the service_start and service_end to the closest time in service_start and service_end
    df[SERVICE_START] = df[SERVICE_START].apply(
        lambda x: (
            min(
                SERVICE_START_TIMES,
                key=lambda t: abs(
                    pd.to_datetime(x, format="%H:%M")
                    - pd.to_datetime(t, format="%H:%M")
                ),
            )
            if pd.notna(x)
            else x
        )
    )
    df[SERVICE_END] = df[SERVICE_END].apply(
        lambda x: (
            min(
                SERVICE_END_TIMES,
                key=lambda t: abs(
                    pd.to_datetime(x, format="%H:%M")
                    - pd.to_datetime(t, format="%H:%M")
                ),
            )
            if pd.notna(x)
            else x
        )
    )

    # Calculate the duration of the service in hours
    df[SERVICE_DURATION] = (
        pd.to_datetime(df[SERVICE_END], format="%H:%M")
        - pd.to_datetime(df[SERVICE_START], format="%H:%M")
    ).dt.total_seconds() / 3600

    # when the service duration is negative, it means that the service end is on the next day, so we add 24 hours to the service duration
    df[SERVICE_DURATION] = (
        pd.to_datetime(df[SERVICE_END], format="%H:%M")
        - pd.to_datetime(df[SERVICE_START], format="%H:%M")
    ).dt.total_seconds() / 3600
    df.loc[df[SERVICE_DURATION] < 0, SERVICE_DURATION] += 24

    return df


def guess_pointages(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Guess the missing information."""
    df, missing_info = add_missed_service_end(df)

    return df, missing_info


def add_missed_service_end(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Guess the service end time."""
    # show NaNs in column service_duration
    df_nans = df.loc[df[SERVICE_END].isna()]
    missing_info = df_nans[[NOMBRE_COMPLETO, FECHA, MARCAJE, MARCAJE_1]]

    # add the closest service end time for each row in df_nans
    for i, t in enumerate(SERVICE_START_TIMES):
        df.loc[df[SERVICE_START] == t, SERVICE_END] = SERVICE_END_TIMES[i]

    # add NOC if the service_start is 22:00
    df.loc[df[SERVICE_START] == "22:00", NOC] = 8

    return df, missing_info


def combine_split_services(df: pd.DataFrame) -> pd.DataFrame:
    """Sometimes the same service is split into two rows with the same NOMBRE_COMPLETO and consecutive "Fecha".
    This function combines those rows into one row."""
    # get the rows with NaNs service_duration
    df_nans = df[df["service_end"].isna()]
    # Create a list to store indices of rows to drop
    rows_to_drop = []
    # Iterate through the DataFrame
    for i in list(df_nans.index):
        # skip if there is no following index in df_nans
        if i + 1 not in df_nans.index:
            continue
        current_row = df_nans.loc[i]
        next_row = df_nans.loc[i + 1]
        # Check if the current row and the next row have the same "Nombre" and consecutive "Fecha"
        if (current_row[NOMBRE_COMPLETO] == next_row[NOMBRE_COMPLETO]) and (
            (
                pd.to_datetime(next_row[FECHA]) - pd.to_datetime(current_row[FECHA])
            ).days
            == 1
        ):
            # Combine the rows by taking the first Marcaje and the second Marcaje.1
            df.at[i, SERVICE_END] = next_row[SERVICE_START]
            df.at[i, MARCAJE_1] = next_row[MARCAJE]
            # Mark the next row for dropping
            rows_to_drop.append(i + 1)
    # Drop the marked rows
    return df.drop(index=(rows_to_drop))


# -------------INVOICE PROCESSING FUNCTIONS----------------


def read_clean_invoice(path: str) -> pd.DataFrame:
    """Reads the invoice file and cleans the employee names data."""
    # read the invoice file
    df = pd.read_excel(path)[:-1]  # remove the last row which is a total
    # remove accents and convert to uppercase
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.upper().apply(unidecode)
    # replace multiple spaces with a single space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r"\s+", " ", regex=True)
    # if the name end in a space+two letters, remove the space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(
        r"(\s+)([A-Z]{2})$", r"\2", regex=True
    )
    # remove the last space if the name end in a space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.strip()
    # df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r'\s+$', '', regex=True)
    # Remove useless columns
    df = df[[NOMBRE_COMPLETO, CONCEPTO_LINEA_PEDIDO, CANTIDAD_LINEA_PEDIDO]]
    return df


# -------------COMBINE FUNCTIONS----------------


def calculate_hours_difference(pointages_df, invoice_df, hour_type="normal"):
    if hour_type == "normal":
        ett_column = SERVICE_DURATION
    elif hour_type == "extra":
        ett_column = EXT
    elif hour_type == "plus_de_nocturnidad_unitario":
        # note that the invoice is in days, not in hours
        ett_column = NOC
    else:
        raise ValueError(
            "Invalid hour type. Must be 'normal', 'extra' or 'plus_de_nocturnidad_unitario'."
        )
    total_hours_pointages_df = pointages_df.groupby(NOMBRE_COMPLETO)[ett_column].sum()
    total_hours_invoice = (
        invoice_df[invoice_df[CONCEPTO_LINEA_PEDIDO] == hour_type]
        .groupby(NOMBRE_COMPLETO)[CANTIDAD_LINEA_PEDIDO]
        .sum()
    )
    if hour_type == "plus_de_nocturnidad_unitario":
        # convert the invoice from days to hours
        total_hours_invoice = total_hours_invoice * 8
    difference = (
        (total_hours_pointages_df - total_hours_invoice)
        .dropna()
        .reset_index(name=f"Horas {hour_type} diferencia")
        .sort_values(f"Horas {hour_type} diferencia", ascending=False)
        .reset_index(drop=True)
    )
    return difference


# -------------MAIN----------------

if __name__ == "__main__":
    import glob
    from constants import UPLOAD_POINTAGES_PATH, UPLOAD_INVOICE_PATH

    pointages_paths = glob.glob(f"{UPLOAD_POINTAGES_PATH}/*.CSV")
    pointages_df = add_pointages(pointages_paths)
    pointages_df = clean_pointages(pointages_df)
    pointages_df, missing_info = guess_pointages(pointages_df)
    invoice_path = glob.glob(f"{UPLOAD_INVOICE_PATH}/*.xlsx")[0]
    invoice_df = read_clean_invoice(invoice_path)
    diff_df = calculate_hours_difference(pointages_df, invoice_df)
    print("Difference between pointages and invoice, normal hours:")
    print(diff_df)
    diff_df_extra = calculate_hours_difference(pointages_df, invoice_df, hour_type="extra")
    print("Difference between pointages and invoice, extra hours:")
    print(diff_df_extra)
    diff_df_plus_de_nocturnidad_unitario = calculate_hours_difference(
        pointages_df, invoice_df, hour_type="plus_de_nocturnidad_unitario"
    )
    print("Difference between pointages and invoice, plus de nocturnidad unitario hours:")
    print(diff_df_plus_de_nocturnidad_unitario)
    print("Missing information for pointages with missing service end:")
    print(missing_info)