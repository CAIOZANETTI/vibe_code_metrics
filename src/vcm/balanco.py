"""Retrospectiva de iteração: compara métricas antes × depois e propõe uma decisão.

Responde, com números, às perguntas feitas a cada implementação:
ficou mais eficiente? mais determinístico? mais enxuto? mais robusto? perdeu algo?

A decisão proposta segue a regra da metodologia:
1. restrição eliminatória piorou        -> REVERTER
2. algo melhorou e nada piorou          -> MANTER
3. nada mudou além do ruído             -> SEM_GANHO (verificar convergência)
4. houve troca (melhorou X, piorou Y)   -> DECISAO_HUMANA
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class Metrica:
    nome: str
    sentido: int  # +1 = maior é melhor; -1 = menor é melhor; 0 = informativa (não julgada)
    pergunta: str  # qual provocação da retrospectiva ela responde
    eliminatoria: bool = False
    ruido_relativo: float = 0.0  # variação relativa considerada ruído (estimar por repetições)
    ruido_absoluto: float = 0.0  # piso absoluto, na unidade da métrica (ex.: 5 ms)


METRICAS_PADRAO: dict[str, Metrica] = {
    m.nome: m
    for m in [
        # Cálculos de poucos ms oscilam mais de 20% entre execuções: piso absoluto de 5 ms.
        Metrica("tempo_referencia_ms", -1, "eficiente", ruido_relativo=0.15, ruido_absoluto=5.0),
        Metrica("tempo_p50_ms", -1, "eficiente", ruido_relativo=0.05),
        Metrica("tempo_p95_ms", -1, "eficiente", ruido_relativo=0.10),
        Metrica("pico_ram_mb", -1, "eficiente", ruido_relativo=0.03, ruido_absoluto=2.0),
        Metrica("custo_usd", -1, "eficiente", ruido_relativo=0.0),
        Metrica("frac_execucoes_identicas", +1, "deterministico", eliminatoria=True),
        Metrica("cobertura_deterministica", +1, "deterministico"),
        # SLOC bruto cresce com toda funcionalidade nova: é informativo. O julgamento de
        # "enxuto" usa a densidade (SLOC por função), a complexidade e as dependências.
        Metrica("sloc", 0, "enxuto"),
        Metrica("n_funcoes", 0, "enxuto"),
        Metrica("sloc_por_funcao", -1, "enxuto", ruido_relativo=0.02),
        Metrica("complexidade_media", -1, "enxuto", ruido_relativo=0.01),
        Metrica("n_dependencias", -1, "enxuto"),
        Metrica("testes_total", 0, "robusto"),
        Metrica("tempo_testes_s", 0, "eficiente"),
        Metrica("testes_falhando", -1, "robusto", eliminatoria=True),
        Metrica("arquivos_com_erro", -1, "robusto"),
        Metrica("cobertura_testes", +1, "robusto", ruido_relativo=0.005),
        Metrica("mutation_score", +1, "robusto", ruido_relativo=0.01),
        Metrica("alertas_seguranca", -1, "robusto", eliminatoria=True),
    ]
}


class Decisao(str, Enum):
    REVERTER = "REVERTER"
    MANTER = "MANTER"
    SEM_GANHO = "SEM_GANHO"
    DECISAO_HUMANA = "DECISAO_HUMANA"


def balanco(
    antes: pd.Series,
    depois: pd.Series,
    metricas: dict[str, Metrica] | None = None,
    ruido_medido: pd.Series | None = None,
) -> pd.DataFrame:
    """Tabela antes × depois com variação e veredito por métrica.

    Só entram métricas presentes nos dois lados e conhecidas no catálogo.
    `ruido_medido` (de `vcm.ruido`): por métrica, vale o maior entre o ruído do
    catálogo e o medido por repetição.
    """
    catalogo = METRICAS_PADRAO if metricas is None else metricas
    nomes = [n for n in catalogo if n in antes.index and n in depois.index]
    if not nomes:
        raise ValueError("nenhuma métrica em comum entre 'antes', 'depois' e o catálogo")

    a = antes.loc[nomes].astype(float)
    d = depois.loc[nomes].astype(float)
    sentido = pd.Series({n: catalogo[n].sentido for n in nomes}, dtype=float)
    ruido = pd.Series({n: catalogo[n].ruido_relativo for n in nomes}, dtype=float)
    if ruido_medido is not None:
        medido = ruido_medido.reindex(nomes).fillna(0.0).astype(float)
        ruido = np.maximum(ruido, medido)
    # Piso absoluto convertido para relativo na escala de cada métrica.
    escala_ruido = a.abs().where(a != 0, 1.0)
    piso = pd.Series({n: catalogo[n].ruido_absoluto for n in nomes}, dtype=float) / escala_ruido
    ruido = np.maximum(ruido, piso)

    # Escala: |antes|; quando antes == 0 a variação é absoluta (evita divisão por zero).
    escala = a.abs().where(a != 0, 1.0)
    variacao = (d - a) / escala
    melhora = variacao * sentido
    veredito = np.select(
        [sentido == 0, melhora > ruido, melhora < -ruido],
        ["info", "melhorou", "piorou"],
        default="igual",
    )

    return pd.DataFrame(
        {
            "pergunta": [catalogo[n].pergunta for n in nomes],
            "eliminatoria": [catalogo[n].eliminatoria for n in nomes],
            "antes": a,
            "depois": d,
            "variacao_pct": 100.0 * variacao,
            "ruido_pct": 100.0 * ruido,
            "veredito": veredito,
        },
        index=pd.Index(nomes, name="metrica"),
    )


def decidir(tabela: pd.DataFrame) -> Decisao:
    """Aplica a regra de decisão da metodologia sobre a tabela de `balanco`."""
    piorou = tabela["veredito"] == "piorou"
    melhorou = tabela["veredito"] == "melhorou"
    if (piorou & tabela["eliminatoria"]).any():
        return Decisao.REVERTER
    if piorou.any():
        return Decisao.DECISAO_HUMANA
    if melhorou.any():
        return Decisao.MANTER
    return Decisao.SEM_GANHO


def respostas(tabela: pd.DataFrame) -> pd.Series:
    """Resume a tabela por pergunta: 'sim', 'não', 'misto' ou 'igual'."""

    def resumo(v: pd.Series) -> str:
        m, p = (v == "melhorou").any(), (v == "piorou").any()
        if m and p:
            return "misto"
        if m:
            return "sim"
        if p:
            return "não"
        return "igual"

    julgadas = tabela[tabela["veredito"] != "info"]
    return julgadas.groupby("pergunta", sort=False)["veredito"].agg(resumo)


def convergiu(historico_melhora: pd.Series, janela: int = 3, limiar: float = 0.0) -> bool:
    """Critério de parada (como num método iterativo): as últimas `janela`
    iterações não trouxeram melhora acima de `limiar`.

    `historico_melhora`: melhora líquida por iteração (ex.: nº de métricas que
    melhoraram menos as que pioraram), em ordem cronológica.
    """
    if len(historico_melhora) < janela:
        return False
    return bool((historico_melhora.iloc[-janela:] <= limiar).all())
