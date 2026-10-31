"""Radar de semáforo da retrospectiva: estado absoluto e índice relativo por dimensão.

Todo o cálculo acontece aqui, em Python. O HTML/Plotly só desenham os valores prontos.

1. Semáforo de estado: cada métrica do snapshot "depois" recebe uma cor por limites
   (`limites_padrao.yaml`); a dimensão herda a pior cor entre suas métricas.
2. Índice da iteração: por dimensão, antes = 1,0 e depois = média geométrica da razão
   depois/antes orientada (maior = melhor) das métricas julgadas.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import yaml

from vcm import formatacao as fmt
from vcm.balanco import METRICAS_PADRAO

DIMENSOES = ["eficiente", "deterministico", "enxuto", "robusto"]
EMOJI = {"verde": "🟢", "amarelo": "🟡", "vermelho": "🔴", "cinza": "⚪"}
# Gravidade crescente; cinza só vale quando não há nenhuma outra cor.
_GRAVIDADE = {"verde": 0, "amarelo": 1, "vermelho": 2}
INDICE_MINIMO = 0.5
INDICE_MAXIMO = 1.5
ARQUIVO_LIMITES = Path(__file__).with_name("limites_padrao.yaml")
_TOLERANCIA = 1e-9


def carregar_limites(extra: dict | None = None) -> dict:
    """Limites padrão, com sobreposição por métrica vinda de `extra` (config do projeto)."""
    limites = yaml.safe_load(ARQUIVO_LIMITES.read_text(encoding="utf-8")) or {}
    limites = {nome: dict(regra) for nome, regra in limites.items()}
    for nome, regra in (extra or {}).items():
        limites[nome] = {**limites.get(nome, {}), **regra}
    return limites


def _regra_legivel(regra: dict | None) -> str:
    if not regra:
        return "sem limite definido"
    sinal = "≥" if regra["sentido"] > 0 else "≤"
    texto = f"verde {sinal} {fmt.numero(regra['verde'], 2)}"
    if regra.get("amarelo") is not None:
        texto += f"; amarelo {sinal} {fmt.numero(regra['amarelo'], 2)}"
    return texto + "; senão vermelho"


def _cor(valor: float, regra: dict | None) -> str:
    if regra is None or pd.isna(valor):
        return "cinza"
    sentido = regra["sentido"]
    # Orientar por `sentido` faz "maior é melhor" valer para os dois casos.
    v = valor * sentido
    if v >= regra["verde"] * sentido - _TOLERANCIA:
        return "verde"
    if regra.get("amarelo") is not None and v >= regra["amarelo"] * sentido - _TOLERANCIA:
        return "amarelo"
    return "vermelho"


def avaliar_estado(valores: pd.Series, limites: dict | None = None) -> pd.DataFrame:
    """Cor de cada métrica do catálogo presente em `valores`.

    Colunas: metrica (índice), dimensao, valor, cor, regra. Informativas e métricas sem
    limite ou sem medição ficam cinza.
    """
    limites = carregar_limites() if limites is None else limites
    linhas = []
    for nome, metrica in METRICAS_PADRAO.items():
        if nome not in valores.index:
            continue
        valor = float(valores[nome]) if pd.notna(valores[nome]) else float("nan")
        regra = None if metrica.sentido == 0 else limites.get(nome)
        linhas.append(
            {
                "metrica": nome,
                "dimensao": metrica.pergunta,
                "valor": valor,
                "cor": _cor(valor, regra),
                "regra": _regra_legivel(regra),
            }
        )
    return pd.DataFrame(linhas, columns=["metrica", "dimensao", "valor", "cor", "regra"]).set_index(
        "metrica"
    )


def cores_por_dimensao(estado: pd.DataFrame) -> pd.Series:
    """Pior cor entre as métricas de cada dimensão (cinza se todas cinza ou ausentes)."""
    gravidade = estado["cor"].map(_GRAVIDADE)  # cinza -> NaN, ignorado pelo max
    pior = gravidade.groupby(estado["dimensao"]).max().reindex(DIMENSOES)
    nomes = {v: k for k, v in _GRAVIDADE.items()}
    return pior.map(lambda g: nomes.get(g, "cinza")).rename("cor").rename_axis("dimensao")


def indices_iteracao(tabela_balanco: pd.DataFrame) -> pd.DataFrame:
    """Índice relativo por dimensão (antes = 1,0; > 1 é sempre melhor).

    Média geométrica de (depois/antes)**sentido das métricas julgadas. Ignora
    informativas, NaN e razões indefinidas (um só lado zero); antes = depois = 0 conta 1,0.
    `indice` guarda o valor sem limite (NaN sem métrica válida); `indice_desenho` fica em
    [0,5; 1,5] para o gráfico (1,0 quando não há métrica válida).
    """
    t = tabela_balanco
    sentido = np.array(
        [METRICAS_PADRAO[n].sentido if n in METRICAS_PADRAO else 0 for n in t.index], dtype=float
    )
    antes = t["antes"].to_numpy(dtype=float)
    depois = t["depois"].to_numpy(dtype=float)
    ambos_zero = (antes == 0) & (depois == 0)
    with np.errstate(divide="ignore", invalid="ignore"):
        razao = np.where(ambos_zero, 1.0, depois / antes)
    valida = (sentido != 0) & np.isfinite(razao) & (razao > 0)
    log_orientado = np.where(valida, sentido * np.log(np.where(valida, razao, 1.0)), 0.0)
    dados = pd.DataFrame(
        {"dimensao": t["pergunta"].to_numpy(), "log": log_orientado, "valida": valida}
    )
    soma = dados.groupby("dimensao")["log"].sum().reindex(DIMENSOES, fill_value=0.0)
    contagem = dados.groupby("dimensao")["valida"].sum().reindex(DIMENSOES, fill_value=0)
    tem = (contagem > 0).to_numpy()
    indice = np.where(tem, np.exp(soma.to_numpy() / np.where(tem, contagem.to_numpy(), 1)), np.nan)
    return pd.DataFrame(
        {
            "dimensao": DIMENSOES,
            "indice": indice,
            "indice_desenho": np.where(tem, np.clip(indice, INDICE_MINIMO, INDICE_MAXIMO), 1.0),
        }
    )


def rotulo_dimensao(dimensao: str, cor: str) -> str:
    """Ex.: 'robusto 🔴'."""
    return f"{dimensao} {EMOJI[cor]}"


def figura_radar(indices: pd.DataFrame, cores: pd.Series) -> go.Figure:
    """Radar polar com dois traços: antes (círculo 1,0) e depois (índice desenhado)."""
    rotulos = [rotulo_dimensao(d, cores.get(d, "cinza")) for d in indices["dimensao"]]
    antes = [1.0] * len(rotulos)
    depois = indices["indice_desenho"].astype(float).tolist()
    textos = [fmt.numero(v, 2) for v in indices["indice"]]
    figura = go.Figure()
    figura.add_trace(
        go.Scatterpolar(
            r=[*antes, antes[0]],
            theta=[*rotulos, rotulos[0]],
            name="antes (1,0)",
            mode="lines",
            line={"color": "#8a94a0", "dash": "dash"},
        )
    )
    figura.add_trace(
        go.Scatterpolar(
            r=[*depois, depois[0]],
            theta=[*rotulos, rotulos[0]],
            name="depois",
            mode="lines+markers",
            fill="toself",
            line={"color": "#1f6feb"},
            text=[*textos, textos[0]],
            hovertemplate="%{theta}: índice %{text}<extra></extra>",
        )
    )
    figura.update_layout(
        polar={"radialaxis": {"range": [0, INDICE_MAXIMO], "tickvals": [0.5, 1.0, 1.5]}},
        showlegend=True,
        margin={"l": 60, "r": 60, "t": 30, "b": 30},
        height=380,
    )
    return figura
