"""Testes do coletor de testes."""

import pytest

from vcm.coletores.testes import medir_testes


def _criar_projeto(raiz, com_testes=True):
    (raiz / "pyproject.toml").write_text('[project]\nname = "pacote"\nversion = "0.0.1"\n')
    (raiz / "src" / "pacote").mkdir(parents=True)
    (raiz / "src" / "pacote" / "__init__.py").write_text("def f():\n    return 1\n")
    if com_testes:
        (raiz / "tests").mkdir()
        (raiz / "tests" / "test_a.py").write_text(
            "def test_um():\n    assert True\n\n"
            "def test_dois():\n    assert 1 + 1 == 2\n\n"
            "def test_tres():\n    assert False\n"
        )


def test_sem_pasta_tests_retorna_zero(tmp_path):
    _criar_projeto(tmp_path, com_testes=False)
    assert medir_testes(tmp_path)["testes_total"] == 0


@pytest.mark.lento
def test_conta_testes_e_falhas(tmp_path):
    _criar_projeto(tmp_path)
    metricas = medir_testes(tmp_path)
    assert metricas["testes_total"] == 3
    assert metricas["testes_falhando"] == 1
    assert 0.0 <= metricas["cobertura_testes"] <= 1.0
    assert metricas["tempo_testes_s"] >= 0.0
    assert not (tmp_path / ".coverage").exists()
