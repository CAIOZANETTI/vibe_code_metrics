"""Cartão da retrospectiva de iteração, em Markdown e HTML.

Todos os números são calculados e formatados aqui, em Python. O HTML só apresenta.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from jinja2 import Environment, PackageLoader, select_autoescape

from vcm import formatacao as fmt
from vcm.balanco import Decisao

PERGUNTAS = {
    "eficiente": "Ficou mais eficiente?",
    "deterministico": "Ficou mais determinístico?",
    "enxuto": "Ficou mais enxuto?",
    "robusto": "Ficou mais robusto?",
}

EXPLICACAO_DECISAO = {
    Decisao.REVERTER: "Uma restrição eliminatória piorou. A iteração deve ser revertida.",
    Decisao.MANTER: "Houve melhora e nenhuma métrica piorou além do ruído.",
    Decisao.SEM_GANHO: "Nada mudou além do ruído. Verificar convergência desta linha de trabalho.",
    Decisao.DECISAO_HUMANA: "Houve troca: algo melhorou e algo piorou. Cabe ao humano decidir.",
}

ICONE = {"melhorou": "▲ melhorou", "piorou": "▼ piorou", "igual": "= igual"}


def _linhas(tabela: pd.DataFrame) -> list[dict]:
    linhas = []
    for nome, r in tabela.iterrows():
        casas = 0 if float(r["antes"]).is_integer() and float(r["depois"]).is_integer() else 3
        linhas.append(
            {
                "metrica": nome,
                "pergunta": r["pergunta"],
                "eliminatoria": "sim" if r["eliminatoria"] else "",
                "antes": fmt.numero(r["antes"], casas),
                "depois": fmt.numero(r["depois"], casas),
                "variacao": fmt.percentual(r["variacao_pct"]),
                "veredito": ICONE[r["veredito"]],
                "classe": r["veredito"],
            }
        )
    return linhas


def _perdas(tabela: pd.DataFrame) -> list[str]:
    return list(tabela.index[tabela["veredito"] == "piorou"])


def contexto(resultado: dict) -> dict:
    tabela = resultado["tabela"]
    respostas = resultado["respostas"]
    perdas = _perdas(tabela)
    return {
        "base": str(resultado["base"])[:7],
        "alvo": str(resultado["alvo"])[:7],
        "mensagem": resultado.get("mensagem_alvo", ""),
        "decisao": resultado["decisao"].value,
        "explicacao": EXPLICACAO_DECISAO[resultado["decisao"]],
        "perguntas": [
            {"pergunta": texto, "resposta": respostas.get(chave, "sem medição")}
            for chave, texto in PERGUNTAS.items()
        ]
        + [
            {
                "pergunta": "Perdeu algo?",
                "resposta": ("sim: " + ", ".join(perdas)) if perdas else "não",
            }
        ],
        "linhas": _linhas(tabela),
    }


def markdown(resultado: dict) -> str:
    c = contexto(resultado)
    partes = [
        f"## Retrospectiva da iteração `{c['base']}` → `{c['alvo']}`",
        "",
        f"_{c['mensagem']}_" if c["mensagem"] else "",
        "",
        f"**Decisão proposta: {c['decisao']}**. {c['explicacao']}",
        "",
        "| Pergunta | Resposta |",
        "|---|---|",
        *[f"| {p['pergunta']} | {p['resposta']} |" for p in c["perguntas"]],
        "| Vale continuar nessa linha? | decisão humana, ver histórico |",
        "",
        "| Métrica | Pergunta | Eliminatória | Antes | Depois | Variação | Veredito |",
        "|---|---|---|---:|---:|---:|---|",
        *[
            f"| {r['metrica']} | {r['pergunta']} | {r['eliminatoria']} | {r['antes']} "
            f"| {r['depois']} | {r['variacao']} | {r['veredito']} |"
            for r in c["linhas"]
        ],
        "",
    ]
    return "\n".join(partes)


def html(resultado: dict) -> str:
    env = Environment(
        loader=PackageLoader("vcm", "templates"), autoescape=select_autoescape(["html"])
    )
    return env.get_template("cartao.html.j2").render(**contexto(resultado))


def gravar(resultado: dict, pasta: Path) -> dict[str, Path]:
    """Grava tabela (Parquet), cartão Markdown e cartão HTML da iteração."""
    pasta.mkdir(parents=True, exist_ok=True)
    nome = f"{str(resultado['base'])[:7]}_{str(resultado['alvo'])[:7]}"
    caminhos = {
        "parquet": pasta / f"{nome}.parquet",
        "md": pasta / f"{nome}.md",
        "html": pasta / f"{nome}.html",
    }
    tabela = resultado["tabela"].assign(decisao=resultado["decisao"].value)
    tabela.to_parquet(caminhos["parquet"])
    caminhos["md"].write_text(markdown(resultado), encoding="utf-8")
    caminhos["html"].write_text(html(resultado), encoding="utf-8")
    return caminhos
