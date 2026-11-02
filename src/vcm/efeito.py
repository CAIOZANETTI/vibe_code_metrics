"""Desempenho do próprio método: métricas antes × depois da adoção do `vcm`.

Estudo observacional no histórico do git de um projeto. Todo cálculo é feito aqui;
o HTML só apresenta os valores prontos.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from jinja2 import Environment, PackageLoader, select_autoescape

from vcm import formatacao as fmt
from vcm.balanco import METRICAS_PADRAO
from vcm.snapshot import COLUNAS_META, _git

# Abaixo de 5 commits de um lado, média e tendência não sustentam conclusão.
N_MINIMO_POR_LADO = 5
RUIDO_MINIMO = 0.02
DECISOES = ("REVERTER", "MANTER", "SEM_GANHO", "DECISAO_HUMANA")
METRICAS_GRAFICO = (
    "complexidade_media",
    "sloc_por_funcao",
    "cobertura_testes",
    "testes_falhando",
    "alertas_seguranca",
    "n_dependencias",
)


def commit_de_adocao(repo: Path) -> str | None:
    """Primeiro commit que adicionou o `vcm.yaml` (o mais antigo), ou None."""
    saida = _git(repo, "log", "--diff-filter=A", "--format=%H", "--", "vcm.yaml")
    hashes = saida.split()
    return hashes[-1] if hashes else None


def _em_utc(instante) -> pd.Timestamp:
    ts = pd.Timestamp(instante)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def _inclinacao(valores: pd.Series) -> float:
    """Inclinação por commit (polyfit grau 1 sobre a posição do commit)."""
    y = valores.to_numpy(dtype=float)
    x = np.arange(len(y), dtype=float)
    ok = ~np.isnan(y)
    if ok.sum() < 2:
        return float("nan")
    return float(np.polyfit(x[ok], y[ok], 1)[0])


def serie_util(serie: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Tira commits sem código (ex.: o commit inicial vazio), que distorcem a tendência "antes".

    Devolve a série filtrada e quantos commits saíram.
    """
    if "n_funcoes" not in serie.columns:
        return serie, 0
    com_codigo = pd.to_numeric(serie["n_funcoes"], errors="coerce").fillna(0) > 0
    return serie[com_codigo].reset_index(drop=True), int((~com_codigo).sum())


def comparar(serie: pd.DataFrame, data_adocao, n_minimo: int = N_MINIMO_POR_LADO) -> pd.DataFrame:
    """Por métrica julgada: médias, tendências e veredito antes × depois da adoção.

    Com menos de `n_minimo` commits de um dos lados, o veredito é "insuficiente".
    """
    instante = pd.to_datetime(serie["data_commit"], utc=True)
    lado_depois = (instante >= _em_utc(data_adocao)).to_numpy()
    nomes = [
        n
        for n, m in METRICAS_PADRAO.items()
        if m.sentido != 0 and n in serie.columns and n not in COLUNAS_META
    ]
    linhas = {}
    for nome in nomes:
        valores = pd.to_numeric(serie[nome], errors="coerce")
        antes, depois = valores[~lado_depois], valores[lado_depois]
        n_a, n_d = int(antes.notna().sum()), int(depois.notna().sum())
        media_a = float(antes.mean()) if n_a else float("nan")
        media_d = float(depois.mean()) if n_d else float("nan")
        escala = abs(media_a) if (n_a and media_a != 0.0) else 1.0
        variacao = (media_d - media_a) / escala
        metrica = METRICAS_PADRAO[nome]
        faixa = max(metrica.ruido_relativo, RUIDO_MINIMO)
        if n_a < n_minimo or n_d < n_minimo:
            veredito = "insuficiente"
        else:
            melhora = variacao * metrica.sentido
            veredito = "melhorou" if melhora > faixa else "piorou" if melhora < -faixa else "igual"
        linhas[nome] = {
            "n_antes": n_a,
            "n_depois": n_d,
            "media_antes": media_a,
            "media_depois": media_d,
            "tendencia_antes": _inclinacao(antes),
            "tendencia_depois": _inclinacao(depois),
            "variacao_pct": 100.0 * variacao,
            "veredito": veredito,
        }
    tabela = pd.DataFrame.from_dict(linhas, orient="index")
    tabela.index.name = "metrica"
    return tabela


def indicadores_processo(pasta_iteracoes: Path) -> dict:
    """Conta os cartões de iteração por decisão (REVERTER = problema pego antes de entrar)."""
    contagem = dict.fromkeys(DECISOES, 0)
    for arquivo in sorted(Path(pasta_iteracoes).glob("*.parquet")):
        tabela = pd.read_parquet(arquivo)
        if "decisao" in tabela.columns and len(tabela):
            decisao = str(tabela["decisao"].iloc[0])
            contagem[decisao] = contagem.get(decisao, 0) + 1
    contagem["total"] = sum(contagem.values())
    return contagem


def ressalvas(comparacao: pd.DataFrame, n_depois_min: int = N_MINIMO_POR_LADO) -> list[str]:
    """Frases de cautela geradas a partir dos números."""
    frases = []
    if comparacao.empty:
        frases.append("Nenhuma métrica julgada na série: nada a comparar.")
    else:
        n_depois = int(comparacao["n_depois"].max())
        n_antes = int(comparacao["n_antes"].max())
        if n_depois < n_depois_min:
            frases.append(f"Só {n_depois} commits depois da adoção: resultado inconclusivo")
        if n_antes < n_depois_min:
            frases.append(f"Só {n_antes} commits antes da adoção: sem base de comparação")
        n_insuf = int((comparacao["veredito"] == "insuficiente").sum())
        if n_insuf and n_depois >= n_depois_min and n_antes >= n_depois_min:
            frases.append(f"{n_insuf} métrica(s) com poucos pontos de um dos lados: insuficiente")
    frases.append(
        "Estudo observacional de um projeto: mudanças de escopo também mexem nas métricas"
    )
    frases.append("Correlação não é causa: o método não foi aplicado de forma controlada")
    return frases


def _figura(serie: pd.DataFrame, metrica: str, data_adocao) -> go.Figure:
    x = pd.to_datetime(serie["data_commit"], utc=True).dt.tz_localize(None)
    corte = _em_utc(data_adocao).tz_localize(None)
    figura = go.Figure(go.Scatter(x=x, y=serie[metrica], mode="lines+markers", name=metrica))
    figura.add_shape(
        type="line",
        x0=corte,
        x1=corte,
        y0=0,
        y1=1,
        yref="paper",
        line={"dash": "dash", "color": "#d1242f"},
    )
    figura.add_annotation(x=corte, y=1, yref="paper", text="adoção do vcm", showarrow=False)
    figura.update_layout(
        title=metrica, height=300, margin={"l": 50, "r": 20, "t": 50, "b": 40}, showlegend=False
    )
    return figura


def gerar_relatorio(
    serie: pd.DataFrame,
    comparacao: pd.DataFrame,
    processo: dict,
    ressalvas: list[str],
    saida: Path,
    adocao: dict,
) -> Path:
    """Grava o HTML do efeito do método. `adocao`: chaves projeto, commit e data."""
    tabela = [
        {
            "metrica": nome,
            "n_antes": int(r.n_antes),
            "n_depois": int(r.n_depois),
            "media_antes": fmt.numero(r.media_antes, 3),
            "media_depois": fmt.numero(r.media_depois, 3),
            "tendencia_antes": fmt.numero(r.tendencia_antes, 4),
            "tendencia_depois": fmt.numero(r.tendencia_depois, 4),
            "variacao": fmt.percentual(r.variacao_pct),
            "veredito": r.veredito,
        }
        for nome, r in comparacao.iterrows()
    ]
    instante = pd.to_datetime(serie["data_commit"], utc=True)
    corte = _em_utc(adocao["data"])
    graficos = []
    for metrica in METRICAS_GRAFICO:
        if metrica not in serie.columns or serie[metrica].notna().sum() == 0:
            continue
        graficos.append(
            pio.to_html(
                _figura(serie, metrica, adocao["data"]),
                include_plotlyjs="cdn" if not graficos else False,
                full_html=False,
            )
        )
    env = Environment(
        loader=PackageLoader("vcm", "templates"), autoescape=select_autoescape(["html"])
    )
    html = env.get_template("efeito.html.j2").render(
        projeto=adocao["projeto"],
        commit_adocao=str(adocao["commit"])[:7],
        data_adocao=str(adocao["data"])[:10],
        n_antes=int((instante < corte).sum()),
        n_depois=int((instante >= corte).sum()),
        ressalvas=ressalvas,
        tabela=tabela,
        graficos=graficos,
        processo=processo,
        decisoes=DECISOES,
    )
    saida = Path(saida)
    saida.parent.mkdir(parents=True, exist_ok=True)
    saida.write_text(html, encoding="utf-8")
    return saida
