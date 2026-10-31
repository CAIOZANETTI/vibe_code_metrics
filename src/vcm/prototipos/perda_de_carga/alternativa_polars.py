"""Alternativa 2: Polars puro (expressões)."""

from __future__ import annotations

import pandas as pd
import polars as pl


def calcular(perfil: pd.DataFrame, vazao_m3s: float, cota_reservatorio_m: float) -> pd.DataFrame:
    """Linha piezométrica por trechos (Hazen-Williams SI) só com expressões Polars."""
    return (
        pl.from_pandas(perfil[["comprimento_m", "cota_terreno_m", "diametro_m", "coef_c"]])
        .with_columns(
            perda_trecho_m=10.67
            * pl.col("comprimento_m")
            * vazao_m3s**1.852
            / (pl.col("coef_c") ** 1.852 * pl.col("diametro_m") ** 4.87)
        )
        .with_columns(perda_acumulada_m=pl.col("perda_trecho_m").cum_sum())
        .with_columns(cota_piezometrica_m=cota_reservatorio_m - pl.col("perda_acumulada_m"))
        .with_columns(
            pressao_disponivel_mca=pl.col("cota_piezometrica_m") - pl.col("cota_terreno_m")
        )
        .select(
            "perda_trecho_m", "perda_acumulada_m", "cota_piezometrica_m", "pressao_disponivel_mca"
        )
        .to_pandas()
    )
