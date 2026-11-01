"""Coletor de telemetria a partir dos logs de sessão locais do Claude Code.

Lê `~/.claude/projects/<projeto>/<sessao>.jsonl` e os subagentes em
`<sessao>/subagents/agent-<id>.jsonl`. A mesma resposta aparece em várias linhas
(uma por bloco de conteúdo) com o mesmo `message.id`: deduplica por (arquivo, id).
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pandas as pd
import yaml

PASTA_PADRAO = Path.home() / ".claude" / "projects"

COLUNAS_TOKENS = [
    "tokens_entrada",
    "tokens_saida",
    "tokens_cache_leitura",
    "tokens_cache_criacao_5m",
    "tokens_cache_criacao_1h",
    "tokens_raciocinio",
]
# Tokens cobrados; o raciocínio já está contido em tokens_saida.
COLUNAS_TOTAL = COLUNAS_TOKENS[:5]
COLUNAS = [
    "projeto",
    "sessao_id",
    "agente_id",
    "tipo_agente",
    "descricao",
    "modelo",
    "mensagem_id",
    "inicio",
    "cwd",
    "git_branch",
    *COLUNAS_TOKENS,
]
PRECOS_CHAVES = ["entrada", "saida", "cache_leitura", "cache_criacao_5m", "cache_criacao_1h"]
COLUNA_TOKENS_POR_PRECO = dict(zip(COLUNAS_TOTAL, PRECOS_CHAVES, strict=True))


def _inteiro(valor: object) -> int:
    return int(valor) if isinstance(valor, (int, float)) else 0


def _linha_para_registro(dado: dict) -> dict | None:
    mensagem = dado.get("message")
    if dado.get("type") != "assistant" or not isinstance(mensagem, dict):
        return None
    uso = mensagem.get("usage")
    if not isinstance(uso, dict) or not mensagem.get("id"):
        return None
    criacao = uso.get("cache_creation") or {}
    detalhes = uso.get("output_tokens_details") or {}
    return {
        "modelo": mensagem.get("model"),
        "mensagem_id": mensagem["id"],
        "inicio": dado.get("timestamp"),
        "cwd": dado.get("cwd"),
        "git_branch": dado.get("gitBranch"),
        "tokens_entrada": _inteiro(uso.get("input_tokens")),
        "tokens_saida": _inteiro(uso.get("output_tokens")),
        "tokens_cache_leitura": _inteiro(uso.get("cache_read_input_tokens")),
        "tokens_cache_criacao_5m": _inteiro(criacao.get("ephemeral_5m_input_tokens")),
        "tokens_cache_criacao_1h": _inteiro(criacao.get("ephemeral_1h_input_tokens")),
        "tokens_raciocinio": _inteiro(detalhes.get("thinking_tokens")),
    }


def _ler_arquivo(arquivo: Path) -> tuple[list[dict], int]:
    registros: list[dict] = []
    invalidas = 0
    with arquivo.open(encoding="utf-8", errors="replace") as f:
        for linha in f:
            if not linha.strip():
                continue
            try:
                dado = json.loads(linha)
            except json.JSONDecodeError:
                invalidas += 1
                continue
            if not isinstance(dado, dict):
                invalidas += 1
                continue
            registro = _linha_para_registro(dado)
            if registro is not None:
                registros.append(registro)
    return registros, invalidas


def _meta(arquivo: Path) -> dict:
    caminho = arquivo.with_suffix(".meta.json")
    try:
        dado = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dado if isinstance(dado, dict) else {}


def _arquivos_do_projeto(pasta_projeto: Path) -> Iterator[tuple[Path, str, str | None]]:
    """Gera (arquivo, sessao_id, agente_id ou None) de um projeto."""
    for arquivo in sorted(pasta_projeto.glob("*.jsonl")):
        yield arquivo, arquivo.stem, None
    for arquivo in sorted(pasta_projeto.glob("*/subagents/agent-*.jsonl")):
        yield arquivo, arquivo.parent.parent.name, arquivo.stem.removeprefix("agent-")


def ler_chamadas(pasta: Path = PASTA_PADRAO, filtro_projeto: str | None = None) -> pd.DataFrame:
    """Uma linha por chamada ao modelo (message.id único).

    Colunas: projeto, sessao_id, agente_id (None na sessão principal), tipo_agente
    ("principal" na sessão principal), descricao, modelo, mensagem_id, inicio (UTC), cwd,
    git_branch, tokens_entrada, tokens_saida, tokens_cache_leitura, tokens_cache_criacao_5m,
    tokens_cache_criacao_1h, tokens_raciocinio (int64; ausente = 0).
    Linhas que não parseiam são ignoradas; o total fica em `df.attrs["linhas_invalidas"]`.
    """
    pasta = Path(pasta)
    registros: list[dict] = []
    invalidas = 0
    projetos = sorted(p for p in pasta.iterdir() if p.is_dir()) if pasta.is_dir() else []
    for pasta_projeto in projetos:
        if filtro_projeto and filtro_projeto not in pasta_projeto.name:
            continue
        for arquivo, sessao_id, agente_id in _arquivos_do_projeto(pasta_projeto):
            linhas, ruins = _ler_arquivo(arquivo)
            invalidas += ruins
            meta = _meta(arquivo) if agente_id else {}
            for linha in linhas:
                linha["arquivo"] = str(arquivo)
                linha["projeto"] = pasta_projeto.name
                linha["sessao_id"] = sessao_id
                linha["agente_id"] = agente_id
                linha["tipo_agente"] = (
                    meta.get("agentType", "subagente") if agente_id else "principal"
                )
                linha["descricao"] = meta.get("description")
            registros.extend(linhas)

    if registros:
        df = pd.DataFrame(registros)
    else:
        df = pd.DataFrame(columns=[*COLUNAS, "arquivo"])
    df["inicio"] = pd.to_datetime(df["inicio"], utc=True, format="ISO8601")
    # Primeiro instante visto da resposta; os demais campos vêm da última linha (uso final).
    df["inicio"] = df.groupby(["arquivo", "mensagem_id"])["inicio"].transform("min")
    df = df.drop_duplicates(["arquivo", "mensagem_id"], keep="last")
    df = df.astype(dict.fromkeys(COLUNAS_TOKENS, "int64"))
    df = df.sort_values(["inicio", "mensagem_id"], kind="stable").reset_index(drop=True)
    df = df[COLUNAS].astype({"agente_id": object, "descricao": object})
    df.attrs["linhas_invalidas"] = invalidas
    return df


def _modelo_mais_frequente(modelos: pd.Series) -> object:
    contagem = modelos.dropna().value_counts()
    return contagem.index[0] if len(contagem) else None


def resumo_por_agente(chamadas: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por (sessao_id, agente_id) com chamadas, tokens, início, fim e duração (s)."""
    base = chamadas.assign(agente_id=chamadas["agente_id"].fillna(""))
    resumo = (
        base.groupby(["sessao_id", "agente_id"], sort=True)
        .agg(
            tipo_agente=("tipo_agente", "first"),
            descricao=("descricao", "first"),
            modelo=("modelo", _modelo_mais_frequente),
            chamadas=("mensagem_id", "size"),
            **{c: (c, "sum") for c in COLUNAS_TOKENS},
            inicio=("inicio", "min"),
            fim=("inicio", "max"),
        )
        .reset_index()
    )
    resumo["tokens_total"] = resumo[COLUNAS_TOTAL].sum(axis=1).astype("int64")
    resumo["duracao_s"] = (resumo["fim"] - resumo["inicio"]).dt.total_seconds()
    resumo["agente_id"] = resumo["agente_id"].replace("", None)
    colunas = ["sessao_id", "agente_id", "tipo_agente", "descricao", "modelo", "chamadas"]
    return resumo[[*colunas, *COLUNAS_TOKENS, "tokens_total", "inicio", "fim", "duracao_s"]]


def carregar_precos(arquivo: Path) -> dict[str, dict[str, float]]:
    """Preços em USD por milhão de tokens, por id de modelo, lidos de `modelos.yaml`.

    Modelos com algum preço ausente (None) ficam de fora: custo desconhecido, nunca zero.
    """
    dado = yaml.safe_load(Path(arquivo).read_text(encoding="utf-8")) or {}
    precos: dict[str, dict[str, float]] = {}
    for modelo in dado.get("modelos", []):
        bruto = modelo.get("preco_usd_por_mtok") or {}
        valores = [bruto.get(chave) for chave in PRECOS_CHAVES]
        if any(v is None for v in valores):
            continue
        precos[modelo["id"]] = {c: float(v) for c, v in zip(PRECOS_CHAVES, valores, strict=True)}
    return precos


def custo_usd(chamadas: pd.DataFrame, precos: dict) -> pd.Series:
    """Custo equivalente de API por chamada (USD); NaN para modelo sem preço."""
    tabela = pd.DataFrame.from_dict(precos, orient="index", dtype="float64")
    tabela = tabela.reindex(columns=PRECOS_CHAVES).reindex(chamadas["modelo"].to_numpy())
    tokens = chamadas[list(COLUNA_TOKENS_POR_PRECO)].to_numpy(dtype="float64")
    precos_alinhados = tabela[list(COLUNA_TOKENS_POR_PRECO.values())].to_numpy()
    custo = (tokens * precos_alinhados).sum(axis=1) / 1e6
    return pd.Series(custo, index=chamadas.index, name="custo_usd", dtype="float64")
