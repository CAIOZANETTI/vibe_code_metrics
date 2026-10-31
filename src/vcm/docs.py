"""Gera um HTML único e formatado a partir dos Markdown de `docs/`.

O Markdown é a fonte da verdade (renderiza no GitHub, inclusive diagramas
Mermaid). O HTML é derivado e determinístico: mesma entrada -> mesmos bytes,
sem carimbo de data. Assim `vcm docs --check` (usado no CI) detecta HTML
desatualizado.
"""

from __future__ import annotations

import hashlib
import html
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader, select_autoescape
from markdown_it import MarkdownIt

DOCS_PADRAO = ("guia.md", "arquitetura.md", "plano.md", "estilo.md")
SAIDA_PADRAO = "index.html"


@dataclass
class Secao:
    nivel: int
    titulo: str
    ancora: str


@dataclass
class Documento:
    id: str
    arquivo: str
    titulo: str
    html: str
    secoes: list[Secao]


def slug(texto: str) -> str:
    t = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return t or "secao"


def _md() -> MarkdownIt:
    md = MarkdownIt("commonmark", {"html": True}).enable(["table", "strikethrough"])
    padrao = md.renderer.rules.get("fence")

    def fence(self, tokens, idx, options, env):
        tok = tokens[idx]
        if tok.info.strip() == "mermaid":
            return f'<pre class="mermaid">{html.escape(tok.content)}</pre>\n'
        return padrao(tokens, idx, options, env)

    md.add_render_rule("fence", fence)
    return md


def _reescrever_links(conteudo: str, ids: dict[str, str]) -> str:
    """Links para outro .md desta documentação viram âncoras internas do HTML."""

    def troca(m: re.Match) -> str:
        alvo, ancora = m.group(1), m.group(2) or ""
        nome = Path(alvo).name
        if nome in ids:
            return f'href="#{ancora[1:] if ancora else ids[nome]}"'
        return m.group(0)

    return re.sub(r'href="([^"#]+\.md)(#[^"]*)?"', troca, conteudo)


_TAREFA = re.compile(r"<li>\[( |x|X)\] ")


def _checkboxes(conteudo: str) -> str:
    """`- [x] item` vira checkbox (lista de tarefas no estilo GitHub)."""

    def troca(m: re.Match) -> str:
        marcado = " checked" if m.group(1).lower() == "x" else ""
        return f'<li class="tarefa"><input type="checkbox" disabled{marcado}> '

    return _TAREFA.sub(troca, conteudo)


def renderizar_documento(caminho: Path, md: MarkdownIt, prefixo: str) -> Documento:
    texto = caminho.read_text(encoding="utf-8")
    tokens = md.parse(texto)
    secoes: list[Secao] = []
    vistos: set[str] = set()
    titulo = caminho.stem
    for i, tok in enumerate(tokens):
        if tok.type != "heading_open":
            continue
        nivel = int(tok.tag[1])
        conteudo = tokens[i + 1].content
        if nivel == 1:
            titulo = conteudo
        base = f"{prefixo}-{slug(conteudo)}"
        ancora, n = base, 2
        while ancora in vistos:
            ancora, n = f"{base}-{n}", n + 1
        vistos.add(ancora)
        tok.attrSet("id", ancora)
        if nivel in (2, 3):
            secoes.append(Secao(nivel, conteudo, ancora))
    corpo = md.renderer.render(tokens, md.options, {})
    return Documento(prefixo, caminho.name, titulo, corpo, secoes)


def construir(
    pasta: Path, arquivos: tuple[str, ...] = DOCS_PADRAO, titulo_pagina: str | None = None
) -> str:
    md = _md()
    ids = {a: f"doc-{Path(a).stem}" for a in arquivos}
    docs = [renderizar_documento(pasta / a, md, ids[a]) for a in arquivos]
    for d in docs:
        d.html = _checkboxes(_reescrever_links(d.html, ids))
    fonte = b"".join((pasta / a).read_bytes() for a in arquivos)
    env = Environment(
        loader=PackageLoader("vcm", "templates"),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    return env.get_template("docs.html.j2").render(
        docs=docs,
        hash_fonte=hashlib.sha256(fonte).hexdigest()[:12],
        **({"titulo_pagina": titulo_pagina} if titulo_pagina else {}),
    )


def gerar_avulso(markdown: Path, saida: Path | None = None) -> Path:
    """Um Markdown qualquer (relatório, diagnóstico) -> HTML no estilo da documentação.

    O título da página é o primeiro `# título` do arquivo.
    """
    saida = saida or markdown.with_suffix(".html")
    primeira = next(
        (
            linha[2:].strip()
            for linha in markdown.read_text(encoding="utf-8").splitlines()
            if linha.startswith("# ")
        ),
        markdown.stem,
    )
    saida.write_text(
        construir(markdown.parent, (markdown.name,), titulo_pagina=primeira), encoding="utf-8"
    )
    return saida


def gerar(pasta: Path, saida: Path | None = None, check: bool = False) -> bool:
    """Gera (ou verifica) o HTML. Retorna True se o arquivo está atualizado."""
    saida = saida or pasta / SAIDA_PADRAO
    novo = construir(pasta)
    atual = saida.read_text(encoding="utf-8") if saida.exists() else None
    if check:
        return atual == novo
    if atual != novo:
        saida.write_text(novo, encoding="utf-8")
    return True
