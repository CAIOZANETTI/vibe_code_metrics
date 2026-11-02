"""Repertório de ferramentas: leitura dos YAML e geração da página `docs/repertorio.md`.

A página é derivada (Python gera, o HTML apresenta): edite os YAML em `repertorio/` e rode
`vcm docs`, que regenera o Markdown e o HTML. A geração é determinística (ordem fixa).
"""

from __future__ import annotations

from pathlib import Path

import yaml

PAPEIS = {
    "calculo": "Cálculo numérico",
    "tabular": "Dados tabulares",
    "armazenamento": "Armazenamento",
    "validacao": "Validação e unidades",
    "geoespacial": "Geoespacial",
    "cad_3d": "CAD, BIM e 3D",
    "grafos": "Grafos",
    "intercambio": "Intercâmbio de dados",
    "documentos": "Documentos e OCR",
    "apresentacao": "Apresentação",
    "qualidade": "Qualidade e testes",
}
STATUS = {
    "em_uso": "em uso",
    "em_teste": "em teste",
    "candidato": "candidato",
    "rejeitado": "rejeitado",
}


def carregar(pasta: Path) -> list[dict]:
    """Todas as entradas `pasta/<papel>/<id>.yaml`, em ordem de papel e de nome."""
    ordem = {papel: i for i, papel in enumerate(PAPEIS)}
    entradas = [
        yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        for arquivo in sorted(pasta.glob("*/*.yaml"))
        if arquivo.parent.name != "skills"  # skills têm catálogo próprio
    ]
    return sorted(entradas, key=lambda e: (ordem.get(e["papel"], len(ordem)), e["nome"].lower()))


def _celula(valor) -> str:
    return "—" if valor in (None, "", []) else str(valor).replace("|", "\\|")


def _lista(titulo: str, itens) -> list[str]:
    if not itens:
        return []
    return [f"**{titulo}**", "", *[f"- {item}" for item in itens], ""]


def _ligacoes(entrada: dict) -> str:
    partes = []
    if entrada.get("compete_com"):
        partes.append("compete com " + ", ".join(f"`{i}`" for i in entrada["compete_com"]))
    if entrada.get("coopera_com"):
        partes.append("coopera com " + ", ".join(f"`{i}`" for i in entrada["coopera_com"]))
    return "; ".join(partes)


def markdown(pasta: Path) -> str:
    """Página do repertório: resumo por papel e premissas de cada ferramenta."""
    entradas = carregar(pasta)
    linhas = [
        "# Repertório de ferramentas",
        "",
        "> Premissas de uso de cada ferramenta: quando considerar, quando evitar e os cuidados.",
        "> Só se comparam ferramentas do **mesmo papel**; a escolha entre elas é tese, não gosto.",
        "> Licença e versão foram conferidas na fonte (PyPI e repositório) na data indicada.",
        "> Página gerada a partir de `repertorio/*/*.yaml` por `vcm docs`; edite os YAML.",
        "",
        "| Papel | Ferramentas |",
        "|---|---|",
    ]
    por_papel: dict[str, list[dict]] = {}
    for entrada in entradas:
        por_papel.setdefault(entrada["papel"], []).append(entrada)
    for papel, grupo in por_papel.items():
        nomes = ", ".join(e["nome"] for e in grupo)
        linhas.append(f"| {PAPEIS.get(papel, papel)} | {nomes} |")
    linhas.append("")

    for papel, grupo in por_papel.items():
        linhas += [
            f"## {PAPEIS.get(papel, papel)}",
            "",
            "| Ferramenta | Situação | Licença | Última versão | Verificado em |",
            "|---|---|---|---|---|",
        ]
        for e in grupo:
            nome = f"[{e['nome']}]({e['documentacao']})" if e.get("documentacao") else e["nome"]
            linhas.append(
                f"| {nome} | {STATUS.get(e.get('status'), _celula(e.get('status')))} "
                f"| {_celula(e.get('licenca'))} | {_celula(e.get('ultima_versao'))} "
                f"| {_celula(e.get('verificado_em'))} |"
            )
        linhas.append("")
        for e in grupo:
            linhas += [f"### {e['nome']}", "", e.get("descricao", ""), ""]
            ligacoes = _ligacoes(e)
            if ligacoes:
                linhas += [f"_{ligacoes.capitalize()}._", ""]
            linhas += _lista("Quando considerar", e.get("quando_considerar"))
            linhas += _lista("Quando evitar", e.get("quando_evitar"))
            linhas += _lista("Cuidados", e.get("cuidados"))
            if e.get("repositorio"):
                linhas += [f"Repositório: <{e['repositorio']}>", ""]
    return "\n".join(linhas).rstrip() + "\n"


# ---------------------------------------------------------------------------------------------
# Skills: catálogo próprio em repertorio/skills/, página docs/skills.md
# ---------------------------------------------------------------------------------------------

ORIGENS = {
    "projeto": "Do projeto (versionadas no repositório)",
    "embutida": "Da plataforma (disponíveis nas sessões do Claude)",
    "plugin": "De plugins instalados",
    "externa": "Externas (repositórios públicos)",
}
AGENTES = {"haiku": "Haiku", "sonnet": "Sonnet", "opus": "Opus", "qualquer": "qualquer"}


def carregar_skills(pasta: Path) -> list[dict]:
    """Entradas `pasta/skills/*.yaml`, em ordem de origem e de nome."""
    ordem = {origem: i for i, origem in enumerate(ORIGENS)}
    entradas = [
        yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        for arquivo in sorted((pasta / "skills").glob("*.yaml"))
    ]
    return sorted(entradas, key=lambda e: (ordem.get(e["origem"], len(ordem)), e["id"]))


def markdown_skills(pasta: Path) -> str:
    """Página das skills: o que são, onde ficam e o catálogo por origem."""
    entradas = carregar_skills(pasta)
    nomes_ferramentas = {e["id"]: e["nome"] for e in carregar(pasta)}
    linhas = [
        "# Skills",
        "",
        "> As ferramentas dizem **com o que** calcular; as skills dizem **como o agente conduz**",
        "> uma tarefa: o passo a passo, quem executa e os cuidados. Cada skill aponta as",
        "> ferramentas do [repertório](repertorio.md) que usa.",
        "> Página gerada a partir de `repertorio/skills/` por `vcm docs`; edite os YAML.",
        "",
    ]
    como = pasta / "skills" / "_como_funcionam.md"
    if como.exists():
        texto = como.read_text(encoding="utf-8").strip().splitlines()
        if texto and texto[0].startswith("# "):
            texto = texto[1:]  # o título vira seção desta página
        linhas += ["## Como as skills funcionam", "", *texto, ""]
    por_origem: dict[str, list[dict]] = {}
    for entrada in entradas:
        por_origem.setdefault(entrada["origem"], []).append(entrada)
    for origem, grupo in por_origem.items():
        linhas += [
            f"## {ORIGENS.get(origem, origem)}",
            "",
            "| Skill | Para quê | Agente sugerido | Situação |",
            "|---|---|---|---|",
        ]
        for e in grupo:
            linhas.append(
                f"| `{e['id']}` | {_celula(e.get('para_que'))} "
                f"| {AGENTES.get(e.get('agente_sugerido'), '—')} "
                f"| {STATUS.get(e.get('status'), _celula(e.get('status')))} |"
            )
        linhas.append("")
        for e in grupo:
            linhas += [f"### {e['nome']}", "", f"`{e['id']}` · {e.get('onde', '')}", ""]
            ferramentas = [
                nomes_ferramentas.get(f, f) for f in e.get("ferramentas_relacionadas") or []
            ]
            if ferramentas:
                linhas += ["_Ferramentas: " + ", ".join(ferramentas) + "._", ""]
            linhas += _lista("Quando usar", e.get("quando_usar"))
            linhas += _lista("Quando evitar", e.get("quando_evitar"))
            linhas += _lista("Cuidados", e.get("cuidados"))
            if e.get("licenca"):
                linhas += [f"Licença: {e['licenca']} (verificada em {e.get('verificado_em')})", ""]
    return "\n".join(linhas).rstrip() + "\n"
