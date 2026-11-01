"""Leitura do registro `pdca/agentes.jsonl` (formato do projeto projetos_em_camadas)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from vcm import agentes
from vcm.cli import main

LINHAS = [
    {
        "rodada": "rodada 20",
        "data": "2026-10-31",
        "modelo": "fable",
        "papel": "gerente",
        "tarefa": "aceite de E4, E5, E6",
        "tokens": 99429,
        "segundos": 143,
        "ferramentas": 11,
        "resultado": "E4 e E5 aceitas; E6 revisar",
    },
    {
        "rodada": "rodada 20",
        "data": "2026-10-30",
        "modelo": "sonnet",
        "papel": "implementador",
        "tarefa": "E1 + E2 (inventário)",
        "tokens": None,
        "segundos": None,
        "ferramentas": None,
        "resultado": "E2 aceita, E1 revisar",
        "obs": "uso não medido: a sessão reiniciou antes do relatório do agente",
    },
    {
        "rodada": "rodada 20",
        "data": "2026-10-31",
        "modelo": "sonnet",
        "papel": "implementador",
        "tarefa": "E5 (retorno da IA no registro)",
        "tokens": 87643,
        "segundos": 115,
        "ferramentas": 20,
        "resultado": "entregue para aceite",
    },
]


def _escrever_jsonl(caminho: Path) -> Path:
    caminho.write_text("\n".join(json.dumps(linha) for linha in LINHAS) + "\n", encoding="utf-8")
    return caminho


def test_ler_pdca_devolve_as_mesmas_colunas(tmp_path: Path) -> None:
    tabela = agentes.ler_pdca(_escrever_jsonl(tmp_path / "agentes.jsonl"))

    assert list(tabela.columns) == agentes.COLUNAS
    assert len(tabela) == 3
    assert tabela.loc[0, "fase"] == "rodada 20"
    assert tabela.loc[0, "chamadas_ferramenta"] == 11
    assert tabela.loc[0, "duracao_s"] == 143
    assert tabela.loc[0, "observacao"] == "E4 e E5 aceitas; E6 revisar"
    assert tabela["aprovado"].isna().all()
    assert tabela["retrabalho_gerente"].isna().all()


def test_ler_pdca_trata_tokens_ausentes_como_nan(tmp_path: Path) -> None:
    tabela = agentes.ler_pdca(_escrever_jsonl(tmp_path / "agentes.jsonl"))

    assert np.isnan(tabela.loc[1, "tokens"])
    assert tabela.loc[1, "tokens"] != 0
    assert tabela["tokens"].isna().sum() == 1


def test_resumo_com_aprovado_ausente_e_tokens_nan(tmp_path: Path) -> None:
    tabela = agentes.ler_pdca(_escrever_jsonl(tmp_path / "agentes.jsonl"))

    resumo = agentes.resumo_por_modelo(tabela)

    assert list(resumo.index) == ["fable", "sonnet"]
    assert resumo.loc["sonnet", "execucoes"] == 2
    assert resumo.loc["sonnet", "aprovadas"] == 0
    assert resumo.loc["sonnet", "tokens_total"] == 87643
    assert resumo.loc["sonnet", "execucoes_sem_tokens"] == 1
    assert resumo.loc["fable", "execucoes_sem_tokens"] == 0
    assert resumo.loc["fable", "tokens_total"] == 99429
    assert resumo["tokens_por_aprovacao"].isna().all()
    assert resumo["taxa_aprovacao"].isna().all()  # sem dado de aprovação: NaN, não 0


def test_resumo_csv_continua_contando_tokens_sem_valor(tmp_path: Path) -> None:
    tabela = pd.DataFrame(
        {
            "modelo": ["sonnet", "sonnet", "fable"],
            "tokens": [100.0, np.nan, np.nan],
            "duracao_s": [10.0, 5.0, 1.0],
            "aprovado": [True, False, True],
        }
    )

    resumo = agentes.resumo_por_modelo(tabela)

    assert resumo.loc["sonnet", "tokens_total"] == 100
    assert resumo.loc["sonnet", "tokens_por_aprovacao"] == 100
    assert resumo.loc["sonnet", "execucoes_sem_tokens"] == 1
    assert np.isnan(resumo.loc["fable", "tokens_total"])


def test_cli_agentes_com_pdca_retorna_zero(tmp_path: Path, capsys) -> None:
    arquivo = _escrever_jsonl(tmp_path / "agentes.jsonl")

    assert main(["agentes", "--pdca", str(arquivo)]) == 0
    saida = capsys.readouterr().out
    assert "sonnet" in saida
    assert "execucoes_sem_tokens" in saida


def test_cli_agentes_recusa_pdca_e_arquivo_juntos(tmp_path: Path, capsys) -> None:
    arquivo = _escrever_jsonl(tmp_path / "agentes.jsonl")

    assert main(["agentes", "--pdca", str(arquivo), "--arquivo", str(arquivo)]) == 1
    assert "não os dois" in capsys.readouterr().err


def test_aprovacao_desconhecida_e_nan_nao_zero():
    import pandas as pd

    from vcm.agentes import COLUNAS, resumo_por_modelo

    tabela = pd.DataFrame(
        [{**dict.fromkeys(COLUNAS), "modelo": "fable", "tokens": 10.0, "duracao_s": 1.0}]
    )
    r = resumo_por_modelo(tabela)
    assert pd.isna(r.loc["fable", "taxa_aprovacao"])
