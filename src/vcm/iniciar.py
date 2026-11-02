"""Adoção do método Vibe Code Metrics num projeto, em um passo (`vcm iniciar`)."""

from __future__ import annotations

import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined, select_autoescape

PASTA_MODELOS = Path(__file__).parent / "modelos_projeto"
LINHAS_GITIGNORE = [".venv/", "__pycache__/", ".claude/worktrees/"]
JA_EXISTIA = "mantido (já existia)"


# Skills do método instaladas em todo projeto (rumo e formulário de interação).
SKILLS_DO_METODO = ("vcm-rumo", "vcm-formulario")


def _ambiente() -> Environment:
    """Jinja2 com delimitadores `[[ ]]`, para não colidir com `${{ }}` do GitHub Actions."""
    return Environment(
        loader=FileSystemLoader(PASTA_MODELOS),
        variable_start_string="[[",
        variable_end_string="]]",
        comment_start_string="[#",
        comment_end_string="#]",
        undefined=StrictUndefined,
        trim_blocks=True,
        keep_trailing_newline=True,
        # Os modelos geram Python, YAML e Markdown: escapar como HTML os corromperia.
        # A política fica explícita: só modelos .html seriam escapados.
        autoescape=select_autoescape(enabled_extensions=("html",), default=False),
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


COMANDO_DO_GANCHO = "vcm formulario --verificar"
JSON_INVALIDO = "não alterado (JSON inválido)"


def _paradas(configuracao: dict) -> list:
    """Lista de hooks Stop da configuração; ValueError se a estrutura for inesperada."""
    ganchos = configuracao.get("hooks", {}) if isinstance(configuracao, dict) else None
    paradas = ganchos.get("Stop", []) if isinstance(ganchos, dict) else None
    if not isinstance(paradas, list):
        raise TypeError("estrutura inesperada")
    return paradas


def _tem_gancho(paradas: list) -> bool:
    """Já existe algum comando de `vcm formulario --verificar` no hook Stop?"""
    return any(
        COMANDO_DO_GANCHO in str(gancho.get("command", ""))
        for grupo in paradas
        for gancho in grupo.get("hooks", [])
    )


def _instalar_gancho(caminho: Path, modelo: str) -> tuple[Path, str]:
    """Cria `.claude/settings.json` ou acrescenta o hook Stop, preservando o resto.

    Nunca sobrescreve: nem `--forcar` apaga configurações do usuário.
    """
    if not caminho.exists():
        caminho.parent.mkdir(parents=True, exist_ok=True)
        caminho.write_text(modelo, encoding="utf-8")
        return caminho, "criado"
    try:
        atual = json.loads(caminho.read_text(encoding="utf-8"))
        paradas = _paradas(atual)
        if _tem_gancho(paradas):
            return caminho, JA_EXISTIA
    except (ValueError, TypeError, AttributeError):
        return caminho, JSON_INVALIDO
    paradas.extend(json.loads(modelo)["hooks"]["Stop"])
    atual.setdefault("hooks", {})["Stop"] = paradas
    caminho.write_text(json.dumps(atual, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return caminho, "atualizado"


def detectar_layout(destino: Path, pacote: str) -> str:
    """Devolve "raiz" se o pacote existente está na raiz (sem `src/`); senão "src"."""
    destino = Path(destino)
    if (destino / "src" / pacote).is_dir():
        return "src"
    if (destino / pacote / "__init__.py").is_file():
        return "raiz"
    return "src"


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
    layout = detectar_layout(destino, pacote)
    contexto = {
        "pacote": pacote,
        "projeto": destino.resolve().name,
        "pastas_fonte": pacote if layout == "raiz" else "src",
        "caminho_pacote": pacote if layout == "raiz" else f"src/{pacote}",
        "tem_pdca": (destino / "pdca").is_dir(),
    }

    def renderizar(modelo: str) -> str:
        return ambiente.get_template(modelo).render(**contexto)

    def copiar(modelo: str) -> str:
        return (PASTA_MODELOS / modelo).read_text(encoding="utf-8")

    pacote_src = destino / pacote if layout == "raiz" else destino / "src" / pacote
    agentes = destino / ".claude" / "agents"
    plano = [
        (destino / "vcm.yaml", renderizar("vcm.yaml.j2")),
        (destino / "CLAUDE.md", renderizar("CLAUDE.md.j2")),
        (destino / "docs" / "estilo.md", copiar("estilo.md")),
        (agentes / "executor-sonnet.md", copiar("agentes/executor-sonnet.md")),
        (agentes / "executor-haiku.md", copiar("agentes/executor-haiku.md")),
        *(
            (
                destino / ".claude" / "skills" / skill / "SKILL.md",
                copiar(f"skills/{skill}/SKILL.md"),
            )
            for skill in SKILLS_DO_METODO
        ),
        (pacote_src / "referencia.py", renderizar("referencia.py.j2")),
        (destino / "tests" / "test_referencia.py", renderizar("test_referencia.py.j2")),
        (destino / ".github" / "workflows" / "vcm.yml", copiar("vcm.yml")),
    ]
    resultado = []
    init = pacote_src / "__init__.py"
    resultado.append(_escrever(init, "", forcar=False))
    resultado.extend(_escrever(caminho, conteudo, forcar) for caminho, conteudo in plano)
    resultado.append(
        _instalar_gancho(destino / ".claude" / "settings.json", copiar("settings.json"))
    )
    resultado.append(_atualizar_gitignore(destino / ".gitignore"))
    return resultado
