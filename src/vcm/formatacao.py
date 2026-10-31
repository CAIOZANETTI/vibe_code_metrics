"""Formatação brasileira para apresentação (vírgula decimal, ponto de milhar).

A formatação é feita em Python; o HTML só exibe o texto pronto.
"""

from __future__ import annotations

import math


def numero(valor: float | None, casas: int = 2) -> str:
    """1234.5 -> '1.234,50'. None ou NaN -> '—'."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "§").replace(".", ",").replace("§", ".")


def percentual(valor: float | None, casas: int = 1, sinal: bool = True) -> str:
    """12.345 -> '+12,3%' (o valor já está em pontos percentuais)."""
    if valor is None or (isinstance(valor, float) and math.isnan(valor)):
        return "—"
    prefixo = "+" if sinal and valor > 0 else ""
    return f"{prefixo}{numero(valor, casas)}%"


def cientifica(valor: float, casas: int = 1) -> str:
    """Notação científica com vírgula decimal: 1.2e-14 -> '1,2e-14'."""
    return f"{valor:.{casas}e}".replace(".", ",")
