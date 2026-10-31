"""Snapshot de métricas de um ref do git e retrospectiva entre dois refs.

`snapshot` cria uma worktree temporária no ref pedido, roda os coletores e devolve
uma linha de métricas. Os snapshots ficam em cache em `results/snapshots.parquet`,
indexados pelo hash do commit, para não medir duas vezes o mesmo código.
"""

from __future__ import annotations

import subprocess
import tempfile
from contextlib import contextmanager
from dataclasses import replace
from pathlib import Path

import pandas as pd

from vcm import balanco as bal

ARQUIVO_SNAPSHOTS = Path("results/snapshots.parquet")
PASTA_ITERACOES = Path("results/iteracoes")
COLUNAS_META = ["commit", "ref", "data_commit", "mensagem", "hash_referencia"]
# Métricas que só são comparáveis se o conjunto de referência (o trabalho medido) for o mesmo.
METRICAS_DA_REFERENCIA = ("tempo_referencia_ms", "pico_ram_mb")


def _git(repo: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(repo), *args], check=False, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} falhou: {r.stderr.strip()}")
    return r.stdout.strip()


def resolver_commit(repo: Path, ref: str) -> str:
    return _git(repo, "rev-parse", f"{ref}^{{commit}}")


@contextmanager
def worktree_temporaria(repo: Path, commit: str):
    """Worktree destacada (detached) no commit, removida ao sair."""
    pasta = Path(tempfile.mkdtemp(prefix="vcm-snapshot-")) / "arvore"
    _git(repo, "worktree", "add", "--detach", str(pasta), commit)
    try:
        yield pasta
    finally:
        _git(repo, "worktree", "remove", "--force", str(pasta))


def medir(raiz: Path, repeticoes_determinismo: int | None = None, com_testes: bool = True) -> dict:
    """Roda todos os coletores sobre um diretório de projeto.

    As pastas, o comando de referência e (se `repeticoes_determinismo` for None) as repetições
    vêm do `vcm.yaml` do projeto medido (ver `vcm.config`).
    """
    from vcm.coletores.codigo import medir_codigo
    from vcm.coletores.determinismo import medir_determinismo
    from vcm.coletores.testes import medir_testes

    metricas: dict = {}
    metricas.update(medir_codigo(raiz))
    if com_testes:
        metricas.update(medir_testes(raiz))
    metricas.update(medir_determinismo(raiz, repeticoes=repeticoes_determinismo))
    return metricas


def snapshot(
    repo: Path,
    ref: str = "HEAD",
    repeticoes_determinismo: int | None = None,
    com_testes: bool = True,
    medidor=medir,
) -> pd.Series:
    """Mede o código do `ref` numa worktree temporária e devolve uma Series."""
    commit = resolver_commit(repo, ref)
    with worktree_temporaria(repo, commit) as pasta:
        metricas = medidor(
            pasta, repeticoes_determinismo=repeticoes_determinismo, com_testes=com_testes
        )
    meta = {
        "commit": commit,
        "ref": ref,
        "data_commit": _git(repo, "log", "-1", "--format=%cI", commit),
        "mensagem": _git(repo, "log", "-1", "--format=%s", commit),
    }
    return pd.Series({**meta, **metricas})


def ler_snapshots(arquivo: Path = ARQUIVO_SNAPSHOTS) -> pd.DataFrame:
    if not arquivo.exists():
        return pd.DataFrame(columns=COLUNAS_META)
    return pd.read_parquet(arquivo)


def gravar_snapshot(linha: pd.Series, arquivo: Path = ARQUIVO_SNAPSHOTS) -> pd.DataFrame:
    """Grava (ou substitui) o snapshot do commit no Parquet de cache."""
    tabela = ler_snapshots(arquivo)
    tabela = tabela[tabela["commit"] != linha["commit"]]
    nova = pd.DataFrame([linha.to_dict()])
    tabela = nova if tabela.empty else pd.concat([tabela, nova], ignore_index=True)
    tabela = tabela.sort_values("data_commit", kind="stable").reset_index(drop=True)
    arquivo.parent.mkdir(parents=True, exist_ok=True)
    tabela.to_parquet(arquivo, index=False)
    return tabela


def obter_snapshot(
    repo: Path,
    ref: str,
    arquivo: Path = ARQUIVO_SNAPSHOTS,
    refazer: bool = False,
    **opcoes,
) -> pd.Series:
    """Usa o cache se o commit já foi medido; senão mede e grava."""
    commit = resolver_commit(repo, ref)
    tabela = ler_snapshots(arquivo)
    achado = tabela[tabela["commit"] == commit]
    if not refazer and not achado.empty:
        return achado.iloc[-1].dropna()
    linha = snapshot(repo, ref, **opcoes)
    gravar_snapshot(linha, arquivo)
    return linha


def retrospectiva(
    antes: pd.Series, depois: pd.Series, ruido_medido: pd.Series | None = None
) -> dict:
    """Balanço completo entre dois snapshots: tabela, respostas e decisão.

    `ruido_medido`: ruído relativo por métrica estimado com `vcm.ruido` (opcional).
    """
    numericas = [i for i in antes.index if i not in COLUNAS_META]
    a = pd.to_numeric(antes[numericas], errors="coerce").dropna()
    d = pd.to_numeric(depois.drop(labels=COLUNAS_META, errors="ignore"), errors="coerce").dropna()
    hash_a, hash_d = antes.get("hash_referencia"), depois.get("hash_referencia")
    referencia_mudou = bool(hash_a and hash_d and hash_a != hash_d)
    catalogo = dict(bal.METRICAS_PADRAO)
    if referencia_mudou:
        # Outro trabalho: tempo e memória deixam de ser comparáveis e viram informativos.
        for nome in METRICAS_DA_REFERENCIA:
            catalogo[nome] = replace(catalogo[nome], sentido=0)
    tabela = bal.balanco(a, d, metricas=catalogo, ruido_medido=ruido_medido)
    return {
        "referencia_mudou": referencia_mudou,
        "depois_valores": d,
        "base": antes.get("commit", ""),
        "alvo": depois.get("commit", ""),
        "mensagem_alvo": depois.get("mensagem", ""),
        "tabela": tabela,
        "respostas": bal.respostas(tabela),
        "decisao": bal.decidir(tabela),
    }
