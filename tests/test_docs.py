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
