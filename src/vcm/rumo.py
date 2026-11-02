"""Rumo do desenvolvimento: WBS versionada (`rumo.yaml`) comparada com o que aconteceu.

O plano (objetivo, etapas, entregáveis, estimativas) vive no repositório. O realizado vem dos
logs de sessão (tokens, tempo) e do git (arquivos tocados). Python calcula tudo; o HTML só exibe.
"""

from __future__ import annotations

import fnmatch
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
import yaml
from jinja2 import Environment, PackageLoader

from vcm import formatacao as fmt
from vcm.coletores import sessoes
from vcm.snapshot import _git

STATUS_VALIDOS = ("a_fazer", "fazendo", "feito", "bloqueado", "cancelado")
AGENTES_VALIDOS = ("haiku", "sonnet", "opus", "humano")
SIMBOLOS = {"feito": "✅", "fazendo": "🔄", "a_fazer": "⏳", "bloqueado": "⛔", "cancelado": "✖"}
LIMITE_ESTOURO = 1.5
LIMITE_PARADA = 2.0
IGNORADOS = ("rumo.yaml", "results/*", "docs/index.html", "uv.lock")


def _para_utc(valor: object) -> pd.Timestamp | None:
    """Converte texto ISO 8601 (ou datetime) em Timestamp UTC; vazio vira None."""
    if valor is None or valor == "":
        return None
    instante = pd.Timestamp(valor)
    if instante.tzinfo is None:
        return instante.tz_localize("UTC")
    return instante.tz_convert("UTC")


def _iso(instante: datetime) -> str:
    return instante.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


_PADROES_ETAPA = {
    "agente": "humano",
    "status": "a_fazer",
    "inicio": None,
    "fim": None,
}
# (campo, valores aceitos): validados na ordem, com a mesma mensagem de erro
_ESCOLHAS_ETAPA = (("status", STATUS_VALIDOS), ("agente", AGENTES_VALIDOS))
_CAMPOS_NUMERICOS_ETAPA = ("estimativa_min", "estimativa_tokens")
_CAMPOS_DATA_ETAPA = ("inicio", "fim")


def _ler_yaml_do_rumo(arquivo: Path) -> dict:
    """Lê o YAML e garante que a raiz é um mapa."""
    if not arquivo.exists():
        raise ValueError(f"arquivo de rumo não encontrado: {arquivo}")
    try:
        rumo = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    except yaml.YAMLError as erro:
        raise ValueError(f"YAML inválido em {arquivo}: {erro}") from erro
    if not isinstance(rumo, dict):
        raise ValueError(f"{arquivo} deve conter um mapa com objetivo e etapas")  # noqa: TRY004
    return rumo


def _validar_raiz_do_rumo(rumo: dict) -> list:
    """Valida objetivo e etapas, aplica os padrões da raiz e devolve a lista de etapas."""
    if not str(rumo.get("objetivo") or "").strip():
        raise ValueError("o rumo precisa de um 'objetivo'")
    etapas = rumo.get("etapas")
    if not isinstance(etapas, list) or not etapas:
        raise ValueError("o rumo precisa de ao menos uma etapa em 'etapas'")
    rumo["criterio_de_pronto"] = rumo.get("criterio_de_pronto") or []
    rumo.setdefault("base", None)
    rumo["historico"] = rumo.get("historico") or []
    return etapas


def _aplicar_padroes_da_etapa(etapa: dict, etapa_id: str) -> None:
    """Preenche os campos opcionais da etapa e normaliza as listas."""
    etapa["id"] = etapa_id
    etapa.setdefault("nome", etapa_id)
    etapa["entregaveis"] = list(etapa.get("entregaveis") or [])
    etapa["depende_de"] = [str(d) for d in (etapa.get("depende_de") or [])]
    for campo, padrao in _PADROES_ETAPA.items():
        etapa.setdefault(campo, padrao)


def _validar_numeros_da_etapa(etapa: dict) -> None:
    for campo in _CAMPOS_NUMERICOS_ETAPA:
        valor = etapa.get(campo, 0)
        if isinstance(valor, bool) or not isinstance(valor, (int, float)) or valor < 0:
            raise ValueError(f"etapa {etapa['id']}: '{campo}' deve ser número maior ou igual a 0")
        etapa[campo] = valor


def _validar_datas_da_etapa(etapa: dict) -> None:
    for campo in _CAMPOS_DATA_ETAPA:
        try:
            _para_utc(etapa[campo])
        except (ValueError, TypeError) as erro:
            raise ValueError(f"etapa {etapa['id']}: '{campo}' não é uma data ISO 8601") from erro


def _validar_etapa(etapa: object, posicao: int, ids_vistos: list[str]) -> None:
    """Valida uma etapa na ordem: id, repetição, padrões, escolhas, números e datas."""
    if not isinstance(etapa, dict) or not str(etapa.get("id") or "").strip():
        raise ValueError(f"etapa {posicao} sem 'id'")
    etapa_id = str(etapa["id"])
    if etapa_id in ids_vistos:
        raise ValueError(f"id de etapa repetido: {etapa_id}")
    ids_vistos.append(etapa_id)
    _aplicar_padroes_da_etapa(etapa, etapa_id)
    for campo, validos in _ESCOLHAS_ETAPA:
        if etapa[campo] not in validos:
            raise ValueError(
                f"etapa {etapa_id}: {campo} '{etapa[campo]}' inválido "
                f"(use um de {', '.join(validos)})"
            )
    _validar_numeros_da_etapa(etapa)
    _validar_datas_da_etapa(etapa)


def carregar(arquivo: Path) -> dict:
    """Lê e valida o `rumo.yaml`; erros em português com o id da etapa."""
    rumo = _ler_yaml_do_rumo(Path(arquivo))
    etapas = _validar_raiz_do_rumo(rumo)
    ids: list[str] = []
    for posicao, etapa in enumerate(etapas, start=1):
        _validar_etapa(etapa, posicao, ids)
    for etapa in etapas:
        for dependencia in etapa["depende_de"]:
            if dependencia not in ids:
                raise ValueError(f"etapa {etapa['id']}: depende_de '{dependencia}', que não existe")
    return rumo


def modelo(objetivo: str) -> str:
    """Texto YAML de um rumo inicial com uma etapa de exemplo."""
    rumo = {
        "objetivo": objetivo,
        "criterio_de_pronto": ["testes passando", "balanço do vcm sem REVERTER"],
        "base": "main",
        "etapas": [
            {
                "id": "E1",
                "nome": "Primeira etapa (edite)",
                "entregaveis": ["tests/test_exemplo.py"],
                "depende_de": [],
                "agente": "sonnet",
                "estimativa_min": 30,
                "estimativa_tokens": 150000,
                "status": "a_fazer",
                "inicio": None,
                "fim": None,
            }
        ],
        "historico": [],
    }
    return yaml.safe_dump(rumo, sort_keys=False, allow_unicode=True)


def marcar(arquivo: Path, etapa_id: str, status: str, agora: datetime | None = None) -> dict:
    """Muda o status de uma etapa, preenche `inicio`/`fim` (UTC) e regrava o YAML."""
    if status not in STATUS_VALIDOS:
        raise ValueError(f"status '{status}' inválido (use um de {', '.join(STATUS_VALIDOS)})")
    rumo = carregar(arquivo)
    etapa = next((e for e in rumo["etapas"] if e["id"] == etapa_id), None)
    if etapa is None:
        raise ValueError(f"etapa '{etapa_id}' não existe no rumo")
    agora = agora or datetime.now(UTC)
    if status == "fazendo":
        if not etapa["inicio"]:
            etapa["inicio"] = _iso(agora)
        etapa["fim"] = None
    elif status in ("feito", "cancelado"):
        if not etapa["inicio"] and status == "feito":
            etapa["inicio"] = _iso(agora)
        etapa["fim"] = _iso(agora)
    etapa["status"] = status
    Path(arquivo).write_text(
        yaml.safe_dump(rumo, sort_keys=False, allow_unicode=True), encoding="utf-8"
    )
    return etapa


def progresso(rumo: dict) -> dict:
    """% concluído ponderado pela estimativa de tempo, etapas por status e próxima etapa."""
    etapas = rumo["etapas"]
    contagem = {s: sum(e["status"] == s for e in etapas) for s in STATUS_VALIDOS}
    validas = [e for e in etapas if e["status"] != "cancelado"]
    pesos = np.array([float(e["estimativa_min"]) for e in validas])
    if pesos.sum() <= 0:
        pesos = np.ones(len(validas))
    fator = np.array([{"feito": 1.0, "fazendo": 0.5}.get(e["status"], 0.0) for e in validas])
    percentual = float((pesos * fator).sum() / pesos.sum() * 100) if len(validas) else 0.0
    feitas = {e["id"] for e in etapas if e["status"] == "feito"}
    proxima = next(
        (
            e["id"]
            for e in etapas
            if e["status"] == "a_fazer" and all(d in feitas for d in e["depende_de"])
        ),
        None,
    )
    return {"percentual": percentual, "por_status": contagem, "proxima": proxima}


def real_por_etapa(
    rumo: dict,
    chamadas: pd.DataFrame,
    raiz_repo: Path,
    agora: datetime | None = None,
    precos: dict | None = None,
) -> pd.DataFrame:
    """Chamadas, tokens, custo e duração reais por etapa, comparados com a estimativa."""
    agora_ts = pd.Timestamp(agora or datetime.now(UTC))
    agora_ts = (
        agora_ts.tz_localize("UTC") if agora_ts.tzinfo is None else agora_ts.tz_convert("UTC")
    )
    raiz = str(Path(raiz_repo).resolve())
    cwd = chamadas["cwd"].fillna("").astype(str)
    dentro = (cwd == raiz) | cwd.str.startswith(raiz + "/")
    # Tokens "trabalhados": entrada, saída e escrita de cache. A leitura de cache (o contexto
    # relido a cada resposta) fica de fora: domina a contagem, custa pouco e já entra no custo.
    colunas_trabalho = [c for c in sessoes.COLUNAS_TOTAL if c != "tokens_cache_leitura"]
    tokens_total = chamadas[colunas_trabalho].sum(axis=1)
    modelos = chamadas["modelo"].fillna("").astype(str) if "modelo" in chamadas else None
    custo = sessoes.custo_usd(chamadas, precos) if precos and len(chamadas) else None
    linhas = []
    for etapa in rumo["etapas"]:
        inicio = _para_utc(etapa["inicio"])
        fim = _para_utc(etapa["fim"]) or agora_ts
        linha = {
            "id": etapa["id"],
            "chamadas": np.nan,
            "tokens_real": np.nan,
            "custo_usd": np.nan,
            "duracao_min": np.nan,
            "horas_ia": np.nan,
        }
        if inicio is not None:
            na_janela = dentro & (chamadas["inicio"] >= inicio) & (chamadas["inicio"] <= fim)
            # Etapas simultâneas não dividem as mesmas chamadas: cada etapa fica com as do
            # modelo do seu agente (ex.: "sonnet" -> claude-sonnet-*).
            if modelos is not None and etapa.get("agente") in ("haiku", "sonnet", "opus", "fable"):
                na_janela = na_janela & modelos.str.contains(etapa["agente"], regex=False)
            linha["chamadas"] = int(na_janela.sum())
            linha["tokens_real"] = int(tokens_total[na_janela].sum())
            if custo is not None:
                linha["custo_usd"] = float(custo[na_janela].sum(min_count=1))
            linha["duracao_min"] = (fim - inicio).total_seconds() / 60
            linha["horas_ia"] = sessoes.tempo_ativo(chamadas[na_janela])["horas_relogio_ia"]
        linhas.append(linha)
    real = pd.DataFrame(linhas)
    estimado_tokens = pd.Series(
        [float(e["estimativa_tokens"]) for e in rumo["etapas"]], dtype="float64"
    )
    estimado_min = pd.Series([float(e["estimativa_min"]) for e in rumo["etapas"]], dtype="float64")
    real["estimativa_tokens"] = estimado_tokens
    real["estimativa_min"] = estimado_min
    real["razao_tokens"] = real["tokens_real"] / estimado_tokens.where(estimado_tokens > 0)
    real["razao_tempo"] = real["duracao_min"] / estimado_min.where(estimado_min > 0)
    return real


def tempo_do_rumo(
    rumo: dict, chamadas: pd.DataFrame, raiz_repo: Path, agora: datetime | None = None
) -> dict | None:
    """Tempo do objetivo: calendário (do primeiro início ao último fim, ou agora se há etapa
    aberta) e horas produtivas da IA nas chamadas feitas no repositório nesse período."""
    inicios = [_para_utc(e["inicio"]) for e in rumo["etapas"] if e["inicio"]]
    if not inicios:
        return None
    agora_ts = pd.Timestamp(agora or datetime.now(UTC))
    agora_ts = (
        agora_ts.tz_localize("UTC") if agora_ts.tzinfo is None else agora_ts.tz_convert("UTC")
    )
    abertas = any(e["status"] in ("a_fazer", "fazendo", "bloqueado") for e in rumo["etapas"])
    fins = [_para_utc(e["fim"]) for e in rumo["etapas"] if e["fim"]]
    inicio = min(inicios)
    fim = agora_ts if abertas or not fins else max(fins)
    raiz = str(Path(raiz_repo).resolve())
    cwd = chamadas["cwd"].fillna("").astype(str)
    dentro = (cwd == raiz) | cwd.str.startswith(raiz + "/")
    janela = dentro & (chamadas["inicio"] >= inicio) & (chamadas["inicio"] <= fim)
    ativo = sessoes.tempo_ativo(chamadas[janela])
    return {
        "inicio": inicio,
        "fim": fim,
        "em_andamento": abertas,
        "dias_corridos": (fim - inicio).total_seconds() / 86400,
        "horas_corridas": (fim - inicio).total_seconds() / 3600,
        "horas_relogio_ia": ativo["horas_relogio_ia"],
        "horas_agente": ativo["horas_agente"],
        "paralelismo": ativo["paralelismo"],
    }


def _texto_tempo(tempo: dict | None) -> list[str]:
    """Linhas de texto (pt-BR) do bloco de tempo, para Markdown e HTML."""
    if not tempo:
        return ["Nenhuma etapa iniciada."]
    fim = (
        "agora (em andamento)" if tempo["em_andamento"] else tempo["fim"].strftime("%d/%m/%Y %H:%M")
    )
    paralelismo = (
        f" · paralelismo {fmt.numero(tempo['paralelismo'], 1)}×"
        if pd.notna(tempo["paralelismo"])
        else ""
    )
    return [
        f"Início {tempo['inicio'].strftime('%d/%m/%Y %H:%M')} UTC · fim {fim}",
        (
            f"{fmt.numero(tempo['dias_corridos'], 2)} dias corridos "
            f"({fmt.numero(tempo['horas_corridas'], 1)} h de calendário)"
        ),
        (
            f"IA trabalhando: {fmt.numero(tempo['horas_relogio_ia'], 1)} h de relógio · "
            f"{fmt.numero(tempo['horas_agente'], 1)} h de agente{paralelismo}"
        ),
    ]


def _arquivos_alterados(raiz_repo: Path, base: str | None) -> list[str]:
    """Arquivos alterados desde a base (commits) mais os não commitados."""
    nomes: set[str] = set()
    if base:
        try:
            saida = _git(raiz_repo, "diff", "--name-only", f"{base}...HEAD")
            nomes.update(linha for linha in saida.splitlines() if linha)
        except RuntimeError:
            pass
    bruto = subprocess.run(
        ["git", "-C", str(raiz_repo), "status", "--porcelain", "-uall"],
        check=False,
        capture_output=True,
        text=True,
    ).stdout
    for linha in bruto.splitlines():
        caminho = linha[3:].strip()
        if " -> " in caminho:
            caminho = caminho.split(" -> ")[-1]
        if caminho:
            nomes.add(caminho.strip('"'))
    return sorted(nomes)


def _entregavel_existe(raiz_repo: Path, padrao: str) -> bool:
    if any(c in padrao for c in "*?["):
        return any(raiz_repo.glob(padrao))
    return (raiz_repo / padrao).exists()


def desvios(rumo: dict, raiz_repo: Path, real: pd.DataFrame) -> list[dict]:
    """Desvios do plano: fora do plano, estouro, parada e entregável ausente."""
    raiz_repo = Path(raiz_repo)
    achados: list[dict] = []
    padroes = [p for e in rumo["etapas"] for p in e["entregaveis"]]
    for arquivo in _arquivos_alterados(raiz_repo, rumo.get("base")):
        if any(fnmatch.fnmatch(arquivo, p) for p in IGNORADOS):
            continue
        if not any(fnmatch.fnmatch(arquivo, p) for p in padroes):
            achados.append(
                {
                    "tipo": "fora do plano",
                    "etapa": None,
                    "detalhe": f"{arquivo} alterado sem pertencer a nenhum entregável",
                }
            )
    por_id = real.set_index("id")
    for etapa in rumo["etapas"]:
        r = por_id.loc[etapa["id"]]
        for coluna, rotulo in (("razao_tokens", "tokens"), ("razao_tempo", "tempo")):
            razao = r[coluna]
            if pd.notna(razao) and razao > LIMITE_ESTOURO:
                achados.append(
                    {
                        "tipo": "estouro",
                        "etapa": etapa["id"],
                        "detalhe": f"{rotulo} real é {fmt.numero(float(razao), 1)}× o estimado",
                    }
                )
        if etapa["status"] == "fazendo":
            razao = r["razao_tempo"]
            if pd.notna(razao) and razao > LIMITE_PARADA:
                achados.append(
                    {
                        "tipo": "parada",
                        "etapa": etapa["id"],
                        "detalhe": (
                            f"em andamento há {fmt.numero(float(razao), 1)}× a estimativa de tempo"
                        ),
                    }
                )
        if etapa["status"] == "feito":
            ausentes = [p for p in etapa["entregaveis"] if not _entregavel_existe(raiz_repo, p)]
            if ausentes:
                achados.append(
                    {
                        "tipo": "entregável ausente",
                        "etapa": etapa["id"],
                        "detalhe": "marcada como feita sem: " + ", ".join(ausentes),
                    }
                )
    return achados


def _barra(percentual: float, largura: int = 10) -> str:
    cheios = round(percentual / 100 * largura)
    return "▓" * cheios + "░" * (largura - cheios)


def _numero(valor: float, casas: int = 0) -> str:
    return fmt.numero(None if pd.isna(valor) else float(valor), casas)


def _linhas_tabela(rumo: dict, real: pd.DataFrame) -> list[dict]:
    """Linhas já formatadas (texto) da tabela de etapas, usadas por Markdown e HTML."""
    por_id = real.set_index("id")
    linhas = []
    for etapa in rumo["etapas"]:
        r = por_id.loc[etapa["id"]]
        razoes = [x for x in (r["razao_tokens"], r["razao_tempo"]) if pd.notna(x)]
        linhas.append(
            {
                "id": etapa["id"],
                "nome": etapa["nome"],
                "status": f"{SIMBOLOS[etapa['status']]} {etapa['status']}",
                "agente": etapa["agente"],
                "est_min": _numero(etapa["estimativa_min"]),
                "est_tokens": _numero(etapa["estimativa_tokens"]),
                "real_min": _numero(r["duracao_min"]),
                "real_tokens": _numero(r["tokens_real"]),
                "ia_h": _numero(r["horas_ia"], 1) if "horas_ia" in r else "—",
                "razao": _numero(max(razoes), 1) + "×" if razoes else "—",
            }
        )
    return linhas


def markdown(
    rumo: dict, prog: dict, real: pd.DataFrame, desv: list[dict], tempo: dict | None = None
) -> str:
    """Resumo compacto para comentário de PR."""
    pct = prog["percentual"]
    linhas = [
        "## Rumo do desenvolvimento",
        "",
        f"**Objetivo:** {rumo['objetivo']}",
        "",
        f"`{_barra(pct)} {fmt.numero(pct, 0)}%`",
        "",
        "**Tempo:** " + " · ".join(_texto_tempo(tempo)),
        "",
        (
            "| Etapa | Nome | Status | Agente | Est. min | Est. tokens | Real min | IA h "
            "| Real tokens | Razão |"
        ),
        "|---|---|---|---|--:|--:|--:|--:|--:|--:|",
    ]
    for t in _linhas_tabela(rumo, real):
        linhas.append(
            f"| {t['id']} | {t['nome']} | {t['status']} | {t['agente']} | {t['est_min']} "
            f"| {t['est_tokens']} | {t['real_min']} | {t['ia_h']} | {t['real_tokens']} "
            f"| {t['razao']} |"
        )
    linhas.append("")
    if desv:
        linhas.append(f"**Desvios ({len(desv)})**")
        for d in desv:
            quem = f"{d['etapa']}: " if d["etapa"] else ""
            linhas.append(f"- {d['tipo']}: {quem}{d['detalhe']}")
    else:
        linhas.append("**Desvios:** nenhum")
    linhas.append("")
    linhas.append(f"**Próxima etapa:** {prog['proxima'] or 'nenhuma disponível'}")
    if rumo["historico"]:
        linhas.append("")
        linhas.append(f"Mudanças de objetivo: {len(rumo['historico'])}")
    return "\n".join(linhas) + "\n"


def _graficos(rumo: dict, real: pd.DataFrame) -> tuple[str, str]:
    """HTML do gráfico estimado × real e da linha do tempo (Plotly)."""
    ids = real["id"].tolist()
    figura = go.Figure()
    for nome, est, rea, eixo in (
        ("Tokens", "estimativa_tokens", "tokens_real", ""),
        ("Minutos", "estimativa_min", "duracao_min", "2"),
    ):
        mostrar = nome == "Tokens"
        for rotulo, coluna, cor in (("Estimado", est, "#8896ab"), ("Real", rea, "#2f6fdb")):
            figura.add_bar(
                x=ids,
                y=real[coluna],
                name=rotulo,
                marker_color=cor,
                legendgroup=rotulo,
                showlegend=mostrar,
                xaxis=f"x{eixo}",
                yaxis=f"y{eixo}",
            )
    figura.update_layout(
        barmode="group",
        height=360,
        margin={"t": 50, "b": 40},
        xaxis={"domain": [0, 0.46]},
        xaxis2={"domain": [0.54, 1], "anchor": "y2"},
        yaxis={"title": "tokens"},
        yaxis2={"title": "minutos", "anchor": "x2"},
        annotations=[
            {"text": titulo, "x": x, "y": 1.1, "xref": "paper", "yref": "paper", "showarrow": False}
            for titulo, x in (("Tokens", 0.23), ("Minutos", 0.77))
        ],
    )
    barras = pio.to_html(figura, include_plotlyjs="cdn", full_html=False)

    agora = pd.Timestamp.now(tz="UTC")
    tempo = go.Figure()
    inicios, duracoes, rotulos = [], [], []
    for etapa in rumo["etapas"]:
        inicio = _para_utc(etapa["inicio"])
        if inicio is None:
            continue
        fim = _para_utc(etapa["fim"]) or agora
        inicios.append(inicio)
        duracoes.append((fim - inicio).total_seconds() * 1000)
        rotulos.append(f"{etapa['id']} {etapa['nome']}")
    if rotulos:
        tempo.add_bar(y=rotulos, x=duracoes, base=inicios, orientation="h", marker_color="#2f6fdb")
        tempo.update_yaxes(autorange="reversed")
        tempo.update_xaxes(type="date")
    tempo.update_layout(height=120 + 40 * max(len(rotulos), 1), margin={"t": 20, "b": 40})
    linha_tempo = pio.to_html(tempo, include_plotlyjs=False, full_html=False)
    return barras, linha_tempo


def html(
    rumo: dict, prog: dict, real: pd.DataFrame, desv: list[dict], tempo: dict | None = None
) -> str:
    """Página HTML do rumo (valores formatados em Python)."""
    barras, linha_tempo = _graficos(rumo, real)
    env = Environment(loader=PackageLoader("vcm", "templates"), autoescape=True)
    return env.get_template("rumo.html.j2").render(
        objetivo=rumo["objetivo"],
        criterios=rumo["criterio_de_pronto"],
        percentual=fmt.numero(prog["percentual"], 0),
        percentual_largura=f"{prog['percentual']:.0f}",
        barra=_barra(prog["percentual"]),
        etapas=_linhas_tabela(rumo, real),
        tempo=_texto_tempo(tempo),
        desvios=desv,
        proxima=prog["proxima"] or "nenhuma disponível",
        n_mudancas=len(rumo["historico"]),
        historico=rumo["historico"],
        grafico_barras=barras,
        grafico_tempo=linha_tempo,
    )
