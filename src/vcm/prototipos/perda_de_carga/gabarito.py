"""Gabarito (avaliador): solução de referência independente, em Python puro.

Usa só `math` e laço escalar; a soma cumulativa é EXATA (somas parciais de Shewchuk, o mesmo
algoritmo de `math.fsum`), de modo que o erro das alternativas vetorizadas é medido sem o ruído
de arredondamento do oráculo.
"""

from __future__ import annotations

import math

import pandas as pd


def perda_trecho_m(
    comprimento_m: float, vazao_m3s: float, coef_c: float, diametro_m: float
) -> float:
    """Perda de carga de um trecho (m), Hazen-Williams SI."""
    return (
        10.67
        * comprimento_m
        * math.pow(vazao_m3s, 1.852)
        / (math.pow(coef_c, 1.852) * math.pow(diametro_m, 4.87))
    )


def perda_total_uniforme_m(
    comprimento_total_m: float, vazao_m3s: float, coef_c: float, diametro_m: float
) -> float:
    """Fórmula fechada para tubulação uniforme: 10,67·L·Q^1,852 / (C^1,852·D^4,87)."""
    return 10.67 * comprimento_total_m * vazao_m3s**1.852 / (coef_c**1.852 * diametro_m**4.87)


def _somar_parcial(parciais: list[float], valor: float) -> None:
    """Acrescenta `valor` às somas parciais exatas (algoritmo `msum`)."""
    indice = 0
    for parcial in parciais:
        if abs(valor) < abs(parcial):
            valor, parcial = parcial, valor
        alta = valor + parcial
        baixa = parcial - (alta - valor)
        if baixa:
            parciais[indice] = baixa
            indice += 1
        valor = alta
    parciais[indice:] = [valor]


def calcular(perfil: pd.DataFrame, vazao_m3s: float, cota_reservatorio_m: float) -> pd.DataFrame:
    """Linha piezométrica de referência, trecho a trecho (laço escalar: é o oráculo)."""
    perdas, acumuladas, piezometricas, pressoes = [], [], [], []
    parciais: list[float] = []
    linhas = zip(
        perfil["comprimento_m"].tolist(),
        perfil["cota_terreno_m"].tolist(),
        perfil["diametro_m"].tolist(),
        perfil["coef_c"].tolist(),
    )
    for comprimento_m, cota_terreno_m, diametro_m, coef_c in linhas:
        perda_m = perda_trecho_m(comprimento_m, vazao_m3s, coef_c, diametro_m)
        _somar_parcial(parciais, perda_m)
        acumulada_m = math.fsum(parciais)
        piezometrica_m = cota_reservatorio_m - acumulada_m
        perdas.append(perda_m)
        acumuladas.append(acumulada_m)
        piezometricas.append(piezometrica_m)
        pressoes.append(piezometrica_m - cota_terreno_m)
    return pd.DataFrame(
        {
            "perda_trecho_m": perdas,
            "perda_acumulada_m": acumuladas,
            "cota_piezometrica_m": piezometricas,
            "pressao_disponivel_mca": pressoes,
        }
    )
