"""Testes do conjunto de referência."""

import subprocess
import sys

from vcm.referencia import casos, hash_referencia


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


def test_modulo_imprime_so_o_hash():
    saida = subprocess.run(
        [sys.executable, "-m", "vcm.referencia"], capture_output=True, text=True, check=True
    )
    assert saida.stdout.strip() == hash_referencia()
