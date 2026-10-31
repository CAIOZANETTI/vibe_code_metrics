"""Testes do prefixo de execução do projeto medido."""

from vcm.coletores.ambiente import prefixo_uv
from vcm.coletores.codigo import medir_codigo


def test_prefixo_com_pyproject(tmp_path):
    (tmp_path / "pyproject.toml").write_text("")
    assert prefixo_uv(tmp_path, ("coverage",)) == [
        "uv", "run", "--directory", str(tmp_path), "--with", "coverage",
    ]  # fmt: skip


def test_prefixo_so_com_requirements(tmp_path):
    (tmp_path / "requirements.txt").write_text("numpy\n")
    assert prefixo_uv(tmp_path, ("pytest",)) == [
        "uv", "run", "--no-project", "--directory", str(tmp_path),
        "--with-requirements", "requirements.txt", "--with", "pytest",
    ]  # fmt: skip


def test_prefixo_sem_nenhum(tmp_path):
    assert prefixo_uv(tmp_path, ("a", "b")) == [
        "uv", "run", "--no-project", "--directory", str(tmp_path), "--with", "a", "--with", "b",
    ]  # fmt: skip


def test_n_dependencias_por_requirements(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "# comentário\nnumpy>=1.0\n\n  # outro\npandas  # inline\n-r outro.txt\n--index-url x\n"
    )
    (tmp_path / "pkg").mkdir()
    (tmp_path / "pkg" / "__init__.py").write_text("x = 1\n")
    assert medir_codigo(tmp_path)["n_dependencias"] == 2.0
