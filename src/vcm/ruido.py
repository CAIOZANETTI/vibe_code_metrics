"""Estimativa do ruído de cada métrica por repetição.

Mede o mesmo commit N vezes. A variação que aparece sem nenhuma mudança de código é
ruído: tempo de execução oscila; SLOC não. O balanço usa esse ruído para não chamar de
"melhorou" ou "piorou" uma variação aleatória.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

ARQUIVO_RUIDO = Path("results/ruido.parquet")
FATOR_SEGURANCA = 2.0  # ruído aceito = FATOR × coeficiente de variação medido


def estimar(medicoes: pd.DataFrame) -> pd.DataFrame:
    """Recebe uma linha por repetição (colunas = métricas numéricas) e devolve,
    por métrica: média, desvio-padrão, coeficiente de variação e ruído relativo."""
    numericas = medicoes.apply(pd.to_numeric, errors="coerce").dropna(axis=1, how="all")
    media = numericas.mean()
    desvio = numericas.std(ddof=1)
    escala = media.abs().where(media != 0, np.nan)
    cv = (desvio / escala).fillna(0.0)
    return pd.DataFrame(
        {
            "media": media,
            "desvio": desvio,
            "coef_variacao": cv,
            "ruido_relativo": FATOR_SEGURANCA * cv,
            "repeticoes": len(numericas),
        }
    ).rename_axis("metrica")


def medir_repetido(repo: Path, ref: str = "HEAD", repeticoes: int = 3, **opcoes) -> pd.DataFrame:
    """Snapshot do mesmo commit `repeticoes` vezes (sem cache)."""
    from vcm import snapshot as snap

    linhas = [snap.snapshot(repo, ref, **opcoes) for _ in range(repeticoes)]
    tabela = pd.DataFrame(linhas)
    return tabela.drop(columns=[c for c in snap.COLUNAS_META if c in tabela.columns])


def gravar(ruido: pd.DataFrame, arquivo: Path = ARQUIVO_RUIDO) -> Path:
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    ruido.to_parquet(arquivo)
    return arquivo


def carregar(arquivo: Path = ARQUIVO_RUIDO) -> pd.Series | None:
    """Ruído relativo medido por métrica, ou None se ainda não foi estimado."""
    if not arquivo.exists():
        return None
    return pd.read_parquet(arquivo)["ruido_relativo"]
