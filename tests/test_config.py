"""Testes da leitura de vcm.yaml e da autodetecção."""

from pathlib import Path

import pytest

from vcm.config import Config, carregar_config

RAIZ_REPOSITORIO = Path(__file__).resolve().parents[1]


def test_sem_yaml_usa_src_se_existir(tmp_path):
    (tmp_path / "src").mkdir()
    config = carregar_config(tmp_path)
    assert config == Config(
        projeto=tmp_path.name,
        pastas_fonte=("src",),
        pasta_testes="tests",
        comando_referencia=None,
        repeticoes=5,
        limites={},
    )


def test_sem_yaml_autodetecta_pacote_na_raiz(tmp_path):
    for nome in ("meupacote", "tests", ".venv", "outro"):
        (tmp_path / nome).mkdir()
        (tmp_path / nome / "__init__.py").write_text("")
    (tmp_path / "semInit").mkdir()
    assert carregar_config(tmp_path).pastas_fonte == ("meupacote", "outro")


def test_sem_yaml_nem_pacote_usa_raiz(tmp_path):
    assert carregar_config(tmp_path).pastas_fonte == (".",)


def test_yaml_completo(tmp_path):
    (tmp_path / "vcm.yaml").write_text(
        "projeto: demo\n"
        "pastas_fonte: [lib, app]\n"
        "pasta_testes: testes\n"
        "referencia:\n"
        "  comando: [python, -m, demo.ref]\n"
        "  repeticoes: 3\n"
        "limites: {sloc: 100}\n",
        encoding="utf-8",
    )
    config = carregar_config(tmp_path)
    assert config.projeto == "demo"
    assert config.pastas_fonte == ("lib", "app")
    assert config.pasta_testes == "testes"
    assert config.comando_referencia == ("python", "-m", "demo.ref")
    assert config.repeticoes == 3
    assert config.limites == {"sloc": 100}


def test_yaml_parcial_completa_com_padroes(tmp_path):
    (tmp_path / "vcm.yaml").write_text("projeto: parcial\n", encoding="utf-8")
    config = carregar_config(tmp_path)
    assert config.projeto == "parcial"
    assert config.pastas_fonte == (".",)
    assert config.repeticoes == 5


@pytest.mark.parametrize(
    ("conteudo", "trecho"),
    [
        ("pastas_fonte: src\n", "pastas_fonte"),
        ("pastas_fonte: []\n", "pastas_fonte"),
        ("pasta_testes: 3\n", "pasta_testes"),
        ("projeto: 7\n", "projeto"),
        ("referencia: {repeticoes: 0}\n", "repeticoes"),
        ("referencia: {repeticoes: abc}\n", "repeticoes"),
        ("referencia: {comando: python}\n", "referencia.comando"),
        ("limites: [1]\n", "limites"),
        ("- lista\n", "mapeamento"),
        ("a: [\n", "YAML inválido"),
    ],
)
def test_yaml_invalido_gera_erro_em_portugues(tmp_path, conteudo, trecho):
    (tmp_path / "vcm.yaml").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError, match=trecho):
        carregar_config(tmp_path)


def test_vcm_yaml_do_repositorio():
    config = carregar_config(RAIZ_REPOSITORIO)
    assert config.pastas_fonte == ("src",)
    assert config.comando_referencia == ("python", "-m", "vcm.referencia")
