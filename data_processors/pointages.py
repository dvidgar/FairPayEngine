"""This module contains functions to process the pointage data, which is the raw data of the services performed by the employees. It includes functions to read the pointage files, clean the data, adjust the service times to the scheduled times, and guess missing information."""

import pandas as pd


from typing import List, Tuple

from deliverable.constants import (
    APELLIDOS,
    FECHA,
    MARCAJE,
    MARCAJE_1,
    MAX_DIFFERENCE_FROM_SCHEDULE,
    NOC,
    NOMBRE,
    NOMBRE_COMPLETO,
    SERVICE_DURATION,
    SERVICE_END,
    SERVICE_END_TIMES,
    SERVICE_START,
    SERVICE_START_TIMES,
)


def add_pointages(paths: List[str]) -> pd.DataFrame:
    """Reads the pointage files and concatenates them into a single DataFrame."""
    dfs = []
    for path in paths:
        dfs.append(
            pd.read_csv(path, sep=";", encoding="latin-1", na_values=["-  ", ""])
        )
    return pd.concat(dfs, ignore_index=True)


def adjust_pointages_to_scheduled_times(df: pd.DataFrame) -> pd.DataFrame:
    """Adjusts pointage times to the nearest scheduled service times and calculates duration."""
    # adjust the service_start and service_end to the closest time, with a margin of 1 hour.
    # If start time is after the start of the pointage period, no adjustment is made.
    start_times = [pd.to_datetime(t, format="%H:%M") for t in SERVICE_START_TIMES]
    end_times = [pd.to_datetime(t, format="%H:%M") for t in SERVICE_END_TIMES]
    for _, t in enumerate(start_times):
        df.loc[
            (df[SERVICE_START] >= t - MAX_DIFFERENCE_FROM_SCHEDULE)
            & (df[SERVICE_START] < t),
            SERVICE_START,
        ] = t
    for _, t in enumerate(end_times):
        df.loc[
            (df[SERVICE_END] > t)
            & (df[SERVICE_END] <= t + MAX_DIFFERENCE_FROM_SCHEDULE),
            SERVICE_END,
        ] = t

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
            (pd.to_datetime(next_row[FECHA]) - pd.to_datetime(current_row[FECHA])).days
            == 1
        ):
            # Combine the rows by taking the first Marcaje and the second Marcaje.1
            df.at[i, SERVICE_END] = next_row[SERVICE_START]
            df.at[i, MARCAJE_1] = next_row[MARCAJE]
            # Mark the next row for dropping
            rows_to_drop.append(i + 1)
    # Drop the marked rows
    return df.drop(index=(rows_to_drop))


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


def guess_pointages(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """Guess the missing information."""
    df, missing_info = add_missed_service_end(df)

    return df, missing_info
