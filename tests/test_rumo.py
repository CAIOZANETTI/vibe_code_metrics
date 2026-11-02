"""Testes do rumo do desenvolvimento (WBS × realizado)."""

from __future__ import annotations

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
