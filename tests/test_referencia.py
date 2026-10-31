"""Testes do conjunto de referência."""

import json
import subprocess
import sys

from vcm.referencia import casos, hash_referencia, medir_referencia


def test_casos_de_referencia_com_bytes():
    resultado = casos()
    assert set(resultado) == {
        "balanco",
        "perda_de_carga",
        "produto_matricial",
        "sistema_linear",
        "soma_acumulada",
    }
    assert all(isinstance(v, bytes) and v for v in resultado.values())


def test_hash_estavel_no_mesmo_processo():
    assert hash_referencia() == hash_referencia()
    assert len(hash_referencia()) == 64


def test_modulo_imprime_json_com_hash_tempo_e_ram():
    saida = subprocess.run(
        [sys.executable, "-m", "vcm.referencia"], capture_output=True, text=True, check=True
    )
    dados = json.loads(saida.stdout.strip().splitlines()[-1])
    assert dados["hash"] == hash_referencia()
    assert dados["tempo_ms"] > 0
    assert dados["pico_ram_mb"] > 0


def test_medir_referencia_traz_hash_tempo_e_ram():
    medida = medir_referencia()
    assert medida["hash"] == hash_referencia()
    assert medida["tempo_ms"] > 0
    assert medida["pico_ram_mb"] > 0
