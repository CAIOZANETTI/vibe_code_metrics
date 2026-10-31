"""Alternativa 3: híbrida (Polars para a tabela, NumPy para o cálculo)."""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl


def calcular(perfil: pd.DataFrame, vazao_m3s: float, cota_reservatorio_m: float) -> pd.DataFrame:
    """Tabela em Polars; o cálculo de Hazen-Williams SI roda em arrays NumPy."""
    tabela = pl.from_pandas(perfil[["comprimento_m", "cota_terreno_m", "diametro_m", "coef_c"]])
    comprimento_m, cota_terreno_m, diametro_m, coef_c = (
        tabela[coluna].to_numpy() for coluna in tabela.columns
    )
    perda_trecho_m = 10.67 * comprimento_m * vazao_m3s**1.852 / (coef_c**1.852 * diametro_m**4.87)
    perda_acumulada_m = np.cumsum(perda_trecho_m)
    cota_piezometrica_m = cota_reservatorio_m - perda_acumulada_m
    return pl.DataFrame(
        {
            "perda_trecho_m": perda_trecho_m,
            "perda_acumulada_m": perda_acumulada_m,
            "cota_piezometrica_m": cota_piezometrica_m,
            "pressao_disponivel_mca": cota_piezometrica_m - cota_terreno_m,
        }
    ).to_pandas()
