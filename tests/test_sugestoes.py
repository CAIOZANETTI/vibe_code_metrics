"""Testes das correções sugeridas (vcm.sugestoes) e da integração no cartão e no rumo."""

import re

import pandas as pd

from vcm import cartao, sugestoes
from vcm import rumo as rumo_mod
from vcm import snapshot as snap
from vcm.balanco import balanco


def _resultado(antes: dict, depois: dict) -> dict:
    return {"tabela": balanco(pd.Series(antes), pd.Series(depois))}


def _metricas(resultado: dict, **kwargs) -> dict[str, dict]:
    return {s["metrica"]: s for s in sugestoes.do_balanco(resultado, **kwargs)}


def test_nada_sugerido_quando_tudo_verde_e_nada_piorou():
    base = {
        "testes_falhando": 0.0,
        "alertas_seguranca": 0.0,
        "frac_execucoes_identicas": 1.0,
        "complexidade_media": 3.0,
        "sloc_por_funcao": 10.0,
        "cobertura_testes": 0.9,
        "n_dependencias": 5.0,
        "tempo_p50_ms": 100.0,
    }
    assert sugestoes.do_balanco(_resultado(base, base)) == []


def test_testes_falhando_e_alta():
    r = _resultado({"testes_falhando": 0.0}, {"testes_falhando": 2.0})
    s = _metricas(r)["testes_falhando"]
    assert s["prioridade"] == "alta" and s["dimensao"] == "robusto"
    assert "corrigir os testes que falham" in s["o_que"]
    assert "testes_falhando = 2" in s["por_que"] and "piorou" in s["por_que"]
    assert s["agente_sugerido"] == "sonnet"


def test_determinismo_cita_blas_e_formata_em_ptbr():
    r = _resultado({"frac_execucoes_identicas": 1.0}, {"frac_execucoes_identicas": 0.5})
    s = _metricas(r)["frac_execucoes_identicas"]
    assert s["prioridade"] == "alta"
    assert "semente" in s["o_que"] and "BLAS" in s["o_que"]
    assert "0,500" in s["por_que"]


def test_complexidade_amarela_sem_raiz_so_a_acao():
    r = _resultado({"complexidade_media": 7.0}, {"complexidade_media": 7.0})
    s = _metricas(r)["complexidade_media"]
    assert s["prioridade"] == "média"
    assert s["o_que"] == "refatorar as funções mais complexas"
    assert "amarelo" in s["por_que"] and "= 7 (" in s["por_que"]


def test_complexidade_piorou_ainda_verde_tambem_sugere():
    r = _resultado({"complexidade_media": 2.0}, {"complexidade_media": 4.0})
    assert "complexidade_media" in _metricas(r)


def test_lista_das_cinco_piores_funcoes_com_radon(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = []\n')
    (tmp_path / "vcm.yaml").write_text("pastas_fonte: [src]\n")
    pasta = tmp_path / "src"
    pasta.mkdir()
    corpo = "".join(f"    if x == {i}:\n        return {i}\n" for i in range(1, 8))
    codigo = "".join(f"def f{n}(x):\n{corpo}    return 0\n\n" for n in range(1, 7))
    (pasta / "a.py").write_text(codigo + "class C:\n    def m(self):\n        return 1\n")
    (pasta / "b.py").write_text("def simples(x):\n    return x\n")
    r = _resultado({"complexidade_media": 7.0}, {"complexidade_media": 7.0})
    o_que = _metricas(r, raiz=tmp_path)["complexidade_media"]["o_que"]
    itens = o_que.split(": ", 1)[1].split("; ")
    assert len(itens) == 5
    assert itens[0] == "src/a.py f1 (8, B)"
    assert "simples" not in o_que and "C.m" not in o_que


def test_sloc_por_funcao_amarelo_sugere_quebrar():
    r = _resultado({"sloc_por_funcao": 30.0}, {"sloc_por_funcao": 30.0})
    s = _metricas(r)["sloc_por_funcao"]
    assert s["prioridade"] == "média" and "quebrar" in s["o_que"]


def test_cobertura_abaixo_do_verde_ou_piorou():
    r = _resultado({"cobertura_testes": 0.7}, {"cobertura_testes": 0.7})
    s = _metricas(r)["cobertura_testes"]
    assert s["prioridade"] == "média" and "acrescentar testes" in s["o_que"]
    assert "0,700" in s["por_que"]
    piorou = _resultado({"cobertura_testes": 0.95}, {"cobertura_testes": 0.85})
    assert "cobertura_testes" in _metricas(piorou)


def test_dependencia_nova_e_baixa_para_humano():
    r = _resultado({"n_dependencias": 5.0}, {"n_dependencias": 6.0})
    s = _metricas(r)["n_dependencias"]
    assert s["prioridade"] == "baixa" and s["agente_sugerido"] == "humano"
    assert "justificar" in s["o_que"]


def test_eficiencia_piorou_pede_perfilar():
    r = _resultado(
        {"tempo_p50_ms": 100.0, "pico_ram_mb": 50.0}, {"tempo_p50_ms": 200.0, "pico_ram_mb": 50.0}
    )
    achados = _metricas(r)
    assert set(achados) == {"tempo_p50_ms"}
    assert achados["tempo_p50_ms"]["prioridade"] == "baixa"
    assert "perfilar" in achados["tempo_p50_ms"]["o_que"]


def test_ordem_por_prioridade():
    r = _resultado(
        {"n_dependencias": 5.0, "complexidade_media": 7.0, "testes_falhando": 0.0},
        {"n_dependencias": 6.0, "complexidade_media": 7.0, "testes_falhando": 1.0},
    )
    prioridades = [s["prioridade"] for s in sugestoes.do_balanco(r)]
    assert prioridades == ["alta", "média", "baixa"]


def test_alertas_do_bandit_com_eval(tmp_path):
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\ndependencies = []\n')
    (tmp_path / "vcm.yaml").write_text("pastas_fonte: [src]\n")
    pasta = tmp_path / "src"
    pasta.mkdir()
    (pasta / "perigo.py").write_text("def f(texto):\n    return eval(texto)\n")
    r = _resultado({"alertas_seguranca": 0.0}, {"alertas_seguranca": 1.0})
    s = _metricas(r, raiz=tmp_path)["alertas_seguranca"]
    assert s["prioridade"] == "alta"
    assert "src/perigo.py:2 B307" in s["o_que"]
    sem_raiz = _metricas(r)["alertas_seguranca"]
    assert sem_raiz["o_que"] == "corrigir os alertas de segurança do bandit"


def test_do_rumo_por_tipo_de_desvio():
    desvios = [
        {"tipo": "fora do plano", "etapa": None, "detalhe": "a.py alterado"},
        {"tipo": "estouro", "etapa": "E1", "detalhe": "tokens real é 2,0× o estimado"},
        {"tipo": "parada", "etapa": "E2", "detalhe": "em andamento há 3,0× a estimativa"},
        {"tipo": "entregável ausente", "etapa": "E3", "detalhe": "marcada como feita sem: x"},
    ]
    saida = sugestoes.do_rumo(desvios)
    por_tipo = {s["por_que"].split(":")[0]: s for s in saida}
    assert "etapa nova" in por_tipo["fora do plano"]["o_que"]
    assert "dividir a etapa" in por_tipo["estouro"]["o_que"]
    assert "bloqueio" in por_tipo["parada"]["o_que"]
    assert "criar o entregável" in por_tipo["entregável ausente"]["o_que"]
    assert [s["prioridade"] for s in saida] == ["alta", "alta", "média", "média"]
    assert sugestoes.do_rumo([]) == []


def test_markdown_tem_tabela_e_frase_fixa():
    texto = sugestoes.markdown(
        [
            {
                "prioridade": "alta",
                "dimensao": "robusto",
                "metrica": "m",
                "o_que": "faz | isso",
                "por_que": "porque",
                "agente_sugerido": "sonnet",
            }
        ]
    )
    assert texto.startswith("### Correções sugeridas")
    assert "| alta | faz \\| isso | porque | sonnet |" in texto
    assert "nada foi alterado. Aplicar exige aprovação humana." in texto
    assert "Nenhuma correção" in sugestoes.markdown([])


def _retro(antes: dict, depois: dict) -> dict:
    return snap.retrospectiva(
        pd.Series({"commit": "a" * 40, **antes}),
        pd.Series({"commit": "b" * 40, "mensagem": "m", **depois}),
    )


def test_cartao_markdown_e_html_trazem_a_secao():
    r = _retro({"complexidade_media": 7.0}, {"complexidade_media": 7.0})
    md = cartao.markdown(r)
    assert "### Correções sugeridas" in md
    assert "refatorar as funções mais complexas" in md
    pagina = cartao.html(r)
    assert "Correções sugeridas" in pagina and "refatorar as funções mais complexas" in pagina
    assert "Aplicar exige aprovação humana" in pagina
    secao = pagina.split("Correções sugeridas", 1)[1].split("<h2>", 1)[0]
    assert "<script" not in secao


def test_cartao_verde_mostra_nenhuma_correcao():
    r = _retro({"complexidade_media": 3.0}, {"complexidade_media": 3.0})
    assert "Nenhuma correção sugerida" in cartao.markdown(r)


def test_rumo_markdown_e_html_trazem_a_secao(tmp_path):
    from test_rumo import _exemplo

    rumo, prog, real, _ = _exemplo(tmp_path)
    desv = [{"tipo": "estouro", "etapa": "E1", "detalhe": "tokens real é 2,0× o estimado"}]
    texto = rumo_mod.markdown(rumo, prog, real, desv)
    assert "### Correções sugeridas" in texto and "dividir a etapa" in texto
    pagina = rumo_mod.html(rumo, prog, real, desv)
    assert "Correções sugeridas" in pagina and "dividir a etapa" in pagina
    scripts = re.findall(r"<script[^>]*>.*?</script>", pagina, flags=re.DOTALL)
    assert all("plotly" in s.lower() for s in scripts)
