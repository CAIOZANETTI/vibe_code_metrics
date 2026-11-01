import subprocess
from pathlib import Path

import pandas as pd
import pytest

from vcm import agentes, cartao, formatacao
from vcm import snapshot as snap
from vcm.balanco import Decisao


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*a):
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True)

    git("init", "-q")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    (repo / "a.py").write_text("x = 1\n")
    git("add", ".")
    git("commit", "-qm", "primeiro")
    (repo / "a.py").write_text("x = 1\ny = 2\nz = 3\n")
    git("commit", "-qam", "segundo")
    return repo


def _medidor_falso(raiz: Path, **_):
    linhas = len((raiz / "a.py").read_text().splitlines())
    return {"sloc_por_funcao": float(linhas), "testes_total": 1.0, "testes_falhando": 0.0}


def test_snapshot_em_worktree_e_cache(tmp_path):
    repo = _repo(tmp_path)
    arquivo = tmp_path / "snap.parquet"
    s1 = snap.obter_snapshot(repo, "HEAD~1", arquivo=arquivo, medidor=_medidor_falso)
    s2 = snap.obter_snapshot(repo, "HEAD", arquivo=arquivo, medidor=_medidor_falso)
    assert s1["sloc_por_funcao"] == 1 and s2["sloc_por_funcao"] == 3
    assert s2["mensagem"] == "segundo"
    assert len(snap.ler_snapshots(arquivo)) == 2
    # cache: não chama o medidor de novo
    s2b = snap.obter_snapshot(repo, "HEAD", arquivo=arquivo, medidor=None)
    assert s2b["sloc_por_funcao"] == 3
    # worktrees temporárias foram removidas
    lista = subprocess.run(
        ["git", "-C", str(repo), "worktree", "list"], check=True, capture_output=True, text=True
    ).stdout
    assert len(lista.strip().splitlines()) == 1

    r = snap.retrospectiva(s1, s2)
    assert r["decisao"] is Decisao.DECISAO_HUMANA
    assert r["tabela"].loc["sloc_por_funcao", "veredito"] == "piorou"


def test_cartao_markdown_e_html(tmp_path):
    antes = pd.Series({"commit": "a" * 40, "sloc_por_funcao": 100.0, "tempo_p50_ms": 50.0})
    depois = pd.Series(
        {"commit": "b" * 40, "mensagem": "m", "sloc_por_funcao": 90.0, "tempo_p50_ms": 50.0}
    )
    r = snap.retrospectiva(antes, depois)
    assert r["decisao"] is Decisao.MANTER
    md = cartao.markdown(r)
    assert "Decisão proposta: MANTER" in md and "-10,0%" in md
    caminhos = cartao.gravar(r, tmp_path)
    h = caminhos["html"].read_text(encoding="utf-8")
    assert "Ficou mais enxuto?" in h
    assert pd.read_parquet(caminhos["parquet"])["decisao"].iloc[0] == "MANTER"


def test_formatacao_brasileira():
    assert formatacao.numero(1234567.891, 2) == "1.234.567,89"
    assert formatacao.numero(float("nan")) == "—"
    assert formatacao.percentual(12.34) == "+12,3%"
    assert formatacao.percentual(-5.0) == "-5,0%"


def test_registro_de_agentes(tmp_path):
    arq = tmp_path / "exec.csv"
    agentes.registrar(arq, modelo="haiku", tokens=1000, duracao_s=10, aprovado=True)
    agentes.registrar(arq, modelo="haiku", tokens=3000, duracao_s=30, aprovado=False)
    agentes.registrar(arq, modelo="sonnet", tokens=5000, duracao_s=50, aprovado=True)
    r = agentes.resumo_por_modelo(agentes.ler(arq))
    assert r.loc["haiku", "tokens_por_aprovacao"] == 4000
    assert r.loc["haiku", "taxa_aprovacao"] == 0.5
    with pytest.raises(ValueError):
        agentes.registrar(arq, modelo_errado="x")


def test_limites_vazios_do_projeto_mantem_os_padroes():
    # Regressão: `limites: {}` no vcm.yaml apagava os limites padrão (semáforo todo cinza).
    antes = pd.Series({"commit": "a" * 40, "testes_falhando": 0.0, "cobertura_testes": 0.9})
    depois = pd.Series({"commit": "b" * 40, "testes_falhando": 0.0, "cobertura_testes": 0.9})
    md = cartao.markdown(snap.retrospectiva(antes, depois), limites={})
    assert "sem limite definido" not in md
    assert "🟢" in md


def test_referencia_mudou_torna_tempo_informativo():
    antes = pd.Series({"commit": "a" * 40, "hash_referencia": "x", "tempo_referencia_ms": 10.0})
    depois = pd.Series({"commit": "b" * 40, "hash_referencia": "y", "tempo_referencia_ms": 20.0})
    r = snap.retrospectiva(antes, depois)
    assert r["referencia_mudou"]
    assert r["tabela"].loc["tempo_referencia_ms", "veredito"] == "info"
    assert "conjunto de referência mudou" in cartao.markdown(r)
    mesmo = pd.Series({"commit": "c" * 40, "hash_referencia": "x", "tempo_referencia_ms": 20.0})
    r2 = snap.retrospectiva(antes, mesmo)
    assert not r2["referencia_mudou"]
    assert r2["tabela"].loc["tempo_referencia_ms", "veredito"] == "piorou"


def test_radar_ignora_metricas_tornadas_informativas():
    from vcm import semaforo

    antes = pd.Series({"commit": "a" * 40, "hash_referencia": "x", "tempo_referencia_ms": 10.0})
    depois = pd.Series({"commit": "b" * 40, "hash_referencia": "y", "tempo_referencia_ms": 20.0})
    indices = semaforo.indices_iteracao(snap.retrospectiva(antes, depois)["tabela"])
    eficiente = indices.set_index("dimensao").loc["eficiente"]
    assert eficiente["indice_desenho"] == 1.0


def test_semaforo_mostra_metricas_que_a_base_nao_tinha():
    antes = pd.Series({"commit": "a" * 40, "cobertura_testes": 0.9})
    depois = pd.Series(
        {"commit": "b" * 40, "cobertura_testes": 0.9, "frac_execucoes_identicas": 0.4}
    )
    md = cartao.markdown(snap.retrospectiva(antes, depois))
    assert "| frac_execucoes_identicas | deterministico |" in md
    assert "🔴" in md


def test_ruido_automatico_pelas_repeticoes_do_snapshot():
    antes = pd.Series(
        {"commit": "a" * 40, "tempo_referencia_ms": 100.0, "cv_tempo_referencia": 0.2}
    )
    depois = pd.Series({"commit": "b" * 40, "tempo_referencia_ms": 130.0})
    # oscilação de 20% nas repetições -> faixa de 40%: +30% é ruído
    r = snap.retrospectiva(antes, depois)
    assert r["tabela"].loc["tempo_referencia_ms", "veredito"] == "igual"


def test_cache_sem_testes_e_remedido_quando_testes_sao_pedidos(tmp_path):
    repo = _repo(tmp_path)
    arquivo = tmp_path / "snap.parquet"
    chamadas = []

    def medidor(raiz, com_testes=True, **_):
        chamadas.append(com_testes)
        return {"sloc_por_funcao": 1.0, **({"testes_total": 3.0} if com_testes else {})}

    snap.obter_snapshot(repo, "HEAD", arquivo=arquivo, medidor=medidor, com_testes=False)
    s = snap.obter_snapshot(repo, "HEAD", arquivo=arquivo, medidor=medidor, com_testes=True)
    assert chamadas == [False, True] and s["testes_total"] == 3
    # agora o cache tem testes: serve também para quem pede sem testes
    snap.obter_snapshot(repo, "HEAD", arquivo=arquivo, medidor=medidor, com_testes=False)
    assert chamadas == [False, True]
