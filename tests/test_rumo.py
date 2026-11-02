"""Testes do rumo do desenvolvimento (WBS × realizado)."""

from __future__ import annotations

import os
import re
import subprocess
from datetime import UTC, datetime

import pandas as pd
import pytest
import yaml

from vcm import cli
from vcm import rumo as mod
from vcm.coletores import sessoes


def _etapa(id_, **extra):
    base = {
        "id": id_,
        "nome": f"Etapa {id_}",
        "entregaveis": [f"{id_.lower()}.txt"],
        "depende_de": [],
        "agente": "sonnet",
        "estimativa_min": 60,
        "estimativa_tokens": 1000,
        "status": "a_fazer",
        "inicio": None,
        "fim": None,
    }
    base.update(extra)
    return base


def _gravar(tmp_path, etapas, **extra):
    dado = {"objetivo": "Meta", "criterio_de_pronto": ["ok"], "base": None, "etapas": etapas}
    dado.update(extra)
    arquivo = tmp_path / "rumo.yaml"
    arquivo.write_text(yaml.safe_dump(dado, sort_keys=False, allow_unicode=True), encoding="utf-8")
    return arquivo


def test_validacao_erros(tmp_path):
    with pytest.raises(ValueError, match="repetido"):
        mod.carregar(_gravar(tmp_path, [_etapa("E1"), _etapa("E1")]))
    with pytest.raises(ValueError, match="não existe"):
        mod.carregar(_gravar(tmp_path, [_etapa("E1", depende_de=["E9"])]))
    with pytest.raises(ValueError, match="status"):
        mod.carregar(_gravar(tmp_path, [_etapa("E1", status="pronto")]))
    with pytest.raises(ValueError, match="estimativa_min"):
        mod.carregar(_gravar(tmp_path, [_etapa("E1", estimativa_min=-1)]))
    with pytest.raises(ValueError, match="objetivo"):
        mod.carregar(_gravar(tmp_path, [_etapa("E1")], objetivo=""))
    with pytest.raises(ValueError, match="não encontrado"):
        mod.carregar(tmp_path / "nao_existe.yaml")


def test_modelo_e_valido(tmp_path):
    arquivo = tmp_path / "rumo.yaml"
    arquivo.write_text(mod.modelo("Algo útil"), encoding="utf-8")
    rumo = mod.carregar(arquivo)
    assert rumo["objetivo"] == "Algo útil"
    assert rumo["etapas"][0]["id"] == "E1"


def test_progresso_ponderado_e_proxima(tmp_path):
    etapas = [
        _etapa("E1", estimativa_min=30, status="feito"),
        _etapa("E2", estimativa_min=60, status="fazendo", depende_de=["E1"]),
        _etapa("E3", estimativa_min=10, status="a_fazer", depende_de=["E2"]),
        _etapa("E4", estimativa_min=30, status="a_fazer", depende_de=["E1"]),
        _etapa("E5", estimativa_min=500, status="cancelado"),
    ]
    prog = mod.progresso(mod.carregar(_gravar(tmp_path, etapas)))
    # (30*1 + 60*0,5) / (30+60+10+30) = 60/130
    assert prog["percentual"] == pytest.approx(60 / 130 * 100)
    assert prog["proxima"] == "E4"
    assert prog["por_status"]["cancelado"] == 1


def test_marcar_preenche_datas(tmp_path):
    arquivo = _gravar(tmp_path, [_etapa("E1")])
    (tmp_path / "e1.txt").write_text("x")
    inicio = datetime(2026, 11, 1, 10, 0, tzinfo=UTC)
    fim = datetime(2026, 11, 1, 11, 30, tzinfo=UTC)
    mod.marcar(arquivo, "E1", "fazendo", agora=inicio)
    mod.marcar(arquivo, "E1", "feito", agora=fim)
    etapa = mod.carregar(arquivo)["etapas"][0]
    assert etapa["status"] == "feito"
    assert etapa["inicio"] == "2026-11-01T10:00:00Z"
    assert etapa["fim"] == "2026-11-01T11:30:00Z"
    with pytest.raises(ValueError):
        mod.marcar(arquivo, "E9", "feito")


def _chamadas(raiz):
    linhas = [
        ("2026-11-01T09:00:00Z", raiz, 100),  # antes da janela
        ("2026-11-01T10:30:00Z", raiz, 200),  # dentro
        ("2026-11-01T10:45:00Z", f"{raiz}/.claude/worktrees/a", 300),  # worktree: dentro
        ("2026-11-01T10:50:00Z", "/outro/projeto", 999),  # outro repositório
        ("2026-11-01T12:00:00Z", raiz, 400),  # depois do fim
    ]
    df = pd.DataFrame(
        {
            "inicio": pd.to_datetime([x[0] for x in linhas], utc=True),
            "cwd": [x[1] for x in linhas],
            "mensagem_id": [f"m{i}" for i in range(len(linhas))],
            "modelo": "claude-sonnet-teste",
        }
    )
    for coluna in sessoes.COLUNAS_TOKENS:
        df[coluna] = 0
    df["tokens_entrada"] = [x[2] for x in linhas]
    return df


def test_real_por_etapa_conta_a_mao(tmp_path):
    etapas = [
        _etapa(
            "E1",
            status="feito",
            inicio="2026-11-01T10:00:00Z",
            fim="2026-11-01T11:30:00Z",
            estimativa_tokens=250,
            estimativa_min=60,
        ),
        _etapa("E2"),
    ]
    rumo = mod.carregar(_gravar(tmp_path, etapas))
    agora = datetime(2026, 11, 2, tzinfo=UTC)
    real = mod.real_por_etapa(rumo, _chamadas(str(tmp_path.resolve())), tmp_path, agora=agora)
    e1 = real.set_index("id").loc["E1"]
    assert e1["chamadas"] == 2
    assert e1["tokens_real"] == 500
    assert e1["duracao_min"] == pytest.approx(90)
    assert e1["razao_tokens"] == pytest.approx(2.0)
    assert e1["razao_tempo"] == pytest.approx(1.5)
    assert real.set_index("id").loc["E2", ["tokens_real", "duracao_min"]].isna().all()


def _repo_git(tmp_path):
    def git(*args):
        subprocess.run(["git", "-C", str(tmp_path), *args], check=True, capture_output=True)

    git("init", "-q", "-b", "main")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (tmp_path / "base.txt").write_text("a")
    git("add", "-A")
    git("commit", "-qm", "base")
    return git


def test_desvios(tmp_path):
    git = _repo_git(tmp_path)
    (tmp_path / "e1.txt").write_text("x")
    (tmp_path / "intruso.py").write_text("x")
    git("add", "-A")
    git("commit", "-qm", "trabalho")
    (tmp_path / "solto.py").write_text("x")  # não commitado
    (tmp_path / "rumo.yaml").write_text("ignorado")
    etapas = [
        _etapa(
            "E1",
            status="feito",
            inicio="2026-11-01T10:00:00Z",
            fim="2026-11-01T11:30:00Z",
            estimativa_tokens=250,
        ),
        _etapa("E2", status="feito", entregaveis=["e2.txt", "dados/*.csv"]),
        _etapa(
            "E3",
            status="fazendo",
            inicio="2026-11-01T00:00:00Z",
            estimativa_min=60,
            entregaveis=["e3.txt"],
        ),
    ]
    rumo = mod.carregar(_gravar(tmp_path, etapas, base="HEAD~1"))
    agora = datetime(2026, 11, 1, 12, 0, tzinfo=UTC)
    real = mod.real_por_etapa(rumo, _chamadas(str(tmp_path.resolve())), tmp_path, agora=agora)
    achados = mod.desvios(rumo, tmp_path, real)
    por_tipo = {}
    for d in achados:
        por_tipo.setdefault(d["tipo"], []).append(d)
    fora = " ".join(d["detalhe"] for d in por_tipo["fora do plano"])
    assert "intruso.py" in fora and "solto.py" in fora
    assert "e1.txt" not in fora and "rumo.yaml" not in fora
    assert {d["etapa"] for d in por_tipo["estouro"]} == {"E1", "E3"}
    assert por_tipo["parada"][0]["etapa"] == "E3"
    assert por_tipo["entregável ausente"][0]["etapa"] == "E2"


def _exemplo(tmp_path):
    etapas = [
        _etapa("E1", status="feito", inicio="2026-11-01T10:00:00Z", fim="2026-11-01T11:00:00Z"),
        _etapa("E2", status="a_fazer", depende_de=["E1"]),
    ]
    rumo = mod.carregar(
        _gravar(tmp_path, etapas, historico=[{"data": "2026-11-01", "mudanca": "m", "motivo": "x"}])
    )
    chamadas = _chamadas(str(tmp_path.resolve()))
    real = mod.real_por_etapa(rumo, chamadas, tmp_path)
    desv = [{"tipo": "fora do plano", "etapa": None, "detalhe": "a.py alterado"}]
    return rumo, mod.progresso(rumo), real, desv


def test_markdown(tmp_path):
    rumo, prog, real, desv = _exemplo(tmp_path)
    texto = mod.markdown(rumo, prog, real, desv)
    assert "▓▓▓▓▓░░░░░ 50%" in texto
    assert "| E1 | Etapa E1 | ✅ feito |" in texto
    assert "| E2 | Etapa E2 | ⏳ a_fazer |" in texto
    assert "fora do plano: a.py alterado" in texto
    assert "Próxima etapa:** E2" in texto
    assert "Mudanças de objetivo: 1" in texto


def test_html_sem_script_proprio(tmp_path):
    rumo, prog, real, desv = _exemplo(tmp_path)
    pagina = mod.html(rumo, prog, real, desv)
    assert "Rumo do desenvolvimento" in pagina and "Meta" in pagina
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", pagina, flags=re.DOTALL)
    assert scripts
    for bloco in re.findall(r"<script[^>]*>.*?</script>", pagina, flags=re.DOTALL):
        assert "plotly" in bloco.lower() or "Plotly" in bloco


def test_cli_novo_marcar_e_relatorio(tmp_path, capsys):
    _repo_git(tmp_path)
    assert cli.main(["rumo", "--repo", str(tmp_path), "--novo", "Meta nova"]) == 0
    assert cli.main(["rumo", "--repo", str(tmp_path), "--novo", "outra"]) == 1
    assert cli.main(["rumo", "--repo", str(tmp_path), "--etapa", "E1", "--status", "fazendo"]) == 0
    assert cli.main(["rumo", "--repo", str(tmp_path), "--sem-sessoes"]) == 0
    assert "Rumo do desenvolvimento" in capsys.readouterr().out
    assert (tmp_path / "results" / "rumo.html").exists()
    assert (tmp_path / "results" / "rumo.md").exists()


def test_tempo_do_rumo_calendario_e_horas_da_ia(tmp_path):
    import pandas as pd
    import pytest

    from vcm import rumo as mod

    rumo = {
        "objetivo": "x", "criterio_de_pronto": [], "base": None, "historico": [],
        "etapas": [
            {"id": "E1", "nome": "a", "entregaveis": [], "depende_de": [], "agente": "sonnet",
             "estimativa_min": 30, "estimativa_tokens": 1, "status": "feito",
             "inicio": "2026-11-01T10:00:00Z", "fim": "2026-11-02T10:00:00Z"},
        ],
    }  # fmt: skip
    chamadas = pd.DataFrame(
        {"sessao_id": "s", "agente_id": None, "cwd": str(tmp_path.resolve()),
         "inicio": pd.to_datetime("2026-11-01T10:00Z") + pd.to_timedelta(range(0, 61, 2), unit="min")}
    )  # fmt: skip
    t = mod.tempo_do_rumo(rumo, chamadas, tmp_path)
    assert t["dias_corridos"] == pytest.approx(1.0)
    assert t["horas_relogio_ia"] == pytest.approx(1.0)
    texto = " ".join(mod._texto_tempo(t))
    assert "1,00 dias corridos" in texto and "1,0 h de relógio" in texto


def test_etapas_simultaneas_ficam_com_as_chamadas_do_seu_agente(tmp_path):
    etapas = [
        _etapa("E1", agente="sonnet", status="feito", inicio="2026-11-01T10:00:00Z",
               fim="2026-11-01T11:30:00Z"),
        _etapa("E2", agente="opus", status="feito", inicio="2026-11-01T10:00:00Z",
               fim="2026-11-01T11:30:00Z"),
    ]  # fmt: skip
    rumo = mod.carregar(_gravar(tmp_path, etapas))
    chamadas = _chamadas(str(tmp_path.resolve()))
    chamadas.loc[1, "modelo"] = "claude-opus-teste"  # a das 10:30 foi do gerente (Opus)
    chamadas.loc[1, "tokens_cache_leitura"] = 10_000_000  # releitura de contexto: fora da conta
    real = mod.real_por_etapa(rumo, chamadas, tmp_path).set_index("id")
    assert real.loc["E1", "tokens_real"] == 300  # só a do Sonnet (worktree)
    assert real.loc["E2", "tokens_real"] == 200  # só a do Opus, sem a leitura de cache


def test_etapas_do_mesmo_modelo_em_paralelo_separam_pela_descricao_do_agente(tmp_path):
    etapas = [
        _etapa("E1", agente="sonnet", status="feito", inicio="2026-11-01T10:00:00Z",
               fim="2026-11-01T11:30:00Z"),
        _etapa("E2", agente="sonnet", status="feito", inicio="2026-11-01T10:00:00Z",
               fim="2026-11-01T11:30:00Z"),
    ]  # fmt: skip
    rumo = mod.carregar(_gravar(tmp_path, etapas))
    chamadas = _chamadas(str(tmp_path.resolve()))
    chamadas["descricao"] = [None, "E1: refatorar", "E2: sugestões", None, None]
    real = mod.real_por_etapa(rumo, chamadas, tmp_path).set_index("id")
    assert real.loc["E1", "tokens_real"] == 200
    assert real.loc["E2", "tokens_real"] == 300


def _gravar_texto(tmp_path, texto):
    arquivo = tmp_path / "rumo.yaml"
    arquivo.write_text(texto, encoding="utf-8")
    return arquivo


@pytest.mark.parametrize(
    ("texto", "mensagem"),
    [
        ("a: [\n", "YAML inválido em"),
        ("- lista\n", "deve conter um mapa com objetivo e etapas"),
        ("etapas: [{id: E1}]\n", "o rumo precisa de um 'objetivo'"),
        ("objetivo: '  '\netapas: [{id: E1}]\n", "o rumo precisa de um 'objetivo'"),
        ("objetivo: X\n", "o rumo precisa de ao menos uma etapa em 'etapas'"),
        ("objetivo: X\netapas: []\n", "o rumo precisa de ao menos uma etapa em 'etapas'"),
        ("objetivo: X\netapas: abc\n", "o rumo precisa de ao menos uma etapa em 'etapas'"),
        ("objetivo: X\netapas: [{nome: A}]\n", "etapa 1 sem 'id'"),
        ("objetivo: X\netapas: [{id: E1}, texto]\n", "etapa 2 sem 'id'"),
        ("objetivo: X\netapas: [{id: ''}]\n", "etapa 1 sem 'id'"),
    ],
)
def test_validacao_estrutura_mensagens(tmp_path, texto, mensagem):
    with pytest.raises(ValueError) as erro:
        mod.carregar(_gravar_texto(tmp_path, texto))
    assert mensagem in str(erro.value)


@pytest.mark.parametrize(
    ("etapas", "mensagem"),
    [
        ([_etapa("E1"), _etapa("E1")], "id de etapa repetido: E1"),
        (
            [_etapa("E1", status="pronto")],
            (
                "etapa E1: status 'pronto' inválido (use um de a_fazer, fazendo, feito, "
                "bloqueado, cancelado)"
            ),
        ),
        (
            [_etapa("E1", agente="robo")],
            "etapa E1: agente 'robo' inválido (use um de haiku, sonnet, opus, humano)",
        ),
        (
            [_etapa("E1", estimativa_min=-1)],
            "etapa E1: 'estimativa_min' deve ser número maior ou igual a 0",
        ),
        (
            [_etapa("E1", estimativa_tokens="muito")],
            "etapa E1: 'estimativa_tokens' deve ser número maior ou igual a 0",
        ),
        (
            [_etapa("E1", estimativa_min=True)],
            "etapa E1: 'estimativa_min' deve ser número maior ou igual a 0",
        ),
        ([_etapa("E1", inicio="ontem")], "etapa E1: 'inicio' não é uma data ISO 8601"),
        ([_etapa("E1", fim="amanhã")], "etapa E1: 'fim' não é uma data ISO 8601"),
        (
            [_etapa("E1", depende_de=["E9"])],
            "etapa E1: depende_de 'E9', que não existe",
        ),
    ],
)
def test_validacao_etapas_mensagens(tmp_path, etapas, mensagem):
    with pytest.raises(ValueError) as erro:
        mod.carregar(_gravar(tmp_path, etapas))
    assert str(erro.value) == mensagem


def test_padroes_do_rumo_e_da_etapa(tmp_path):
    arquivo = _gravar_texto(tmp_path, "objetivo: X\netapas:\n  - id: 7\n")
    rumo = mod.carregar(arquivo)
    assert rumo["criterio_de_pronto"] == []
    assert rumo["base"] is None
    assert rumo["historico"] == []
    assert rumo["etapas"][0] == {
        "id": "7",
        "nome": "7",
        "entregaveis": [],
        "depende_de": [],
        "agente": "humano",
        "status": "a_fazer",
        "inicio": None,
        "fim": None,
        "forcado": None,
        "estimativa_min": 0,
        "estimativa_tokens": 0,
    }


def test_depende_de_vira_texto_e_estimativas_decimais_valem(tmp_path):
    etapas = [_etapa("1"), _etapa("2", depende_de=[1], estimativa_min=2.5, estimativa_tokens=0)]
    rumo = mod.carregar(_gravar(tmp_path, etapas))
    assert rumo["etapas"][1]["depende_de"] == ["1"]
    assert rumo["etapas"][1]["estimativa_min"] == 2.5


def test_ordem_das_chaves_da_etapa_e_estavel(tmp_path):
    rumo = mod.carregar(_gravar_texto(tmp_path, "objetivo: X\netapas:\n  - id: E1\n"))
    assert list(rumo["etapas"][0]) == [
        "id",
        "nome",
        "entregaveis",
        "depende_de",
        "agente",
        "status",
        "inicio",
        "fim",
        "forcado",
        "estimativa_min",
        "estimativa_tokens",
    ]


def _balanco(tmp_path, testes_falhando=0.0, decisao="MANTER", mtime=None):
    """Grava um cartão Parquet mínimo, no formato de `cartao.gravar`."""
    pasta = tmp_path / "results" / "iteracoes"
    pasta.mkdir(parents=True, exist_ok=True)
    tabela = pd.DataFrame(
        {"antes": [0.0], "depois": [testes_falhando], "decisao": [decisao]},
        index=pd.Index(["testes_falhando"], name="metrica"),
    )
    cartao = pasta / "aaaaaaa_bbbbbbb.parquet"
    tabela.to_parquet(cartao)
    if mtime is not None:
        os.utime(cartao, (mtime, mtime))
    return cartao


def test_feito_bloqueia_entregavel_ausente_e_libera_presente(tmp_path):
    arquivo = _gravar(tmp_path, [_etapa("E1")])
    with pytest.raises(ValueError, match="entregável ausente: e1.txt"):
        mod.marcar(arquivo, "E1", "feito")
    assert mod.carregar(arquivo)["etapas"][0]["status"] == "a_fazer"
    (tmp_path / "e1.txt").write_text("x")
    assert mod.marcar(arquivo, "E1", "feito")["status"] == "feito"


def test_feito_bloqueia_balanco_com_teste_falhando(tmp_path):
    (tmp_path / "e1.txt").write_text("x")
    _balanco(tmp_path, testes_falhando=2.0)
    etapa = _etapa("E1", inicio="2020-01-01T00:00:00Z")
    pendencias = mod.provas_de_feito(etapa, tmp_path)
    assert pendencias == ["último balanço com 2 teste(s) falhando (aaaaaaa_bbbbbbb.parquet)"]


def test_feito_ignora_balanco_anterior_ao_inicio(tmp_path):
    (tmp_path / "e1.txt").write_text("x")
    _balanco(tmp_path, testes_falhando=2.0, mtime=datetime(2024, 1, 1, tzinfo=UTC).timestamp())
    etapa = _etapa("E1", inicio="2025-01-01T00:00:00Z")
    assert mod.provas_de_feito(etapa, tmp_path) == []


def test_feito_bloqueia_decisao_reverter(tmp_path):
    (tmp_path / "e1.txt").write_text("x")
    _balanco(tmp_path, decisao="REVERTER")
    pendencias = mod.provas_de_feito(_etapa("E1", inicio="2020-01-01T00:00:00Z"), tmp_path)
    assert pendencias == ["último balanço com decisão REVERTER (aaaaaaa_bbbbbbb.parquet)"]


def test_forcar_sem_motivo_da_erro_e_com_motivo_grava_e_gera_desvio(tmp_path):
    arquivo = _gravar(tmp_path, [_etapa("E1")])
    with pytest.raises(ValueError, match="motivo"):
        mod.marcar(arquivo, "E1", "feito", forcar=True)
    etapa = mod.marcar(arquivo, "E1", "feito", forcar=True, motivo="entregue em outro PR")
    assert etapa["forcado"] == "entregue em outro PR"
    rumo = mod.carregar(arquivo)
    assert rumo["etapas"][0]["forcado"] == "entregue em outro PR"
    real = mod.real_por_etapa(rumo, _chamadas(str(tmp_path.resolve())), tmp_path)
    desvios = [d for d in mod.desvios(rumo, tmp_path, real) if d["tipo"] == "feito sem prova"]
    assert len(desvios) == 1
    assert "entregue em outro PR" in desvios[0]["detalhe"]


def test_cli_feito_sem_prova_devolve_1_com_mensagem(tmp_path, capsys):
    _gravar(tmp_path, [_etapa("E1")])
    base = ["rumo", "--repo", str(tmp_path), "--etapa", "E1", "--status", "feito"]
    assert cli.main(base) == 1
    erro = capsys.readouterr().err
    assert "entregável ausente: e1.txt" in erro
    assert "--forcar --motivo" in erro
    assert cli.main([*base, "--forcar"]) == 1
    assert cli.main([*base, "--forcar", "--motivo", "ok"]) == 0
