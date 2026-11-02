"""Medição do histórico do git: uma série de snapshots, um por commit amostrado.

Reaproveita `vcm.snapshot.obter_snapshot` (e o cache em Parquet) para cada commit.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from vcm.snapshot import ARQUIVO_SNAPSHOTS, _git, obter_snapshot, resolver_commit


def commits_amostrados(
    repo: Path,
    desde: str | None = None,
    ate: str = "HEAD",
    passo: int = 1,
    maximo: int | None = None,
) -> list[str]:
    """Commits da primeira linha (do mais antigo ao mais novo), um a cada `passo`.

    O primeiro e o último sempre entram. `maximo` limita a quantidade por amostra uniforme.
    """
    if passo < 1:
        raise ValueError("passo deve ser pelo menos 1")
    saida = _git(repo, "log", "--first-parent", "--reverse", "--format=%H", ate)
    todos = saida.split()
    if desde is not None:
        inicio = resolver_commit(repo, desde)
        if inicio not in todos:
            raise ValueError(f"'{desde}' não está na primeira linha de '{ate}'")
        todos = todos[todos.index(inicio) :]
    if not todos:
        return []
    ultimo = len(todos) - 1
    posicoes = np.union1d(np.arange(0, len(todos), passo), [ultimo])
    if maximo is not None and len(posicoes) > maximo:
        if maximo < 2:
            posicoes = np.array([ultimo])
        else:
            posicoes = np.unique(np.linspace(0, ultimo, maximo).round().astype(int))
    return [todos[i] for i in posicoes]


def medir_historico(
    repo: Path,
    commits: list[str],
    com_testes: bool = False,
    arquivo: Path = ARQUIVO_SNAPSHOTS,
    medidor=None,
) -> pd.DataFrame:
    """Mede cada commit (com cache) e devolve a série ordenada por `data_commit`."""
    opcoes: dict = {"com_testes": com_testes}
    if medidor is not None:
        opcoes["medidor"] = medidor
    linhas = []
    for i, commit in enumerate(commits, start=1):
        print(f"{i}/{len(commits)} {commit[:7]}", flush=True)
        linhas.append(obter_snapshot(repo, commit, arquivo=arquivo, **opcoes))
    if not linhas:
        return pd.DataFrame()
    serie = pd.DataFrame(linhas).reset_index(drop=True)
    instante = pd.to_datetime(serie["data_commit"], utc=True)
    return serie.iloc[np.argsort(instante.to_numpy(), kind="stable")].reset_index(drop=True)
