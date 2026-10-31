"""Alternativa 1: NumPy puro."""

from __future__ import annotations

import numpy as np
import pandas as pd


def calcular(perfil: pd.DataFrame, vazao_m3s: float, cota_reservatorio_m: float) -> pd.DataFrame:
    """Linha piezométrica por trechos (Hazen-Williams SI) com arrays NumPy."""
    comprimento_m = perfil["comprimento_m"].to_numpy(dtype=np.float64)
    cota_terreno_m = perfil["cota_terreno_m"].to_numpy(dtype=np.float64)
    diametro_m = perfil["diametro_m"].to_numpy(dtype=np.float64)
    coef_c = perfil["coef_c"].to_numpy(dtype=np.float64)
    perda_trecho_m = 10.67 * comprimento_m * vazao_m3s**1.852 / (coef_c**1.852 * diametro_m**4.87)
    perda_acumulada_m = np.cumsum(perda_trecho_m)
    cota_piezometrica_m = cota_reservatorio_m - perda_acumulada_m
    return pd.DataFrame(
        {
            "perda_trecho_m": perda_trecho_m,
            "perda_acumulada_m": perda_acumulada_m,
            "cota_piezometrica_m": cota_piezometrica_m,
            "pressao_disponivel_mca": cota_piezometrica_m - cota_terreno_m,
        }
    )
