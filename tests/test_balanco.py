import pandas as pd
import pytest

from vcm.balanco import Decisao, balanco, convergiu, decidir, respostas


def _s(**kw):
    return pd.Series(kw, dtype=float)


def test_melhora_sem_perda_mantem():
    t = balanco(_s(tempo_p50_ms=100, sloc_por_funcao=12), _s(tempo_p50_ms=80, sloc_por_funcao=12))
    assert t.loc["tempo_p50_ms", "veredito"] == "melhorou"
    assert t.loc["sloc_por_funcao", "veredito"] == "igual"
    assert decidir(t) is Decisao.MANTER


def test_variacao_dentro_do_ruido_e_igual():
    # tempo_p50_ms tem ruído de 5%: 3% de melhora não conta
    t = balanco(_s(tempo_p50_ms=100), _s(tempo_p50_ms=97))
    assert t.loc["tempo_p50_ms", "veredito"] == "igual"
    assert decidir(t) is Decisao.SEM_GANHO


def test_eliminatoria_piorou_reverte_mesmo_com_ganhos():
    t = balanco(
        _s(tempo_p50_ms=100, testes_falhando=0),
        _s(tempo_p50_ms=10, testes_falhando=1),
    )
    assert decidir(t) is Decisao.REVERTER


def test_troca_pede_decisao_humana():
    t = balanco(
        _s(tempo_p50_ms=100, complexidade_media=3.0),
        _s(tempo_p50_ms=70, complexidade_media=4.0),
    )
    assert decidir(t) is Decisao.DECISAO_HUMANA
    r = respostas(t)
    assert r["eficiente"] == "sim"
    assert r["enxuto"] == "não"


def test_antes_zero_usa_variacao_absoluta():
    t = balanco(_s(alertas_seguranca=0), _s(alertas_seguranca=2))
    assert t.loc["alertas_seguranca", "variacao_pct"] == pytest.approx(200.0)
    assert t.loc["alertas_seguranca", "veredito"] == "piorou"


def test_metricas_desconhecidas_sao_ignoradas_e_sem_comum_falha():
    t = balanco(_s(sloc_por_funcao=10, xyz=1), _s(sloc_por_funcao=9, xyz=2))
    assert list(t.index) == ["sloc_por_funcao"]
    with pytest.raises(ValueError):
        balanco(_s(xyz=1), _s(xyz=2))


def test_convergencia():
    assert not convergiu(pd.Series([3, 0]))
    assert convergiu(pd.Series([3, 2, 0, 0, -1]))
    assert not convergiu(pd.Series([0, 0, 1]))


def test_metrica_informativa_nao_e_julgada():
    t = balanco(_s(sloc=100, sloc_por_funcao=10), _s(sloc=300, sloc_por_funcao=9))
    assert t.loc["sloc", "veredito"] == "info"
    assert decidir(t) is Decisao.MANTER
    assert respostas(t)["enxuto"] == "sim"
