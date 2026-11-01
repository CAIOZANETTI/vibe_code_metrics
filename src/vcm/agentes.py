"""Registro das execuções de agentes (base de dados da tese T003, roteamento)."""

from __future__ import annotations

import json
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
# Campo do registro `pdca/agentes.jsonl` (projetos_em_camadas) -> coluna de COLUNAS.
# O campo `obs` de algumas linhas não tem coluna correspondente e é ignorado.
MAPEAMENTO_PDCA = {
    "data": "data",
    "rodada": "fase",
    "tarefa": "tarefa",
    "papel": "papel",
    "modelo": "modelo",
    "tokens": "tokens",
    "ferramentas": "chamadas_ferramenta",
    "segundos": "duracao_s",
    "resultado": "observacao",
}
COLUNAS_NUMERICAS = ["tokens", "chamadas_ferramenta", "duracao_s"]


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


def ler_pdca(arquivo: Path) -> pd.DataFrame:
    """Lê `pdca/agentes.jsonl` (projetos_em_camadas): uma linha JSON por execução.

    Devolve as mesmas `COLUNAS` de `ler`. Campo ausente ou `null` vira NaN (ex.: `tokens`
    de sessão reiniciada), nunca zero. `aprovado` e `retrabalho_gerente` ficam None,
    porque esse formato não os registra.
    """
    registros = []
    with arquivo.open(encoding="utf-8") as origem:
        for linha in origem:
            if not linha.strip():
                continue
            bruto = json.loads(linha)
            registro = {destino: bruto.get(campo) for campo, destino in MAPEAMENTO_PDCA.items()}
            registro["aprovado"] = None
            registro["retrabalho_gerente"] = None
            registros.append(registro)
    tabela = pd.DataFrame(registros, columns=COLUNAS)
    for coluna in COLUNAS_NUMERICAS:
        tabela[coluna] = tabela[coluna].astype("float64")
    return tabela


def resumo_por_modelo(tabela: pd.DataFrame) -> pd.DataFrame:
    """Custo em tokens por tarefa aprovada, por modelo.

    `aprovado` ausente (formato pdca) conta como não aprovado. Tokens ausentes (NaN) não
    entram na soma e são contados em `execucoes_sem_tokens`.
    """
    t = tabela.assign(
        aprovado=tabela["aprovado"].fillna(False).astype(bool),
        sem_tokens=tabela["tokens"].isna(),
    )
    g = t.groupby("modelo")
    resumo = pd.DataFrame(
        {
            "execucoes": g.size(),
            "aprovadas": g["aprovado"].sum(),
            "tokens_total": g["tokens"].sum(min_count=1),
            "duracao_total_s": g["duracao_s"].sum(),
        }
    )
    aprovadas = resumo["aprovadas"].where(resumo["aprovadas"] > 0)
    resumo["tokens_por_aprovacao"] = resumo["tokens_total"] / aprovadas
    resumo["taxa_aprovacao"] = resumo["aprovadas"] / resumo["execucoes"]
    resumo["execucoes_sem_tokens"] = g["sem_tokens"].sum()
    return resumo
