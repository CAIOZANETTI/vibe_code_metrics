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


def test_dependencias_extras(tmp_path):
    assert carregar_config(tmp_path).dependencias_extras == ()
    (tmp_path / "vcm.yaml").write_text("dependencias_extras: [pymupdf, rasterio]\n")
    assert carregar_config(tmp_path).dependencias_extras == ("pymupdf", "rasterio")


@pytest.mark.parametrize("valor", ["pymupdf", "[1, 2]", "[a, '']"])
def test_dependencias_extras_invalidas(tmp_path, valor):
    (tmp_path / "vcm.yaml").write_text(f"dependencias_extras: {valor}\n")
    with pytest.raises(ValueError, match="dependencias_extras"):
        carregar_config(tmp_path)


@pytest.mark.parametrize(
    ("conteudo", "mensagem"),
    [
        ("a: [\n", "vcm.yaml: YAML inválido:"),
        ("- lista\n", "vcm.yaml: o conteúdo deve ser um mapeamento (chave: valor)"),
        ("projeto: ''\n", "vcm.yaml: 'projeto' deve ser um texto não vazio"),
        ("projeto: 7\n", "vcm.yaml: 'projeto' deve ser um texto não vazio"),
        ("pastas_fonte: [1]\n", "vcm.yaml: 'pastas_fonte' deve ser uma lista não vazia de textos"),
        ("pastas_fonte: []\n", "vcm.yaml: 'pastas_fonte' deve ser uma lista não vazia de textos"),
        ("pasta_testes: ''\n", "vcm.yaml: 'pasta_testes' deve ser um texto não vazio"),
        ("referencia: [1]\n", "vcm.yaml: 'referencia' deve ser um mapeamento"),
        (
            "referencia: {comando: []}\n",
            "vcm.yaml: 'referencia.comando' deve ser uma lista não vazia de textos",
        ),
        (
            "referencia: {repeticoes: true}\n",
            "vcm.yaml: 'referencia.repeticoes' deve ser um inteiro >= 1",
        ),
        (
            "referencia: {repeticoes: 2.5}\n",
            "vcm.yaml: 'referencia.repeticoes' deve ser um inteiro >= 1",
        ),
        ("limites: texto\n", "vcm.yaml: 'limites' deve ser um mapeamento"),
        (
            "dependencias_extras: [a, 3]\n",
            "vcm.yaml: 'dependencias_extras' deve ser uma lista de textos",
        ),
    ],
)
def test_mensagens_exatas_de_erro(tmp_path, conteudo, mensagem):
    (tmp_path / "vcm.yaml").write_text(conteudo, encoding="utf-8")
    with pytest.raises(ValueError) as erro:
        carregar_config(tmp_path)
    assert mensagem in str(erro.value)


def test_arquivo_vazio_e_valores_nulos_usam_padroes(tmp_path):
    (tmp_path / "vcm.yaml").write_text("", encoding="utf-8")
    vazio = carregar_config(tmp_path)
    assert vazio.projeto == tmp_path.resolve().name
    assert vazio.pasta_testes == "tests"
    assert vazio.comando_referencia is None
    assert vazio.repeticoes == 5
    assert vazio.limites == {}
    assert vazio.dependencias_extras == ()
    (tmp_path / "vcm.yaml").write_text("referencia:\nlimites:\npastas_fonte:\n", encoding="utf-8")
    assert carregar_config(tmp_path) == vazio


def test_valores_validos_sao_convertidos(tmp_path):
    (tmp_path / "vcm.yaml").write_text(
        "pastas_fonte: [a, b]\nreferencia: {comando: [x, y], repeticoes: 3}\n"
        "limites: {cobertura: 1}\ndependencias_extras: []\n",
        encoding="utf-8",
    )
    config = carregar_config(tmp_path)
    assert config.pastas_fonte == ("a", "b")
    assert config.comando_referencia == ("x", "y")
    assert config.repeticoes == 3
    assert config.limites == {"cobertura": 1}
    assert config.dependencias_extras == ()
