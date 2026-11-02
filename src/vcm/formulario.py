"""Formulário padrão de interação: a forma fixa de toda resposta do agente ao humano.

O Python preenche os campos que vêm de dados (objetivo, onde estamos, tempo, gasto, desvios,
agentes das etapas abertas). Os campos de texto (o que estou fazendo, campo livre) ficam com
marcadores para o agente completar. O formulário é o mesmo em todo projeto com o vcm.
"""

from __future__ import annotations

import pandas as pd

from vcm import formatacao as fmt

MARCADOR = "…"

CAMPOS = (
    "O que estou fazendo",
    "Onde estamos",
    "Agentes",
    "Precisa de você",
    "Campo livre",
)


def _barra(percentual: float, largura: int = 10) -> str:
    """Barra de progresso em texto (█ feito, ░ a fazer)."""
    cheios = round(max(0.0, min(100.0, percentual)) / 100 * largura)
    return "█" * cheios + "░" * (largura - cheios)


def _gasto_usd(real: pd.DataFrame | None) -> float | None:
    """Soma do custo equivalente de API das etapas; None se não houver medição."""
    if real is None or "custo_usd" not in real or real["custo_usd"].isna().all():
        return None
    return float(real["custo_usd"].sum())


def _onde_estamos(rumo: dict, prog: dict, real: pd.DataFrame | None, tempo: dict | None) -> str:
    """Linha única: barra, etapas em andamento, próxima, tempo e gasto."""
    pct = float(prog["percentual"])
    abertas = [f"{e['id']} {e['nome']}" for e in rumo["etapas"] if e["status"] == "fazendo"]
    partes = [f"`{_barra(pct)} {fmt.numero(pct, 0)}%`"]
    partes.append("em andamento: " + ("; ".join(abertas) if abertas else "nenhuma etapa"))
    partes.append(f"próxima: {prog['proxima'] or 'nenhuma disponível'}")
    if tempo:
        partes.append(
            f"{fmt.numero(tempo['dias_corridos'], 2)} dias · "
            f"IA {fmt.numero(tempo['horas_relogio_ia'], 1)} h"
        )
    gasto = _gasto_usd(real)
    if gasto is not None:
        partes.append(f"US$ {fmt.numero(gasto, 2)}")
    return " · ".join(partes)


def _agentes(rumo: dict) -> list[str]:
    """Agente de cada etapa em andamento ou disponível, como linhas de tabela."""
    feitas = {e["id"] for e in rumo["etapas"] if e["status"] == "feito"}
    linhas = []
    for etapa in rumo["etapas"]:
        disponivel = etapa["status"] == "a_fazer" and all(d in feitas for d in etapa["depende_de"])
        if etapa["status"] == "fazendo" or disponivel:
            situacao = "trabalhando" if etapa["status"] == "fazendo" else "a seguir"
            linhas.append(f"| {etapa['agente']} | {etapa['id']} {etapa['nome']} | {situacao} |")
    return linhas


def _precisa_de_voce(desv: list[dict]) -> list[str]:
    """Desvios em aberto; cada um é uma decisão do humano."""
    if not desv:
        return ["- nada no momento"]
    return [f"- {d['tipo']}: {d['etapa'] + ': ' if d['etapa'] else ''}{d['detalhe']}" for d in desv]


def preencher(
    rumo: dict,
    prog: dict,
    real: pd.DataFrame | None = None,
    desv: list[dict] | None = None,
    tempo: dict | None = None,
    projeto: str | None = None,
) -> str:
    """Formulário em Markdown com os campos de dados preenchidos e os de texto marcados."""
    titulo = f"### Interação · {projeto}" if projeto else "### Interação"
    linhas = [
        titulo,
        "",
        f"**Objetivo:** {rumo['objetivo']}",
        "",
        f"**O que estou fazendo:** {MARCADOR}",
        "",
        f"**Onde estamos:** {_onde_estamos(rumo, prog, real, tempo)}",
        "",
        "**Agentes**",
        "",
        "| Agente | Etapa | Situação |",
        "|---|---|---|",
        *(_agentes(rumo) or ["| — | nenhuma etapa aberta | — |"]),
        "",
        "**Precisa de você**",
        "",
        *_precisa_de_voce(desv or []),
        "",
        f"**Campo livre:** {MARCADOR}",
    ]
    return "\n".join(linhas) + "\n"


def campos_faltando(texto: str) -> list[str]:
    """Campos obrigatórios ausentes numa resposta; vazio quando o formulário está completo."""
    return [c for c in CAMPOS if f"**{c}" not in texto]
