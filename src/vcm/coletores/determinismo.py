"""Coletor de determinismo: repete o conjunto de referência em subprocessos independentes."""

from __future__ import annotations

import json
import statistics
import subprocess
from collections import Counter
from pathlib import Path

from vcm.coletores.ambiente import prefixo_uv
from vcm.config import carregar_config


def _interpretar_saida(saida: str) -> tuple[str, dict]:
    """Interpreta a ÚLTIMA linha não vazia de stdout.

    Retorna (hash, extras). A linha é um JSON {"hash", "tempo_ms", "pico_ram_mb"} ou só o hash.
    """
    linhas = [linha.strip() for linha in saida.splitlines() if linha.strip()]
    if not linhas:
        raise RuntimeError("o comando de referência não imprimiu nada em stdout")
    ultima = linhas[-1]
    try:
        dados = json.loads(ultima)
    except json.JSONDecodeError:
        return ultima, {}
    if isinstance(dados, dict) and "hash" in dados:
        return str(dados["hash"]), dados
    return ultima, {}


def medir_determinismo(
    raiz: Path,
    repeticoes: int | None = None,
    comando: list[str] | tuple[str, ...] | None = None,
    timeout_s: float = 300,
) -> dict[str, float]:
    """Executa o comando de referência `repeticoes` vezes em subprocessos independentes
    (uv run --directory <raiz> <comando...>) e retorna:
    frac_execucoes_identicas -> (nº de execuções com o hash mais frequente) / repeticoes
    repeticoes_determinismo  -> repeticoes
    tempo_referencia_ms      -> MEDIANA do `tempo_ms` entre execuções (se o JSON trouxer)
    pico_ram_mb              -> MÁXIMO do `pico_ram_mb` entre execuções (se o JSON trouxer)

    `comando` e `repeticoes` None vêm de `vcm.yaml` (`vcm.config`). Sem comando de referência,
    ou se o módulo do comando não existir no projeto (commit antigo), retorna {}.

    Protocolo de saída do comando: a última linha não vazia de stdout é um JSON
    {"hash": str, "tempo_ms": float, "pico_ram_mb": float} ou apenas o hash.

    Todas as repetições usam o ambiente padrão (mesmo número de threads do BLAS). Observado:
    OMP_NUM_THREADS=1 e o padrão (4 núcleos) dão hashes diferentes entre si em produto
    matricial e solve, embora cada configuração seja estável; misturá-las faria a métrica
    ser sempre < 1, sem informar nada sobre o código medido.
    """
    raiz = Path(raiz).resolve()
    config = carregar_config(raiz)
    if comando is None:
        comando = config.comando_referencia
    if not comando:
        return {}
    if repeticoes is None:
        repeticoes = config.repeticoes
    if repeticoes < 1:
        raise ValueError("repeticoes deve ser pelo menos 1")
    completo = [*prefixo_uv(raiz, config.dependencias_extras), *comando]
    hashes: list[str] = []
    tempos_ms: list[float] = []
    picos_ram_mb: list[float] = []
    for i in range(repeticoes):
        try:
            resultado = subprocess.run(
                completo, capture_output=True, text=True, timeout=timeout_s, check=False
            )
        except subprocess.TimeoutExpired as erro:
            raise RuntimeError(f"tempo limite excedido na repetição {i + 1}") from erro
        except OSError as erro:
            raise RuntimeError(f"falha ao executar a ferramenta: {erro}") from erro
        if resultado.returncode != 0:
            if "No module named" in resultado.stderr and any(
                parte in resultado.stderr for parte in comando[1:] if not parte.startswith("-")
            ):
                return {}
            raise RuntimeError(
                f"falha ao executar o comando de referência (código {resultado.returncode}): "
                f"{resultado.stderr.strip()[-500:]}"
            )
        hash_execucao, extras = _interpretar_saida(resultado.stdout)
        hashes.append(hash_execucao)
        if "tempo_ms" in extras:
            tempos_ms.append(float(extras["tempo_ms"]))
        if extras.get("pico_ram_mb") is not None:  # None: plataforma sem medição
            picos_ram_mb.append(float(extras["pico_ram_mb"]))

    hash_dominante, mais_frequente = Counter(hashes).most_common(1)[0]
    metricas = {
        # texto, não métrica: identifica o trabalho medido (ver snapshot.retrospectiva)
        "hash_referencia": hash_dominante,
        "frac_execucoes_identicas": mais_frequente / repeticoes,
        "repeticoes_determinismo": float(repeticoes),
    }
    if tempos_ms:
        metricas["tempo_referencia_ms"] = float(statistics.median(tempos_ms))
        if len(tempos_ms) > 1 and statistics.mean(tempos_ms) > 0:
            # Oscilação entre as repetições deste snapshot (usada como ruído automático).
            metricas["cv_tempo_referencia"] = float(
                statistics.stdev(tempos_ms) / statistics.mean(tempos_ms)
            )
    if picos_ram_mb:
        metricas["pico_ram_mb"] = float(max(picos_ram_mb))
    return metricas
