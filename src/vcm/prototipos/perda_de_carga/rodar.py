"""Executa o benchmark da T005 e grava `runs.parquet` e `resumo.parquet`.

Memória: usa `tracemalloc`, que só enxerga alocações Python/NumPy/pandas. Ele SUBESTIMA a memória
nativa (Rust) do Polars; o pico do Polars e da híbrida deve ser lido com essa ressalva.
O tempo é medido em execuções separadas das de memória (o `tracemalloc` distorce o tempo).
"""

from __future__ import annotations

import hashlib
import inspect
import time
import tracemalloc
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np
import pandas as pd
from radon.raw import analyze

from vcm.prototipos.perda_de_carga import (
    COLUNAS_SAIDA,
    alternativa_hibrida,
    alternativa_numpy,
    alternativa_polars,
    gabarito,
)
from vcm.prototipos.perda_de_carga.dados import gerar_perfil

TAMANHOS_PADRAO = (100, 1_000, 10_000, 100_000, 1_000_000)
REPETICOES_PADRAO = 7
LIMITE_GABARITO_PADRAO = 100_000
PASTA_PADRAO = Path("results/runs/T005")
SEMENTE = 42

FUNCOES: dict[str, Callable[..., pd.DataFrame]] = {
    "numpy": alternativa_numpy.calcular,
    "polars": alternativa_polars.calcular,
    "hibrida": alternativa_hibrida.calcular,
}


def hash_saida(saida: pd.DataFrame) -> str:
    """SHA-256 dos bytes float64 das colunas de saída, na ordem canônica."""
    resumo = hashlib.sha256()
    for coluna in COLUNAS_SAIDA:
        resumo.update(np.ascontiguousarray(saida[coluna].to_numpy(dtype=np.float64)).tobytes())
    return resumo.hexdigest()


def erro_max_abs_m(saida: pd.DataFrame, referencia: pd.DataFrame) -> float:
    """Maior diferença absoluta (m ou m.c.a.) entre a saída e a referência, em todas as colunas."""
    return max(
        float(
            np.max(
                np.abs(
                    saida[coluna].to_numpy(dtype=np.float64)
                    - referencia[coluna].to_numpy(dtype=np.float64)
                )
            )
        )
        for coluna in COLUNAS_SAIDA
    )


def sloc_da_funcao(funcao: Callable[..., object]) -> int:
    """Linhas de código-fonte (radon) da função, sem docstring, comentários e brancos."""
    return analyze(inspect.getsource(funcao)).sloc


def _medir_tempo_ms(funcao: Callable[..., pd.DataFrame], argumentos: tuple) -> float:
    inicio = time.perf_counter()
    funcao(*argumentos)
    return (time.perf_counter() - inicio) * 1000.0


def _medir_pico_mb(funcao: Callable[..., pd.DataFrame], argumentos: tuple) -> float:
    tracemalloc.start()
    try:
        funcao(*argumentos)
        _, pico_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    return pico_bytes / 1e6


def rodar(
    tamanhos: Sequence[int] = TAMANHOS_PADRAO,
    repeticoes: int = REPETICOES_PADRAO,
    pasta_saida: Path | str | None = PASTA_PADRAO,
    limite_gabarito: int = LIMITE_GABARITO_PADRAO,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Roda todas as alternativas em todos os tamanhos. Devolve (execucoes, resumo).

    Há 1 execução de aquecimento por alternativa e tamanho. Com `pasta_saida=None` nada é gravado.
    """
    sloc = {nome: sloc_da_funcao(funcao) for nome, funcao in FUNCOES.items()}
    linhas: list[dict] = []
    for n_trechos in tamanhos:
        perfil = gerar_perfil(n_trechos, semente=SEMENTE)
        argumentos = (perfil, perfil.attrs["vazao_m3s"], perfil.attrs["cota_reservatorio_m"])
        if n_trechos <= limite_gabarito:
            referencia, nome_referencia = gabarito.calcular(*argumentos), "gabarito"
        else:
            referencia, nome_referencia = alternativa_numpy.calcular(*argumentos), "numpy"
        for nome, funcao in FUNCOES.items():
            funcao(*argumentos)  # aquecimento
            for repeticao in range(repeticoes):
                tempo_ms = _medir_tempo_ms(funcao, argumentos)
                pico_mb = _medir_pico_mb(funcao, argumentos)
                saida = funcao(*argumentos)
                linhas.append(
                    {
                        "alternativa": nome,
                        "n_trechos": n_trechos,
                        "repeticao": repeticao,
                        "tempo_ms": tempo_ms,
                        "pico_mb": pico_mb,
                        "erro_max_abs_m": erro_max_abs_m(saida, referencia),
                        "referencia": nome_referencia,
                        "hash_saida": hash_saida(saida),
                        "sloc": sloc[nome],
                    }
                )
    execucoes = pd.DataFrame(linhas)
    resumo = resumir(execucoes)
    if pasta_saida is not None:
        pasta = Path(pasta_saida)
        pasta.mkdir(parents=True, exist_ok=True)
        execucoes.to_parquet(pasta / "runs.parquet", index=False)
        resumo.to_parquet(pasta / "resumo.parquet", index=False)
    return execucoes, resumo


def resumir(execucoes: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por alternativa x tamanho: p50, p95, pico, erro, determinismo e SLOC."""
    agrupado = execucoes.groupby(["alternativa", "n_trechos"], sort=False)
    resumo = agrupado.agg(
        tempo_p50_ms=("tempo_ms", lambda s: float(np.percentile(s, 50))),
        tempo_p95_ms=("tempo_ms", lambda s: float(np.percentile(s, 95))),
        pico_mb=("pico_mb", "max"),
        erro_max_abs_m=("erro_max_abs_m", "max"),
        referencia=("referencia", "first"),
        n_hashes=("hash_saida", "nunique"),
        sloc=("sloc", "first"),
    ).reset_index()
    resumo["deterministico"] = resumo["n_hashes"] == 1
    return resumo.drop(columns="n_hashes")
