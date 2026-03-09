"""Ader invoice processing module. This module contains functions to read and clean the invoice data, and to calculate the difference in hours between the pointages and the invoice for each employee."""

from deliverable.constants import (
    CANTIDAD_LINEA_PEDIDO,
    CONCEPTO_LINEA_PEDIDO,
    NOMBRE_COMPLETO,
)


import pandas as pd


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
    # Remove useless columns
    return df[[NOMBRE_COMPLETO, CONCEPTO_LINEA_PEDIDO, CANTIDAD_LINEA_PEDIDO]]
