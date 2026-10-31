"""Testes do coletor de determinismo."""

from pathlib import Path

import pytest

from vcm.coletores.determinismo import _interpretar_saida, medir_determinismo

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]


def _mini_projeto(raiz: Path, corpo_script: str, repeticoes: int = 3) -> None:
    """Projeto mínimo sem dependências, com um script de referência e um vcm.yaml."""
    (raiz / "pyproject.toml").write_text(
        '[project]\nname = "mini"\nversion = "0.0.1"\nrequires-python = ">=3.11"\n'
        "[tool.uv]\npackage = false\n"
    )
    (raiz / "ref.py").write_text(corpo_script, encoding="utf-8")
    (raiz / "vcm.yaml").write_text(
        f"referencia:\n  comando: [python, ref.py]\n  repeticoes: {repeticoes}\n",
        encoding="utf-8",
    )


@pytest.mark.lento
def test_repositorio_real_e_deterministico():
    resultado = medir_determinismo(RAIZ_REPOSITORIO, repeticoes=2)
    assert resultado["frac_execucoes_identicas"] == 1.0
    assert resultado["repeticoes_determinismo"] == 2
    assert resultado["tempo_referencia_ms"] > 0
    assert resultado["pico_ram_mb"] > 0


def test_sem_comando_de_referencia_retorna_vazio(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.0.1"\n')
    assert medir_determinismo(tmp_path, repeticoes=1) == {}


def test_interpretar_saida_json_e_so_hash():
    assert _interpretar_saida('ruído\n{"hash": "abc", "tempo_ms": 1.5}\n\n') == (
        "abc",
        {"hash": "abc", "tempo_ms": 1.5},
    )
    assert _interpretar_saida("ruído\nabc123\n\n") == ("abc123", {})
    with pytest.raises(RuntimeError, match="não imprimiu"):
        _interpretar_saida("\n  \n")


@pytest.mark.lento
def test_protocolo_json(tmp_path):
    _mini_projeto(
        tmp_path,
        "import json\nprint('ruído')\n"
        "print(json.dumps({'hash': 'h', 'tempo_ms': 10.0, 'pico_ram_mb': 50.0}))\n",
    )
    resultado = medir_determinismo(tmp_path)  # repetições e comando vêm do vcm.yaml
    assert resultado["frac_execucoes_identicas"] == 1.0
    assert resultado["repeticoes_determinismo"] == 3
    assert resultado["tempo_referencia_ms"] == 10.0
    assert resultado["pico_ram_mb"] == 50.0


@pytest.mark.lento
def test_protocolo_so_hash(tmp_path):
    _mini_projeto(tmp_path, "print('abc123')\n")
    resultado = medir_determinismo(tmp_path, repeticoes=2)
    assert resultado == {
        "hash_referencia": "abc123",
        "frac_execucoes_identicas": 1.0,
        "repeticoes_determinismo": 2.0,
    }


@pytest.mark.lento
def test_hash_variavel_reduz_fracao_e_agrega_tempo_e_ram(tmp_path):
    # O hash muda via arquivo contador; tempo é a mediana, RAM o máximo.
    _mini_projeto(
        tmp_path,
        "import json, pathlib\n"
        "c = pathlib.Path('contador.txt')\n"
        "n = int(c.read_text()) if c.exists() else 0\n"
        "c.write_text(str(n + 1))\n"
        "print(json.dumps({'hash': 'a' if n < 2 else 'b', 'tempo_ms': [1.0, 9.0, 5.0, 7.0][n],"
        " 'pico_ram_mb': [10.0, 40.0, 20.0, 30.0][n]}))\n",
    )
    resultado = medir_determinismo(tmp_path, repeticoes=4)
    assert resultado["frac_execucoes_identicas"] == 0.5
    assert resultado["tempo_referencia_ms"] == 6.0  # mediana de 1, 9, 5, 7
    assert resultado["pico_ram_mb"] == 40.0


@pytest.mark.lento
def test_modulo_inexistente_retorna_vazio(tmp_path):
    _mini_projeto(tmp_path, "")
    resultado = medir_determinismo(
        tmp_path, repeticoes=1, comando=["python", "-m", "pacote_que_nao_existe.ref"]
    )
    assert resultado == {}
