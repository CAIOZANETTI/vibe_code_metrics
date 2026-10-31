"""Gerador determinístico do perfil sintético da adutora."""

from __future__ import annotations

import numpy as np
import pandas as pd

VAZAO_M3S = 0.180
COTA_RESERVATORIO_M = 810.0
DIAMETROS_COMERCIAIS_M = (0.400, 0.350, 0.300)  # DN 400, 350 e 300 mm, de montante a jusante


def gerar_perfil(
    n_trechos: int, comprimento_total_m: float = 5000.0, semente: int = 42
) -> pd.DataFrame:
    """Perfil da adutora com `n_trechos` trechos somando `comprimento_total_m`.

    Colunas: `trecho`, `comprimento_m`, `cota_terreno_m` (cota no fim do trecho, 700 a 760 m),
    `diametro_m` (DN 400/350/300 em três lances) e `coef_c` (Hazen-Williams, 120 a 140).
    Os parâmetros globais `vazao_m3s` e `cota_reservatorio_m` vão em `perfil.attrs`.
    """
    if n_trechos < 1:
        raise ValueError("n_trechos deve ser pelo menos 1")
    if comprimento_total_m <= 0:
        raise ValueError("comprimento_total_m deve ser positivo")
    gerador = np.random.default_rng(semente)

    pesos = gerador.uniform(0.5, 1.5, n_trechos)
    comprimento_m = pesos / pesos.sum() * comprimento_total_m
    comprimento_m[-1] = comprimento_total_m - comprimento_m[:-1].sum()

    fracao = np.cumsum(comprimento_m) / comprimento_total_m
    ruido_m = gerador.normal(0.0, 0.5, n_trechos)
    relevo_m = 22.0 * np.sin(2 * np.pi * 1.5 * fracao) + 8.0 * np.cos(2 * np.pi * 4.0 * fracao)
    cota_terreno_m = np.clip(730.0 + relevo_m + ruido_m, 700.0, 760.0)

    lance = np.minimum((fracao * 3).astype(np.int64), 2)
    diametro_m = np.asarray(DIAMETROS_COMERCIAIS_M, dtype=np.float64)[lance]
    coef_c = gerador.integers(120, 141, n_trechos).astype(np.float64)

    perfil = pd.DataFrame(
        {
            "trecho": np.arange(n_trechos, dtype=np.int64),
            "comprimento_m": comprimento_m,
            "cota_terreno_m": cota_terreno_m,
            "diametro_m": diametro_m,
            "coef_c": coef_c,
        }
    )
    perfil.attrs["vazao_m3s"] = VAZAO_M3S
    perfil.attrs["cota_reservatorio_m"] = COTA_RESERVATORIO_M
    return perfil
