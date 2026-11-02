import os
import re
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from vcm import efeito, historico


def _repo(tmp_path: Path, n: int = 8, adocao: int = 4) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()

    def git(*a, env=None):
        subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True, env=env)

    git("init", "-q")
    git("config", "user.email", "t@t")
    git("config", "user.name", "t")
    for i in range(1, n + 1):
        (repo / "a.txt").write_text(f"{i}\n")
        if i == adocao:
            (repo / "vcm.yaml").write_text("x: 1\n")
        git("add", ".")
        data = f"2026-01-{i:02d}T12:00:00+00:00"
        git(
            "commit",
            "-qm",
            f"c{i}",
            env={**os.environ, "GIT_COMMITTER_DATE": data, "GIT_AUTHOR_DATE": data},
        )
    return repo


def _medidor(raiz: Path, **_):
    i = int((raiz / "a.txt").read_text())
    # antes da adoção (i < 4) constante em 10; depois cai 1 por commit
    complexidade = 10.0 if i < 4 else 10.0 - (i - 3)
    return {"complexidade_media": complexidade, "sloc": 100.0 + i, "testes_falhando": 0.0}


@pytest.fixture
def repo(tmp_path):
    return _repo(tmp_path)


@pytest.fixture
def serie(repo, tmp_path):
    commits = historico.commits_amostrados(repo)
    return historico.medir_historico(
        repo, commits, arquivo=tmp_path / "snap.parquet", medidor=_medidor
    )


def test_amostragem_inclui_primeiro_e_ultimo(repo):
    todos = historico.commits_amostrados(repo)
    assert len(todos) == 8
    amostra = historico.commits_amostrados(repo, passo=3)
    assert amostra == [todos[0], todos[3], todos[6], todos[7]]
    limitada = historico.commits_amostrados(repo, maximo=3)
    assert len(limitada) == 3 and limitada[0] == todos[0] and limitada[-1] == todos[-1]
    assert historico.commits_amostrados(repo, desde=todos[2]) == todos[2:]


def test_commit_de_adocao(repo, tmp_path):
    assert efeito.commit_de_adocao(repo) == historico.commits_amostrados(repo)[3]
    vazio = tmp_path / "vazio"
    vazio.mkdir()
    subprocess.run(["git", "-C", str(vazio), "init", "-q"], check=True)
    subprocess.run(
        ["git", "-C", str(vazio), "-c", "user.email=a@b", "-c", "user.name=a"]
        + ["commit", "-q", "--allow-empty", "-m", "x"],
        check=True,
    )
    assert efeito.commit_de_adocao(vazio) is None


def test_serie_ordenada_e_progresso(serie, capsys):
    assert len(serie) == 8
    assert serie["data_commit"].is_monotonic_increasing


def test_vereditos_e_tendencia(serie):
    comp = efeito.comparar(serie, serie.loc[3, "data_commit"])
    assert "sloc" not in comp.index  # informativa, não julgada
    c = comp.loc["complexidade_media"]
    assert (c.n_antes, c.n_depois) == (3, 5)
    assert c.media_antes == 10.0
    assert c.media_depois == pytest.approx(np.mean([9, 8, 7, 6, 5]))
    assert c.tendencia_antes == pytest.approx(0.0, abs=1e-9)
    assert c.tendencia_depois == pytest.approx(-1.0)
    assert c.veredito == "melhorou"
    assert comp.loc["testes_falhando", "veredito"] == "igual"
    tarde = efeito.comparar(serie, serie.loc[6, "data_commit"])
    assert tarde.loc["complexidade_media", "veredito"] == "insuficiente"
    frases = efeito.ressalvas(tarde)
    assert any("Só 2 commits depois da adoção" in f for f in frases)
    assert any("Estudo observacional" in f for f in frases)


def test_indicadores_processo(tmp_path):
    pasta = tmp_path / "it"
    pasta.mkdir()
    for nome, dec in [("a", "MANTER"), ("b", "MANTER"), ("c", "REVERTER")]:
        pd.DataFrame({"antes": [1.0], "decisao": [dec]}).to_parquet(pasta / f"{nome}.parquet")
    r = efeito.indicadores_processo(pasta)
    assert (r["MANTER"], r["REVERTER"], r["SEM_GANHO"], r["total"]) == (2, 1, 0, 3)


def test_relatorio_html(serie, tmp_path):
    data = serie.loc[3, "data_commit"]
    comp = efeito.comparar(serie, data)
    saida = efeito.gerar_relatorio(
        serie,
        comp,
        efeito.indicadores_processo(tmp_path / "nada"),
        efeito.ressalvas(comp),
        tmp_path / "out" / "efeito.html",
        {"projeto": "repo", "commit": "abc1234ffff", "data": data},
    )
    html = saida.read_text(encoding="utf-8")
    assert "ado\\u00e7\\u00e3o do vcm" in html and "abc1234" in html
    assert "complexidade_media" in html and "Ressalvas" in html
    for corpo in re.findall(r"<script[^>]*>(.*?)</script>", html, flags=re.DOTALL):
        assert corpo == "" or "Plotly" in corpo
