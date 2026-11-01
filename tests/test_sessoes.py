"""Testes do coletor de logs de sessão do Claude Code."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from vcm import cli
from vcm.coletores import sessoes


def _linha(msg_id, modelo, instante, entrada, saida, leitura, c5m, c1h, raciocinio=0, **extra):
    return {
        "type": "assistant",
        "timestamp": instante,
        "sessionId": "S1",
        "cwd": "/x",
        "gitBranch": "main",
        "message": {
            "id": msg_id,
            "model": modelo,
            "usage": {
                "input_tokens": entrada,
                "output_tokens": saida,
                "cache_read_input_tokens": leitura,
                "cache_creation": {
                    "ephemeral_5m_input_tokens": c5m,
                    "ephemeral_1h_input_tokens": c1h,
                },
                "output_tokens_details": {"thinking_tokens": raciocinio},
            },
        },
        **extra,
    }


def _gravar(caminho: Path, linhas: list, lixo: bool = False) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    textos = [json.dumps(x) for x in linhas]
    if lixo:
        textos.insert(1, "{isto nao e json")
    caminho.write_text("\n".join(textos) + "\n", encoding="utf-8")


def _montar(raiz: Path) -> Path:
    projeto = raiz / "-home-user-meu-projeto"
    a = _linha("m1", "claude-opus-5-5", "2026-10-31T10:00:00.000Z", 10, 100, 1000, 200, 0, 30)
    a_repetida = [a, a, a]
    b = _linha("m2", "claude-opus-5-5", "2026-10-31T10:00:10Z", 5, 50, 2000, 0, 400)
    _gravar(projeto / "S1.jsonl", [*a_repetida, b, {"type": "user"}], lixo=True)
    sub = projeto / "S1" / "subagents"
    c = _linha("m3", "claude-haiku-5-5", "2026-10-31T10:00:02Z", 1, 2, 3, 4, 5, agentId="abc")
    d = _linha("m4", "claude-haiku-5-5", "2026-10-31T10:00:07Z", 1, 2, 3, 4, 5, agentId="abc")
    _gravar(sub / "agent-abc.jsonl", [c, d])
    (sub / "agent-abc.meta.json").write_text(
        json.dumps({"agentType": "executor-haiku", "description": "Tarefa mecânica"}),
        encoding="utf-8",
    )
    return raiz


def test_deduplica_e_conta(tmp_path):
    chamadas = sessoes.ler_chamadas(_montar(tmp_path))
    assert len(chamadas) == 4
    assert chamadas["mensagem_id"].is_unique
    assert chamadas.attrs["linhas_invalidas"] == 1
    assert str(chamadas["tokens_saida"].dtype) == "int64"
    principal = chamadas[chamadas["agente_id"].isna()]
    assert set(principal["tipo_agente"]) == {"principal"}
    assert principal["tokens_saida"].sum() == 150
    assert chamadas["inicio"].dt.tz is not None


def test_filtro_projeto(tmp_path):
    _montar(tmp_path)
    assert sessoes.ler_chamadas(tmp_path, "meu-projeto").shape[0] == 4
    assert sessoes.ler_chamadas(tmp_path, "outro").empty


def test_resumo_por_agente(tmp_path):
    resumo = sessoes.resumo_por_agente(sessoes.ler_chamadas(_montar(tmp_path)))
    assert len(resumo) == 2
    sub = resumo[resumo["agente_id"] == "abc"].iloc[0]
    assert sub["tipo_agente"] == "executor-haiku"
    assert sub["descricao"] == "Tarefa mecânica"
    assert sub["modelo"] == "claude-haiku-5-5"
    assert sub["chamadas"] == 2
    assert sub["tokens_total"] == 2 * (1 + 2 + 3 + 4 + 5)
    assert sub["duracao_s"] == 5.0
    prin = resumo[resumo["agente_id"].isna()].iloc[0]
    assert prin["tipo_agente"] == "principal"
    assert prin["chamadas"] == 2
    assert prin["tokens_raciocinio"] == 30
    assert prin["tokens_total"] == (10 + 100 + 1000 + 200) + (5 + 50 + 2000 + 400)
    assert prin["duracao_s"] == 10.0


def _yaml_precos(caminho: Path) -> Path:
    modelos = [
        {
            "id": "claude-opus-5-5",
            "preco_usd_por_mtok": {
                "entrada": 10.0,
                "saida": 50.0,
                "cache_leitura": 1.0,
                "cache_criacao_5m": 12.0,
                "cache_criacao_1h": 20.0,
            },
        },
        {
            "id": "claude-haiku-5-5",
            "preco_usd_por_mtok": {"entrada": 1.0, "saida": None, "cache_leitura": 0.1},
        },
    ]
    caminho.write_text(yaml.safe_dump({"modelos": modelos}), encoding="utf-8")
    return caminho


def test_precos_ignoram_modelo_incompleto(tmp_path):
    precos = sessoes.carregar_precos(_yaml_precos(tmp_path / "m.yaml"))
    assert list(precos) == ["claude-opus-5-5"]
    assert precos["claude-opus-5-5"]["cache_criacao_1h"] == 20.0


def test_custo_usd(tmp_path):
    chamadas = sessoes.ler_chamadas(_montar(tmp_path))
    precos = sessoes.carregar_precos(_yaml_precos(tmp_path / "m.yaml"))
    custo = sessoes.custo_usd(chamadas, precos)
    m1 = (10 * 10 + 100 * 50 + 1000 * 1 + 200 * 12 + 0 * 20) / 1e6
    m2 = (5 * 10 + 50 * 50 + 2000 * 1 + 0 * 12 + 400 * 20) / 1e6
    por_id = pd.Series(custo.to_numpy(), index=chamadas["mensagem_id"])
    np.testing.assert_allclose(por_id["m1"], m1, atol=1e-12)
    np.testing.assert_allclose(por_id["m2"], m2, atol=1e-12)
    assert np.isnan(por_id["m3"]) and np.isnan(por_id["m4"])


def test_cli_sessoes(tmp_path, monkeypatch, capsys):
    _montar(tmp_path / "logs")
    monkeypatch.chdir(tmp_path)
    saida = tmp_path / "saida"
    codigo = cli.main(["sessoes", "--pasta", str(tmp_path / "logs"), "--saida", str(saida)])
    assert codigo == 0
    assert pd.read_parquet(saida / "chamadas.parquet").shape[0] == 4
    assert pd.read_parquet(saida / "por_agente.parquet").shape[0] == 2
    assert "executor-haiku" in capsys.readouterr().out
