"""Conjunto de referência de cálculos determinísticos, para medir determinismo.

Cada caso devolve bytes canônicos; o hash de todos os casos deve ser idêntico entre execuções.
"""

from __future__ import annotations

import hashlib
import json
import time

import numpy as np
import pandas as pd

from vcm import medicao
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


def _caso_perda_de_carga() -> bytes:
    """Linha piezométrica da adutora de 5 km (T005, alternativa NumPy), 1.000 trechos."""
    from vcm.prototipos.perda_de_carga import alternativa_numpy, dados

    perfil = dados.gerar_perfil(1_000)
    saida = alternativa_numpy.calcular(perfil, dados.VAZAO_M3S, dados.COTA_RESERVATORIO_M)
    return np.ascontiguousarray(saida.to_numpy(), dtype=np.float64).tobytes()


def casos() -> dict[str, bytes]:
    """Nome do caso -> bytes canônicos do resultado."""
    return {
        "balanco": _caso_balanco(),
        "perda_de_carga": _caso_perda_de_carga(),
        "produto_matricial": _caso_produto_matricial(),
        "sistema_linear": _caso_sistema_linear(),
        "soma_acumulada": _caso_soma_acumulada(),
    }


def _hash_dos_casos(conteudos: dict[str, bytes]) -> str:
    resumo = hashlib.sha256()
    for nome, conteudo in sorted(conteudos.items()):
        resumo.update(nome.encode())
        resumo.update(conteudo)
    return resumo.hexdigest()


def hash_referencia() -> str:
    """SHA-256 (hex) de todos os casos, em ordem de nome."""
    return _hash_dos_casos(casos())


def medir_referencia() -> dict[str, float | str]:
    """Roda `casos()` uma vez e devolve hash, tempo (ms) e pico de RAM (MiB).

    `tempo_ms`: duração de `casos()` com `time.perf_counter` dentro do processo.
    `pico_ram_mb`: pico de memória do processo (MiB), portável via `vcm.medicao`.
    """
    inicio_s = time.perf_counter()
    conteudos = casos()
    tempo_ms = (time.perf_counter() - inicio_s) * 1000.0
    pico_ram_mb = medicao.pico_ram_mb()
    return {
        "hash": _hash_dos_casos(conteudos),
        "tempo_ms": tempo_ms,
        "pico_ram_mb": pico_ram_mb,
    }


if __name__ == "__main__":
    print(json.dumps(medir_referencia()))
