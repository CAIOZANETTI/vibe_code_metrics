"""Conjunto de referência de cálculos determinísticos, para medir determinismo.

Cada caso devolve bytes canônicos; o hash de todos os casos deve ser idêntico entre execuções.
"""

from __future__ import annotations

import hashlib

import numpy as np
import pandas as pd

from vcm.balanco import balanco, decidir


def _bytes_vetor(valores: np.ndarray) -> bytes:
    return np.ascontiguousarray(valores, dtype=np.float64).tobytes()


def _bytes_tabela(tabela: pd.DataFrame) -> bytes:
    return pd.util.hash_pandas_object(tabela, index=True).values.tobytes()


def _caso_balanco() -> bytes:
    gerador = np.random.default_rng(42)
    metricas = ["tempo_p50_ms", "pico_ram_mb", "sloc", "cobertura_testes", "testes_falhando"]
    antes = pd.Series(gerador.uniform(1.0, 100.0, len(metricas)), index=metricas)
    depois = pd.Series(gerador.uniform(1.0, 100.0, len(metricas)), index=metricas)
    tabela = balanco(antes, depois)
    decisao = decidir(tabela)
    return _bytes_tabela(tabela.drop(columns=["pergunta", "veredito"])) + decisao.value.encode()


def _caso_soma_acumulada() -> bytes:
    valores = np.random.default_rng(42).standard_normal(1_000_000)
    return _bytes_vetor(np.cumsum(valores))


def _caso_sistema_linear() -> bytes:
    gerador = np.random.default_rng(42)
    matriz = gerador.standard_normal((200, 200)) + 200 * np.eye(200)
    independente = gerador.standard_normal(200)
    return _bytes_vetor(np.linalg.solve(matriz, independente))


def _caso_produto_matricial() -> bytes:
    gerador = np.random.default_rng(42)
    a = gerador.standard_normal((500, 500))
    b = gerador.standard_normal((500, 500))
    return _bytes_vetor(a @ b)


def casos() -> dict[str, bytes]:
    """Nome do caso -> bytes canônicos do resultado."""
    return {
        "balanco": _caso_balanco(),
        "produto_matricial": _caso_produto_matricial(),
        "sistema_linear": _caso_sistema_linear(),
        "soma_acumulada": _caso_soma_acumulada(),
    }


def hash_referencia() -> str:
    """SHA-256 (hex) de todos os casos, em ordem de nome."""
    resumo = hashlib.sha256()
    for nome, conteudo in sorted(casos().items()):
        resumo.update(nome.encode())
        resumo.update(conteudo)
    return resumo.hexdigest()


if __name__ == "__main__":
    print(hash_referencia())
