"""Adoção do método Vibe Code Metrics num projeto, em um passo (`vcm iniciar`)."""

from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

PASTA_MODELOS = Path(__file__).parent / "modelos_projeto"
LINHAS_GITIGNORE = [".venv/", "__pycache__/", ".claude/worktrees/"]
JA_EXISTIA = "mantido (já existia)"


def _ambiente() -> Environment:
    """Jinja2 com delimitadores `[[ ]]`, para não colidir com `${{ }}` do GitHub Actions."""
    return Environment(
        loader=FileSystemLoader(PASTA_MODELOS),
        variable_start_string="[[",
        variable_end_string="]]",
        comment_start_string="[#",
        comment_end_string="#]",
        undefined=StrictUndefined,
        keep_trailing_newline=True,
    )


def _escrever(caminho: Path, conteudo: str, forcar: bool) -> tuple[Path, str]:
    existia = caminho.exists()
    if existia and not forcar:
        return caminho, JA_EXISTIA
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding="utf-8")
    return caminho, "sobrescrito" if existia else "criado"


def _atualizar_gitignore(caminho: Path) -> tuple[Path, str]:
    existia = caminho.exists()
    linhas = caminho.read_text(encoding="utf-8").splitlines() if existia else []
    faltantes = [linha for linha in LINHAS_GITIGNORE if linha not in linhas]
    if existia and not faltantes:
        return caminho, JA_EXISTIA
    caminho.write_text("\n".join(linhas + faltantes) + "\n", encoding="utf-8")
    return caminho, "atualizado" if existia else "criado"


def iniciar(destino: Path, pacote: str, forcar: bool = False) -> list[tuple[Path, str]]:
    """Cria os arquivos do método em `destino`; devolve (arquivo, status) de cada um.

    Nunca sobrescreve um arquivo existente sem `forcar`. O `__init__.py` do pacote nunca é
    sobrescrito, pois pode conter código do usuário.
    """
    if not pacote.isidentifier():
        raise ValueError(f"nome de pacote inválido: {pacote!r}")
    destino = Path(destino)
    destino.mkdir(parents=True, exist_ok=True)
    ambiente = _ambiente()
    contexto = {"pacote": pacote, "projeto": destino.resolve().name}

    def renderizar(modelo: str) -> str:
        return ambiente.get_template(modelo).render(**contexto)

    def copiar(modelo: str) -> str:
        return (PASTA_MODELOS / modelo).read_text(encoding="utf-8")

    pacote_src = destino / "src" / pacote
    agentes = destino / ".claude" / "agents"
    plano = [
        (destino / "vcm.yaml", renderizar("vcm.yaml.j2")),
        (destino / "CLAUDE.md", renderizar("CLAUDE.md.j2")),
        (destino / "docs" / "estilo.md", copiar("estilo.md")),
        (agentes / "executor-sonnet.md", copiar("agentes/executor-sonnet.md")),
        (agentes / "executor-haiku.md", copiar("agentes/executor-haiku.md")),
        (pacote_src / "referencia.py", renderizar("referencia.py.j2")),
        (destino / "tests" / "test_referencia.py", renderizar("test_referencia.py.j2")),
        (destino / ".github" / "workflows" / "vcm.yml", copiar("vcm.yml")),
    ]
    resultado = []
    init = pacote_src / "__init__.py"
    resultado.append(_escrever(init, "", forcar=False))
    resultado.extend(_escrever(caminho, conteudo, forcar) for caminho, conteudo in plano)
    resultado.append(_atualizar_gitignore(destino / ".gitignore"))
    return resultado
