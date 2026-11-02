"""Testes do formulário padrão de interação."""

import pandas as pd

from vcm import formulario

RUMO = {
    "objetivo": "Calcular a perda de carga da adutora",
    "etapas": [
        {"id": "E1", "nome": "Darcy", "status": "feito", "agente": "sonnet", "depende_de": []},
        {"id": "E2", "nome": "Hazen", "status": "fazendo", "agente": "sonnet", "depende_de": []},
        {"id": "E3", "nome": "Docs", "status": "a_fazer", "agente": "haiku", "depende_de": ["E1"]},
        {"id": "E4", "nome": "PR", "status": "a_fazer", "agente": "opus", "depende_de": ["E2"]},
    ],
    "historico": [],
}
PROG = {"percentual": 50.0, "por_status": {}, "proxima": "E3"}


def test_formulario_tem_todos_os_campos_e_os_dados_preenchidos():
    real = pd.DataFrame({"id": ["E1", "E2"], "custo_usd": [1.25, 0.75]})
    texto = formulario.preencher(RUMO, PROG, real, [], None, projeto="adutora")
    assert formulario.campos_faltando(texto) == []
    assert "### Interação · adutora" in texto
    assert "Calcular a perda de carga da adutora" in texto
    assert "`█████░░░░░ 50%`" in texto
    assert "em andamento: E2 Hazen" in texto
    assert "US$ 2,00" in texto
    assert "- nada no momento" in texto


def test_agentes_listam_etapas_em_andamento_e_disponiveis():
    texto = formulario.preencher(RUMO, PROG)
    assert "| sonnet | E2 Hazen | trabalhando |" in texto
    assert "| haiku | E3 Docs | a seguir |" in texto
    assert "E4 PR" not in texto  # depende de E2, que não terminou


def test_desvios_viram_decisoes_do_humano():
    desv = [{"tipo": "estouro", "etapa": "E2", "detalhe": "2,1× os tokens"}]
    texto = formulario.preencher(RUMO, PROG, desv=desv)
    assert "- estouro: E2: 2,1× os tokens" in texto


def test_sem_custo_medido_nao_mostra_gasto():
    real = pd.DataFrame({"id": ["E1"], "custo_usd": [float("nan")]})
    assert "US$" not in formulario.preencher(RUMO, PROG, real)


def test_campos_faltando_aponta_o_que_falta():
    assert formulario.campos_faltando("**O que estou fazendo:** x") == [
        "Onde estamos",
        "Agentes",
        "Precisa de você",
        "Campo livre",
    ]
