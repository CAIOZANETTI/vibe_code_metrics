"""Testes do coletor de determinismo."""

from pathlib import Path

import pytest

from vcm.coletores.determinismo import medir_determinismo

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]


@pytest.mark.lento
def test_repositorio_real_e_deterministico():
    resultado = medir_determinismo(RAIZ_REPOSITORIO, repeticoes=2)
    assert resultado["frac_execucoes_identicas"] == 1.0
    assert resultado["repeticoes_determinismo"] == 2


@pytest.mark.lento
def test_projeto_sem_modulo_retorna_vazio(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.0.1"\n')
    assert medir_determinismo(tmp_path, repeticoes=1) == {}
