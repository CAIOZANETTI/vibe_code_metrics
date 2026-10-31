"""Gera `results/reports/T005.html`, autocontido (Plotly via CDN), a partir dos resultados."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from jinja2 import Environment, FileSystemLoader, select_autoescape

from vcm.prototipos.perda_de_carga import alternativa_numpy
from vcm.prototipos.perda_de_carga.dados import gerar_perfil

PASTA_RUNS_PADRAO = Path("results/runs/T005")
HTML_PADRAO = Path("results/reports/T005.html")
TOLERANCIA_M = 1e-9
N_PERFIL = 1_000
NOTA_MEMORIA = (
    "Memória medida com tracemalloc: só vê alocações Python/NumPy/pandas e subestima a "
    "memória nativa (Rust) do Polars. Referência 'numpy' (acima de 100.000 trechos) não valida "
    "o próprio NumPy."
)


def formatar(valor: float, casas: int = 2) -> str:
    """Formata número no padrão brasileiro: ponto de milhar e vírgula decimal."""
    texto = f"{valor:,.{casas}f}"
    return texto.replace(",", "\0").replace(".", ",").replace("\0", ".")


def formatar_cientifica(valor: float) -> str:
    """Notação científica com vírgula decimal (ex.: 1,2e-14)."""
    return f"{valor:.1e}".replace(".", ",")


def _p50(resumo: pd.DataFrame, alternativa: str, n_trechos: int, coluna: str) -> float:
    filtro = (resumo["alternativa"] == alternativa) & (resumo["n_trechos"] == n_trechos)
    return float(resumo.loc[filtro, coluna].iloc[0])


def avaliar_hipoteses(resumo: pd.DataFrame) -> list[dict[str, str]]:
    """Veredito de H1 a H3 a partir do resumo (critérios fixados em hypothesis.md)."""
    tamanhos = sorted(resumo["n_trechos"].unique())
    n_max = tamanhos[-1]
    pequenos = [n for n in tamanhos if n <= 1_000]

    # H1: Polars >= 20% mais rápido que NumPy no maior n; NumPy mais rápido em n <= 1000.
    razao = _p50(resumo, "polars", n_max, "tempo_p50_ms") / _p50(
        resumo, "numpy", n_max, "tempo_p50_ms"
    )
    numpy_vence_pequenos = all(
        min(
            resumo[resumo["n_trechos"] == n].set_index("alternativa")["tempo_p50_ms"].items(),
            key=lambda par: par[1],
        )[0]
        == "numpy"
        for n in pequenos
    )
    h1_grande = razao <= 0.8
    v1 = "confirmada" if h1_grande and numpy_vence_pequenos else "rejeitada"
    ev1 = (
        f"Em n = {formatar(n_max, 0)}, Polars/NumPy = {formatar(razao, 2)} no p50 "
        f"(limite 0,80); NumPy foi a mais rápida em todos os n ≤ 1.000: "
        f"{'sim' if numpy_vence_pequenos else 'não'}."
    )

    # H2: erro <= 1e-9 m onde há gabarito e hash único em todas as alternativas.
    com_gabarito = resumo[resumo["referencia"] == "gabarito"]
    erro_max = float(com_gabarito["erro_max_abs_m"].max())
    todas_deterministicas = bool(resumo["deterministico"].all())
    v2 = "confirmada" if erro_max <= TOLERANCIA_M and todas_deterministicas else "rejeitada"
    ev2 = (
        f"Erro máximo contra o gabarito: {formatar_cientifica(erro_max)} m "
        f"(tolerância {formatar_cientifica(TOLERANCIA_M)} m); determinismo (hash único) em "
        f"todas as combinações: {'sim' if todas_deterministicas else 'não'}."
    )

    # H3: menor pico (tracemalloc) = NumPy e menor SLOC = Polars, no maior n.
    final = resumo[resumo["n_trechos"] == n_max].set_index("alternativa")
    menor_pico = str(final["pico_mb"].idxmin())
    menor_sloc = str(final["sloc"].idxmin())
    v3 = "confirmada" if menor_pico == "numpy" and menor_sloc == "polars" else "rejeitada"
    ev3 = (
        f"Em n = {formatar(n_max, 0)}, menor pico (tracemalloc): {menor_pico} "
        f"({formatar(float(final['pico_mb'].min()), 1)} MB); menor SLOC: {menor_sloc} "
        f"({int(final['sloc'].min())} linhas)."
    )
    return [
        {
            "rotulo": "H1 (tempo).",
            "texto": "Em n máximo, o Polars puro é pelo menos 20% mais rápido que o NumPy; "
            "em n ≤ 1.000 o NumPy é o mais rápido.",
            "veredito": v1,
            "evidencia": ev1,
        },
        {
            "rotulo": "H2 (exatidão e determinismo).",
            "texto": "As três alternativas ficam a ≤ 1e-9 m do gabarito e têm hash único.",
            "veredito": v2,
            "evidencia": ev2,
        },
        {
            "rotulo": "H3 (memória e concisão).",
            "texto": "Em n máximo, NumPy tem o menor pico de memória e Polars o menor SLOC.",
            "veredito": v3,
            "evidencia": ev3,
        },
    ]


def montar_leitura(resumo: pd.DataFrame) -> list[str]:
    """Frases geradas a partir dos números: mais rápida por tamanho e por quanto."""
    frases = []
    for n_trechos in sorted(resumo["n_trechos"].unique()):
        grupo = resumo[resumo["n_trechos"] == n_trechos].sort_values("tempo_p50_ms")
        rapida = grupo.iloc[0]
        outras = [
            f"{formatar(float(linha.tempo_p50_ms / rapida.tempo_p50_ms), 1)}x mais lenta que "
            f"{rapida.alternativa} ({linha.alternativa}, {formatar(float(linha.tempo_p50_ms), 3)} ms)"
            for linha in grupo.iloc[1:].itertuples()
        ]
        frases.append(
            f"Com {formatar(n_trechos, 0)} trechos, a mais rápida foi {rapida.alternativa} "
            f"({formatar(float(rapida.tempo_p50_ms), 3)} ms no p50); " + "; ".join(outras) + "."
        )
    sloc = resumo.groupby("alternativa")["sloc"].first()
    frases.append(
        "SLOC da função calcular: "
        + ", ".join(f"{nome} {int(valor)}" for nome, valor in sloc.items())
        + "."
    )
    if (resumo["erro_max_abs_m"] > TOLERANCIA_M).any():
        frases.append("Há combinação acima da tolerância de 1e-9 m: alternativa eliminada.")
    else:
        frases.append("Nenhuma combinação excedeu a tolerância absoluta de 1e-9 m.")
    if not resumo["deterministico"].all():
        frases.append("Há combinação não determinística (mais de um hash): critério eliminatório.")
    else:
        frases.append("Todas as combinações geraram um único hash de saída nas repetições.")
    return frases


def _grafico_tempo(resumo: pd.DataFrame) -> str:
    figura = go.Figure()
    for nome, grupo in resumo.groupby("alternativa", sort=False):
        figura.add_trace(
            go.Scatter(
                x=grupo["n_trechos"],
                y=grupo["tempo_p50_ms"],
                mode="lines+markers",
                name=str(nome),
            )
        )
    figura.update_layout(
        xaxis={"title": "Número de trechos", "type": "log"},
        yaxis={"title": "Tempo p50 (ms)", "type": "log"},
        separators=",.",
        template="plotly_white",
    )
    return pio.to_html(figura, include_plotlyjs="cdn", full_html=False)


def _grafico_perfil(n_trechos: int) -> str:
    perfil = gerar_perfil(n_trechos)
    saida = alternativa_numpy.calcular(
        perfil, perfil.attrs["vazao_m3s"], perfil.attrs["cota_reservatorio_m"]
    )
    distancia_m = perfil["comprimento_m"].cumsum()
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(x=distancia_m, y=perfil["cota_terreno_m"], mode="lines", name="Terreno")
    )
    figura.add_trace(
        go.Scatter(
            x=distancia_m,
            y=saida["cota_piezometrica_m"],
            mode="lines",
            name="Linha piezométrica",
        )
    )
    figura.update_layout(
        xaxis={"title": "Distância (m)"},
        yaxis={"title": "Cota (m)"},
        separators=",.",
        template="plotly_white",
    )
    return pio.to_html(figura, include_plotlyjs=False, full_html=False)


def _tabela(resumo: pd.DataFrame) -> tuple[list[str], list[list[str]]]:
    cabecalhos = [
        "Alternativa",
        "n trechos",
        "p50 (ms)",
        "p95 (ms)",
        "Pico (MB)",
        "Erro máx. (m)",
        "Referência",
        "Determinístico",
        "SLOC",
    ]
    linhas = [
        [
            str(linha.alternativa),
            formatar(linha.n_trechos, 0),
            formatar(linha.tempo_p50_ms, 3),
            formatar(linha.tempo_p95_ms, 3),
            formatar(linha.pico_mb, 2),
            formatar_cientifica(linha.erro_max_abs_m),
            str(linha.referencia),
            "sim" if linha.deterministico else "não",
            str(int(linha.sloc)),
        ]
        for linha in resumo.sort_values(["n_trechos", "alternativa"]).itertuples()
    ]
    return cabecalhos, linhas


def gerar_relatorio(
    pasta_runs: Path | str = PASTA_RUNS_PADRAO,
    caminho_html: Path | str = HTML_PADRAO,
    n_perfil: int = N_PERFIL,
) -> Path:
    """Lê `resumo.parquet`, gera o HTML e devolve o caminho."""
    resumo = pd.read_parquet(Path(pasta_runs) / "resumo.parquet")
    cabecalhos, linhas = _tabela(resumo)
    ambiente = Environment(
        loader=FileSystemLoader(Path(__file__).parent),
        autoescape=select_autoescape(["html", "j2"]),
    )
    html = ambiente.get_template("relatorio.html.j2").render(
        titulo="T005 — Perda de carga numa adutora de 5 km: NumPy x Polars x híbrida",
        status="inconclusiva_preliminar",
        hipoteses=avaliar_hipoteses(resumo),
        cabecalhos=cabecalhos,
        linhas=linhas,
        nota_memoria=NOTA_MEMORIA,
        grafico_tempo=_grafico_tempo(resumo),
        grafico_perfil=_grafico_perfil(n_perfil),
        n_perfil=formatar(n_perfil, 0),
        leitura=montar_leitura(resumo),
    )
    destino = Path(caminho_html)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(html, encoding="utf-8")
    return destino
