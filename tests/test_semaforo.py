import re

import numpy as np
import pandas as pd

from vcm import cartao, semaforo
from vcm import snapshot as snap


def _estado(**valores):
    return semaforo.avaliar_estado(pd.Series(valores, dtype=float))


def _resultado(**pares):
    return snap.retrospectiva(
        pd.Series({"commit": "a" * 40, **{k: v[0] for k, v in pares.items()}}),
        pd.Series({"commit": "b" * 40, "mensagem": "m", **{k: v[1] for k, v in pares.items()}}),
    )


def test_cores_com_valores_conhecidos():
    e = _estado(
        testes_falhando=0,
        alertas_seguranca=2,
        frac_execucoes_identicas=0.9,
        cobertura_testes=0.85,
        complexidade_media=7.0,
        sloc_por_funcao=60.0,
        sloc=1000.0,
        mutation_score=0.5,
    )
    assert e.loc["testes_falhando", "cor"] == "verde"
    assert e.loc["alertas_seguranca", "cor"] == "vermelho"
    assert e.loc["frac_execucoes_identicas", "cor"] == "amarelo"
    assert e.loc["cobertura_testes", "cor"] == "verde"
    assert e.loc["complexidade_media", "cor"] == "amarelo"
    assert e.loc["sloc_por_funcao", "cor"] == "vermelho"
    assert e.loc["sloc", "cor"] == "cinza"  # informativa
    assert e.loc["mutation_score", "cor"] == "cinza"  # sem limite
    assert "verde ≤ 5,00" in e.loc["complexidade_media", "regra"]


def test_nan_e_cinza_e_limites_extras():
    assert _estado(cobertura_testes=np.nan).loc["cobertura_testes", "cor"] == "cinza"
    lim = semaforo.carregar_limites({"cobertura_testes": {"verde": 0.95}})
    e = semaforo.avaliar_estado(pd.Series({"cobertura_testes": 0.85}), lim)
    assert e.loc["cobertura_testes", "cor"] == "amarelo"
    assert semaforo.carregar_limites()["cobertura_testes"]["verde"] == 0.80


def test_pior_cor_por_dimensao():
    e = _estado(testes_falhando=0, cobertura_testes=0.7, alertas_seguranca=1, sloc=10.0)
    cores = semaforo.cores_por_dimensao(e)
    assert cores["robusto"] == "vermelho"
    assert cores["enxuto"] == "cinza"
    assert cores["eficiente"] == "cinza"
    assert list(cores.index) == semaforo.DIMENSOES
    e2 = _estado(testes_falhando=0, cobertura_testes=0.7)
    assert semaforo.cores_por_dimensao(e2)["robusto"] == "amarelo"


def test_indices_media_geometrica_e_orientacao():
    t = _resultado(
        sloc_por_funcao=(100.0, 50.0), complexidade_media=(4.0, 4.0), sloc=(10.0, 999.0)
    )["tabela"]
    idx = semaforo.indices_iteracao(t).set_index("dimensao")
    # menor é melhor: razão 0,5 vira 2,0; complexidade 1,0; geométrica = raiz de 2
    assert np.isclose(idx.loc["enxuto", "indice"], np.sqrt(2))
    assert np.isnan(idx.loc["eficiente", "indice"])
    assert idx.loc["eficiente", "indice_desenho"] == 1.0


def test_indices_antes_zero_limite_e_informativas():
    t = _resultado(
        testes_falhando=(0.0, 0.0),  # 0 -> 0 conta 1,0
        alertas_seguranca=(0.0, 3.0),  # razão indefinida: ignorada
        cobertura_testes=(0.2, 0.8),  # x4
        sloc=(10.0, 20.0),  # informativa: ignorada
    )["tabela"]
    idx = semaforo.indices_iteracao(t).set_index("dimensao")
    assert np.isclose(idx.loc["robusto", "indice"], 2.0)  # sqrt(1,0 * 4)
    assert idx.loc["robusto", "indice_desenho"] == semaforo.INDICE_MAXIMO
    assert np.isnan(idx.loc["enxuto", "indice"])  # só informativa


def test_indice_piora_limitado_embaixo():
    t = _resultado(cobertura_testes=(0.8, 0.1))["tabela"]
    idx = semaforo.indices_iteracao(t).set_index("dimensao")
    assert np.isclose(idx.loc["robusto", "indice"], 0.125)
    assert idx.loc["robusto", "indice_desenho"] == semaforo.INDICE_MINIMO


def test_figura_com_dois_tracos_e_rotulos():
    t = _resultado(testes_falhando=(0.0, 2.0), sloc_por_funcao=(30.0, 20.0))["tabela"]
    estado = semaforo.avaliar_estado(t["depois"])
    cores = semaforo.cores_por_dimensao(estado)
    fig = semaforo.figura_radar(semaforo.indices_iteracao(t), cores)
    assert len(fig.data) == 2
    assert all(tr.type == "scatterpolar" for tr in fig.data)
    assert set(fig.data[0].r) == {1.0}
    assert "robusto 🔴" in fig.data[1].theta
    assert "enxuto 🟢" in fig.data[1].theta


def test_cartao_html_tem_radar_e_cores_sem_calculo_em_js(tmp_path):
    r = _resultado(testes_falhando=(0.0, 2.0), sloc_por_funcao=(30.0, 20.0))
    h = cartao.html(r)
    assert "plotly-graph-div" in h and "scatterpolar" in h
    assert "bolinha vermelho" in h and "bolinha verde" in h
    assert "robusto \\ud83d\\udd34" in h  # Plotly escapa o emoji no JSON
    # os únicos <script> são os do Plotly (CDN e a chamada de desenho com dados prontos)
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", h, flags=re.DOTALL)
    assert scripts
    for corpo in scripts:
        assert corpo.strip() == "" or "Plotly" in corpo or "PLOTLYENV" in corpo
    assert "cdn.plot.ly" in h
    md = cartao.markdown(r)
    assert "🔴" in md and "🟢" in md and "⚪" in md


def test_contexto_aceita_limites_do_projeto():
    r = _resultado(sloc_por_funcao=(30.0, 20.0))
    padrao = cartao.contexto(r)["semaforo"]["metricas"][0]
    assert padrao["cor"] == "verde"
    lim = semaforo.carregar_limites({"sloc_por_funcao": {"verde": 10, "amarelo": 15}})
    assert cartao.contexto(r, lim)["semaforo"]["metricas"][0]["cor"] == "vermelho"
