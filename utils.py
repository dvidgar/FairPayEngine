from typing import List

from constants import NOMBRE, APELLIDOS, NOMBRE_COMPLETO, PRES, CANTIDAD_LINEA_PEDIDO, HORAS_DIFERENCIA
import os
import warnings
import pandas as pd
from typing import List
from unidecode import unidecode


def clear_dir(path):
    """check if upload path exists and empty it."""
    if os.path.exists(path):
        for f in os.listdir(path):
            os.remove(os.path.join(path, f))


def add_pointages(paths: List[str]) -> pd.DataFrame:
    """Reads the pointage files and concatenates them into a single DataFrame."""
    dfs = []
    for path in [paths[0], paths[1], paths[3]]:
        dfs.append(pd.read_csv(path, sep=";", encoding='latin-1', na_values=['-  ', '']))
    df = pd.concat(dfs, ignore_index=True)
    
    return df

def clean_pointages(input_df: pd.DataFrame) -> pd.DataFrame:
    """Fixes the dataset data format"""
    df = input_df.copy()
    # consolidate name and surname
    df[NOMBRE_COMPLETO] = (df[NOMBRE] + " " + df[APELLIDOS]).apply(unidecode)
    # replace multiple spaces with a single space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r'\s+', ' ', regex=True)
    # remove the last space if the name end in a space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.strip()
    # df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r'\s+$', '', regex=True)
    
    return df

def read_clean_invoice(path: str) -> pd.DataFrame:
    """Reads the invoice file and cleans the employee names data."""
    # read the invoice file
    df = pd.read_excel(path)[:-1]  #remove the last row which is a total
    # remove accents and convert to uppercase
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.upper().apply(unidecode)
    # replace multiple spaces with a single space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r'\s+', ' ', regex=True)
    # if the name end in a space+two letters, remove the space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r'(\s+)([A-Z]{2})$', r'\2', regex=True)
    # remove the last space if the name end in a space
    df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.strip()
    # df[NOMBRE_COMPLETO] = df[NOMBRE_COMPLETO].str.replace(r'\s+$', '', regex=True)
    return df

def process_data(pointages_df: pd.DataFrame, invoice_df: pd.DataFrame) -> pd.DataFrame:
    pointages_hours = pointages_df.groupby(NOMBRE_COMPLETO)[PRES].sum()
    invoice_hours = invoice_df.groupby(NOMBRE_COMPLETO)[CANTIDAD_LINEA_PEDIDO].sum()
    
    diff = (pointages_hours - invoice_hours).dropna().reset_index(name=HORAS_DIFERENCIA)
    return diff.sort_values(HORAS_DIFERENCIA, ascending=False).reset_index(drop=True)

