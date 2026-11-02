from pathlib import Path

from vcm import docs


def _pasta(tmp_path: Path) -> Path:
    (tmp_path / "arquitetura.md").write_text(
        "# Arquitetura\n\n## Visão geral\n\nVer [plano](plano.md).\n\n"
        "```mermaid\nflowchart LR\n  A --> B\n```\n\n| a | b |\n|---|---|\n| 1 | 2 |\n",
        encoding="utf-8",
    )
    (tmp_path / "plano.md").write_text(
        "# Plano\n\n## Fase 0\n\n- [x] feito\n- [ ] a fazer\n", encoding="utf-8"
    )
    (tmp_path / "estilo.md").write_text("# Estilo\n\n## Regras\n", encoding="utf-8")
    (tmp_path / "guia.md").write_text("# Guia\n\n## Instalar\n", encoding="utf-8")
    (tmp_path / "repertorio.md").write_text("# Repertório\n\n## Cálculo\n", encoding="utf-8")
    return tmp_path


def test_html_tem_navegacao_mermaid_tabela_e_checkbox(tmp_path):
    h = docs.construir(_pasta(tmp_path))
    assert 'id="doc-arquitetura-visao-geral"' in h
    assert 'href="#doc-arquitetura-visao-geral"' in h
    assert '<pre class="mermaid">flowchart LR\n  A --&gt; B\n</pre>' in h
    assert "<table>" in h
    assert 'href="#doc-plano"' in h  # link entre documentos vira âncora
    assert '<input type="checkbox" disabled checked> feito' in h
    assert '<input type="checkbox" disabled> a fazer' in h


def test_geracao_deterministica_e_check(tmp_path):
    pasta = _pasta(tmp_path)
    assert docs.construir(pasta) == docs.construir(pasta)
    assert not docs.gerar(pasta, check=True)  # ainda não gerado
    docs.gerar(pasta)
    assert docs.gerar(pasta, check=True)
    (pasta / "plano.md").write_text("# Plano\n\nmudou\n", encoding="utf-8")
    assert not docs.gerar(pasta, check=True)


def test_slug_remove_acentos():
    assert docs.slug("Retrospectiva de iteração") == "retrospectiva-de-iteracao"


def test_docs_do_repositorio_estao_em_dia():
    raiz = Path(__file__).resolve().parents[1]
    assert docs.gerar(raiz / "docs", check=True), "rode: uv run vcm docs"


def test_markdown_avulso_vira_html_com_titulo(tmp_path):
    md = tmp_path / "diagnostico.md"
    md.write_text(
        "# Diagnóstico X\n\n## Achados\n\n| a | b |\n|---|---|\n| 1 | 2 |\n", encoding="utf-8"
    )
    saida = docs.gerar_avulso(md)
    h = saida.read_text(encoding="utf-8")
    assert saida.name == "diagnostico.html"
    assert "<title>Diagnóstico X</title>" in h and "<table>" in h
    assert "docs/diagnostico.md" not in h and "vcm html diagnostico.md" in h


def test_versao_artefato_sem_esqueleto_nem_script_externo(tmp_path):
    pasta = _pasta(tmp_path)
    saida = docs.gerar_artefato(pasta, tmp_path / "artefato.html")
    h = saida.read_text(encoding="utf-8")
    assert h.startswith("<title>Vibe Code Metrics</title>")
    assert "<html" not in h and "<body" not in h and "<script" not in h
    assert '<pre class="mermaid">' in h and 'data-theme="dark"' in h
    assert "https://github.com/CAIOZANETTI/vibe_code_metrics/blob/main/docs/plano.md" in h


def test_repertorio_md_e_gerado_dos_yaml_e_vigiado_pelo_check(tmp_path):
    from vcm import repertorio

    docs_ = tmp_path / "docs"
    docs_.mkdir()
    _pasta(docs_)
    origem = tmp_path / "repertorio" / "calculo"
    origem.mkdir(parents=True)
    (origem / "numpy.yaml").write_text(
        "id: numpy\nnome: NumPy\npapel: calculo\ndescricao: Arrays.\n"
        "quando_considerar: [matriz densa]\nquando_evitar: []\ncuidados: [threads do BLAS]\n"
        "coopera_com: []\ncompete_com: []\nlicenca: BSD-3-Clause\nstatus: em_uso\n",
        encoding="utf-8",
    )
    md = repertorio.markdown(tmp_path / "repertorio")
    assert "## Cálculo numérico" in md and "| NumPy | em uso | BSD-3-Clause |" in md
    assert "- threads do BLAS" in md
    assert not docs.gerar(docs_, check=True)  # repertorio.md da fixture está desatualizado
    docs.gerar(docs_)
    assert docs.gerar(docs_, check=True)
    assert (docs_ / "repertorio.md").read_text(encoding="utf-8") == md
