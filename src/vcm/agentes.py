"""Registro das execuções de agentes (base de dados da tese T003, roteamento)."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

ARQUIVO_PADRAO = Path("results/agentes/execucoes.csv")
COLUNAS = [
    "data",
    "fase",
    "tarefa",
    "papel",
    "modelo",
    "tokens",
    "chamadas_ferramenta",
    "duracao_s",
    "aprovado",
    "retrabalho_gerente",
    "observacao",
]


def registrar(arquivo: Path = ARQUIVO_PADRAO, **campos) -> pd.DataFrame:
    """Acrescenta uma execução ao CSV (cria o arquivo se não existir)."""
    desconhecidos = set(campos) - set(COLUNAS)
    if desconhecidos:
        raise ValueError(f"campos desconhecidos: {sorted(desconhecidos)}")
    linha = pd.DataFrame([{c: campos.get(c) for c in COLUNAS}])
    if arquivo.exists():
        tabela = pd.concat([ler(arquivo), linha], ignore_index=True)
    else:
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        tabela = linha
    tabela.to_csv(arquivo, index=False)
    return tabela


def ler(arquivo: Path = ARQUIVO_PADRAO) -> pd.DataFrame:
    return pd.read_csv(arquivo)


def resumo_por_modelo(tabela: pd.DataFrame) -> pd.DataFrame:
    """Custo em tokens por tarefa aprovada, por modelo."""
    t = tabela.assign(aprovado=tabela["aprovado"].astype(bool))
    g = t.groupby("modelo")
    resumo = pd.DataFrame(
        {
            "execucoes": g.size(),
            "aprovadas": g["aprovado"].sum(),
            "tokens_total": g["tokens"].sum(),
            "duracao_total_s": g["duracao_s"].sum(),
        }
    )
    aprovadas = resumo["aprovadas"].where(resumo["aprovadas"] > 0)
    resumo["tokens_por_aprovacao"] = resumo["tokens_total"] / aprovadas
    resumo["taxa_aprovacao"] = resumo["aprovadas"] / resumo["execucoes"]
    return resumo
