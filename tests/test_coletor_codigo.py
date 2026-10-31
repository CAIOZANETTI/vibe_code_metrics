from pathlib import Path

from vcm.coletores.codigo import medir_codigo

PYPROJECT = """\
[project]
name = "mini"
version = "0.1.0"
dependencies = ["numpy>=2.0", "pandas>=2.2"]
"""

# complexidade: simples = 1; ramificada = 1 + if + elif + for = 4
MODULO = """\
def simples(x):
    return x


def ramificada(valores):
    total = 0
    for v in valores:
        if v > 0:
            total += v
        elif v < 0:
            total -= v
    return total
"""

MODULO_INSEGURO = """\
def avaliar(texto):
    return eval(texto)
"""


def _criar_projeto(raiz: Path) -> None:
    (raiz / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")
    (raiz / "src").mkdir()
    (raiz / "src" / "modulo.py").write_text(MODULO, encoding="utf-8")


def test_valores_do_mini_projeto(tmp_path):
    _criar_projeto(tmp_path)
    metricas = medir_codigo(tmp_path)
    assert metricas["sloc"] == 10.0
    assert metricas["complexidade_media"] == (1 + 4) / 2
    assert metricas["n_dependencias"] == 2.0
    assert metricas["alertas_seguranca"] == 0.0
    assert metricas["n_arquivos_py"] == 1.0
    assert metricas["arquivos_com_erro"] == 0.0
    assert all(isinstance(valor, float) for valor in metricas.values())


def test_bandit_conta_eval_como_alerta(tmp_path):
    _criar_projeto(tmp_path)
    (tmp_path / "src" / "inseguro.py").write_text(MODULO_INSEGURO, encoding="utf-8")
    metricas = medir_codigo(tmp_path)
    # eval (B307) tem severidade MEDIUM no bandit
    assert metricas["alertas_seguranca"] == 1.0
    assert metricas["n_arquivos_py"] == 2.0


def test_ignora_venv_e_pycache_e_conta_arquivos_com_erro(tmp_path):
    _criar_projeto(tmp_path)
    (tmp_path / "src" / ".venv").mkdir()
    (tmp_path / "src" / ".venv" / "lixo.py").write_text(MODULO, encoding="utf-8")
    (tmp_path / "src" / "__pycache__").mkdir()
    (tmp_path / "src" / "__pycache__" / "lixo.py").write_text(MODULO, encoding="utf-8")
    (tmp_path / "src" / "quebrado.py").write_text("def (:\n", encoding="utf-8")
    metricas = medir_codigo(tmp_path)
    assert metricas["n_arquivos_py"] == 1.0
    assert metricas["arquivos_com_erro"] == 1.0
    assert metricas["sloc"] == 10.0


def test_metodos_de_classe_entram_na_complexidade(tmp_path):
    (tmp_path / "src").mkdir()
    codigo = (
        "class A:\n    def m(self, x):\n        if x:\n            return 1\n        return 2\n"
    )
    (tmp_path / "src" / "a.py").write_text(codigo, encoding="utf-8")
    assert medir_codigo(tmp_path)["complexidade_media"] == 2.0


def test_diretorio_sem_pyproject_e_sem_fonte(tmp_path):
    metricas = medir_codigo(tmp_path)
    assert metricas == {
        "sloc": 0.0,
        "complexidade_media": 0.0,
        "n_dependencias": 0.0,
        "alertas_seguranca": 0.0,
        "n_arquivos_py": 0.0,
        "arquivos_com_erro": 0.0,
    }


def test_sem_pyproject_mas_com_codigo(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "modulo.py").write_text(MODULO, encoding="utf-8")
    metricas = medir_codigo(tmp_path)
    assert metricas["n_dependencias"] == 0.0
    assert metricas["n_arquivos_py"] == 1.0


def test_pastas_fonte_personalizadas(tmp_path):
    _criar_projeto(tmp_path)
    (tmp_path / "lib").mkdir()
    (tmp_path / "lib" / "outro.py").write_text(MODULO, encoding="utf-8")
    assert medir_codigo(tmp_path, ("src", "lib"))["n_arquivos_py"] == 2.0
    assert medir_codigo(tmp_path, ("lib",))["n_arquivos_py"] == 1.0
