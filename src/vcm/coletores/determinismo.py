"""Coletor de determinismo: repete o conjunto de referência em subprocessos independentes."""

from __future__ import annotations

import subprocess
from collections import Counter
from pathlib import Path


def medir_determinismo(raiz: Path, repeticoes: int = 5, timeout_s: float = 300) -> dict[str, float]:
    """Executa `python -m vcm.referencia` em `repeticoes` subprocessos independentes
    (uv run --directory <raiz> python -m vcm.referencia) e retorna:
    frac_execucoes_identicas -> (nº de execuções com o hash mais frequente) / repeticoes
    repeticoes_determinismo  -> repeticoes
    Se o módulo vcm.referencia não existir no projeto (commit antigo), retorna {}.

    Todas as repetições usam o ambiente padrão (mesmo número de threads do BLAS). Observado:
    OMP_NUM_THREADS=1 e o padrão (4 núcleos) dão hashes diferentes entre si em produto
    matricial e solve, embora cada configuração seja estável; misturá-las faria a métrica
    ser sempre < 1, sem informar nada sobre o código medido.
    """
    if repeticoes < 1:
        raise ValueError("repeticoes deve ser pelo menos 1")
    raiz = Path(raiz).resolve()
    comando = ["uv", "run", "--directory", str(raiz), "python", "-m", "vcm.referencia"]
    hashes: list[str] = []
    for i in range(repeticoes):
        try:
            resultado = subprocess.run(
                comando, capture_output=True, text=True, timeout=timeout_s, check=False
            )
        except subprocess.TimeoutExpired as erro:
            raise RuntimeError(f"tempo limite excedido na repetição {i + 1}") from erro
        except OSError as erro:
            raise RuntimeError(f"falha ao executar a ferramenta: {erro}") from erro
        if resultado.returncode != 0:
            if "No module named" in resultado.stderr and "vcm.referencia" in resultado.stderr:
                return {}
            raise RuntimeError(
                f"falha ao executar vcm.referencia (código {resultado.returncode}): "
                f"{resultado.stderr.strip()[-500:]}"
            )
        hashes.append(resultado.stdout.strip())

    mais_frequente = Counter(hashes).most_common(1)[0][1]
    return {
        "frac_execucoes_identicas": mais_frequente / repeticoes,
        "repeticoes_determinismo": float(repeticoes),
    }
