"""Testes do protótipo T005 (perda de carga)."""

import numpy as np
import pandas as pd
import pytest

from vcm.prototipos.perda_de_carga import (
    COLUNAS_SAIDA,
    alternativa_hibrida,
    alternativa_numpy,
    alternativa_polars,
    gabarito,
)
from vcm.prototipos.perda_de_carga.dados import gerar_perfil
from vcm.prototipos.perda_de_carga.relatorio import gerar_relatorio, montar_leitura
from vcm.prototipos.perda_de_carga.rodar import rodar

ALTERNATIVAS = [alternativa_numpy, alternativa_polars, alternativa_hibrida]


def test_perfil_soma_5000_m_e_e_deterministico():
    perfil = gerar_perfil(1000)
    assert perfil["comprimento_m"].sum() == pytest.approx(5000.0, abs=1e-9)
    assert (perfil["comprimento_m"] > 0).all()
    assert perfil["cota_terreno_m"].between(700, 760).all()
    assert set(perfil["diametro_m"]) <= {0.300, 0.350, 0.400}
    assert perfil["coef_c"].between(120, 140).all()
    pd.testing.assert_frame_equal(perfil, gerar_perfil(1000))
    assert not perfil.equals(gerar_perfil(1000, semente=7))


@pytest.mark.parametrize("n_trechos", [100, 1000])
@pytest.mark.parametrize("modulo", ALTERNATIVAS)
def test_alternativas_batem_com_o_gabarito(modulo, n_trechos):
    perfil = gerar_perfil(n_trechos)
    argumentos = (perfil, perfil.attrs["vazao_m3s"], perfil.attrs["cota_reservatorio_m"])
    esperado = gabarito.calcular(*argumentos)
    obtido = modulo.calcular(*argumentos)
    for coluna in COLUNAS_SAIDA:
        np.testing.assert_allclose(obtido[coluna], esperado[coluna], rtol=0, atol=1e-9)


def test_soma_por_trechos_bate_com_formula_fechada_uniforme():
    n_trechos, comprimento_total_m = 1000, 5000.0
    vazao_m3s, coef_c, diametro_m = 0.180, 130.0, 0.350
    perfil = gerar_perfil(n_trechos).assign(coef_c=coef_c, diametro_m=diametro_m)
    saida = gabarito.calcular(perfil, vazao_m3s, 810.0)
    fechada_m = gabarito.perda_total_uniforme_m(comprimento_total_m, vazao_m3s, coef_c, diametro_m)
    assert saida["perda_acumulada_m"].iloc[-1] == pytest.approx(fechada_m, rel=0, abs=1e-9)
    for modulo in ALTERNATIVAS:
        obtido = modulo.calcular(perfil, vazao_m3s, 810.0)
        assert obtido["perda_acumulada_m"].iloc[-1] == pytest.approx(fechada_m, rel=0, abs=1e-9)


def test_relatorio_gera_html_para_tamanhos_pequenos(tmp_path):
    pasta = tmp_path / "runs"
    execucoes, resumo = rodar(tamanhos=(50, 200), repeticoes=2, pasta_saida=pasta)
    assert len(execucoes) == 3 * 2 * 2
    assert resumo["deterministico"].all()
    assert (resumo["erro_max_abs_m"] <= 1e-9).all()
    assert "mais rápida" in montar_leitura(resumo)[0]
    caminho = gerar_relatorio(pasta, tmp_path / "T005.html", n_perfil=200)
    html = caminho.read_text(encoding="utf-8")
    assert "Leitura dos resultados" in html
    assert "H1" in html and "plotly" in html.lower()
