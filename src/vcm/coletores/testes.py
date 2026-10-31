"""Coletor de métricas da suíte de testes (total, falhas, cobertura e duração)."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import defusedxml.ElementTree as ET

from vcm.coletores.ambiente import prefixo_uv
from vcm.config import carregar_config


def _executar(comando: list[str], timeout_s: float, ambiente: dict[str, str]) -> None:
    """Roda um comando; timeout ou ferramenta ausente viram `RuntimeError`."""
    try:
        subprocess.run(
            comando, capture_output=True, text=True, timeout=timeout_s, env=ambiente, check=False
        )
    except subprocess.TimeoutExpired as erro:
        raise RuntimeError(f"tempo limite de {timeout_s:g} s excedido ao rodar os testes") from erro
    except OSError as erro:
        raise RuntimeError(f"falha ao executar a ferramenta: {erro}") from erro


def _ler_junit(caminho: Path) -> tuple[int, int, float]:
    """Retorna (total, falhando, tempo_s) do XML JUnit; falhando = falhas + erros."""
    raiz = ET.parse(caminho).getroot()
    suites = [raiz] if raiz.tag == "testsuite" else list(raiz.iter("testsuite"))
    total = sum(int(s.get("tests", 0)) for s in suites)
    falhando = sum(int(s.get("failures", 0)) + int(s.get("errors", 0)) for s in suites)
    tempo_s = sum(float(s.get("time", 0.0)) for s in suites)
    return total, falhando, tempo_s


def medir_testes(raiz: Path, timeout_s: float = 900) -> dict[str, float]:
    """Roda a suíte de testes do projeto em `raiz` com cobertura, em subprocesso. Retorna:
    testes_total, testes_falhando (falhas + erros), cobertura_testes (fração 0–1 das linhas das pastas-fonte),
    tempo_testes_s (duração da suíte). Pastas-fonte e de testes vêm do `vcm.yaml`
    (ou da autodetecção). Se não houver a pasta de testes, retorna testes_total=0 e não roda nada.
    """
    raiz = Path(raiz).resolve()
    config = carregar_config(raiz)
    if not (raiz / config.pasta_testes).is_dir():
        return {
            "testes_total": 0.0,
            "testes_falhando": 0.0,
            "cobertura_testes": 0.0,
            "tempo_testes_s": 0.0,
        }

    with tempfile.TemporaryDirectory(prefix="vcm_testes_") as pasta:
        tmp = Path(pasta)
        junit = tmp / "junit.xml"
        cobertura = tmp / "cov.json"
        ambiente = {**os.environ, "COVERAGE_FILE": str(tmp / ".coverage")}
        fonte = ",".join(config.pastas_fonte)
        prefixo = prefixo_uv(raiz, ("coverage", "pytest", *config.dependencias_extras))

        _executar(
            [
                *prefixo,
                *["coverage", "run", f"--source={fonte}", "-m", "pytest", "-q"],
                *[config.pasta_testes, "-p", "no:cacheprovider", f"--junitxml={junit}"],
            ],
            timeout_s,
            ambiente,
        )
        if not junit.exists():
            raise RuntimeError(
                "a suíte de testes não gerou o relatório JUnit (falha da ferramenta)"
            )
        _executar([*prefixo, "coverage", "json", "-o", str(cobertura)], timeout_s, ambiente)
        if not cobertura.exists():
            raise RuntimeError("não foi possível gerar o relatório de cobertura")

        total, falhando, tempo_s = _ler_junit(junit)
        percentual = json.loads(cobertura.read_text())["totals"]["percent_covered"]

    return {
        "testes_total": float(total),
        "testes_falhando": float(falhando),
        "cobertura_testes": float(percentual) / 100.0,
        "tempo_testes_s": tempo_s,
    }
