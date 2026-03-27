from typing import List

import pandas as pd

from constants import (
    CANTIDAD_LINEA_PEDIDO,
    CONCEPTO_LINEA_PEDIDO,
    EXT,
    NOC,
    NOMBRE_COMPLETO,
    SERVICE_DURATION,
)
from data_processors.ader_invoice import read_clean_invoice
from data_processors.pointages import add_pointages, clean_pointages, guess_pointages


def calculate_hours_difference(
    pointages_df: pd.DataFrame, invoice_df: pd.DataFrame, hour_type: str = "normal"
) -> tuple:
    """Calculates the difference in hours between the pointages and the invoice for each employee."""
    # TODO: only working for ader standard invoice
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
    return difference, total_hours_invoice, total_hours_pointages_df


def web_main(pointages_paths: List[str], invoice_path: str) -> tuple:
    pointages_df = add_pointages(pointages_paths)
    pointages_df = clean_pointages(pointages_df)
    pointages_df, missing_info = guess_pointages(pointages_df)
    invoice_df = read_clean_invoice(invoice_path)
    diff_df, total_hours_invoice, total_hours_pointages_df = calculate_hours_difference(
        pointages_df, invoice_df
    )
    print("Difference between pointages and invoice, normal hours:")
    print(diff_df)
    diff_df_extra, total_hours_invoice_extra, total_hours_pointages_df_extra = (
        calculate_hours_difference(pointages_df, invoice_df, hour_type="extra")
    )
    print("Difference between pointages and invoice, extra hours:")
    print(diff_df_extra)
    (
        diff_df_plus_de_nocturnidad_unitario,
        total_hours_invoice_plus_de_nocturnidad_unitario,
        total_hours_pointages_df_plus_de_nocturnidad_unitario,
    ) = calculate_hours_difference(
        pointages_df, invoice_df, hour_type="plus_de_nocturnidad_unitario"
    )
    print(
        "Difference between pointages and invoice, plus de nocturnidad unitario hours:"
    )
    print(diff_df_plus_de_nocturnidad_unitario)
    print("Missing information for pointages with missing service end:")
    print(missing_info)

    return (
        diff_df,
        diff_df_extra,
        diff_df_plus_de_nocturnidad_unitario,
        missing_info,
        total_hours_invoice,
        total_hours_pointages_df,
        total_hours_invoice_extra,
        total_hours_pointages_df_extra,
        total_hours_invoice_plus_de_nocturnidad_unitario,
        total_hours_pointages_df_plus_de_nocturnidad_unitario,
    )


# -------------MAIN----------------

if __name__ == "__main__":
    import glob

    from constants import UPLOAD_INVOICE_PATH, UPLOAD_POINTAGES_PATH

    pointages_paths = glob.glob(f"{UPLOAD_POINTAGES_PATH}/*.CSV")
    invoice_path = glob.glob(f"{UPLOAD_INVOICE_PATH}/*.xlsx")[0]

    output_df = web_main(pointages_paths, invoice_path)

    # Save to Excel
    with pd.ExcelWriter("output.xlsx") as writer:
        output_df[0].to_excel(writer, sheet_name="Normal Hours Difference", index=False)
        output_df[1].to_excel(writer, sheet_name="Extra Hours Difference", index=False)
        output_df[2].to_excel(
            writer,
            sheet_name="Plus de Nocturnidad Unitario Hours Difference",
            index=False,
        )
        output_df[3].to_excel(writer, sheet_name="Missing Information", index=False)
        output_df[4].to_excel(writer, sheet_name="Fichajes internos", index=False)
        output_df[5].to_excel(writer, sheet_name="Factura recibida", index=False)
