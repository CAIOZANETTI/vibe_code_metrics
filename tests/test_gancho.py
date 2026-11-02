"""Testes do gancho Stop (`vcm.gancho` e `vcm formulario --verificar`)."""

import io
import json

from vcm import formulario, gancho
from vcm.cli import main

FORMULARIO_COMPLETO = "\n\n".join(f"**{campo}:** ok" for campo in formulario.CAMPOS)


def _humana(texto="faça isso"):
    return {"type": "user", "message": {"role": "user", "content": texto}}


def _assistente(*blocos):
    return {"type": "assistant", "message": {"role": "assistant", "content": list(blocos)}}


def _uso(nome, **entrada):
    return {"type": "tool_use", "id": "t1", "name": nome, "input": entrada}


def _texto(texto):
    return {"type": "text", "text": texto}


def _resultado():
    bloco = {"type": "tool_result", "tool_use_id": "t1", "content": "ok"}
    return {"type": "user", "message": {"role": "user", "content": [bloco]}}


def _transcript(tmp_path, mensagens):
    caminho = tmp_path / "transcript.jsonl"
    caminho.write_text("\n".join(json.dumps(m) for m in mensagens) + "\n", encoding="utf-8")
    return caminho


def _entrada(caminho, **extra):
    return {"session_id": "s", "transcript_path": str(caminho), "hook_event_name": "Stop", **extra}


def test_edicao_sem_formulario_bloqueia(tmp_path):
    caminho = _transcript(
        tmp_path,
        [_humana(), _assistente(_uso("Edit", file_path="a.py")), _assistente(_texto("pronto"))],
    )
    decisao = gancho.avaliar_parada(_entrada(caminho))
    assert decisao["decision"] == "block"
    assert "Campo livre" in decisao["reason"]
    assert "vcm rumo --formulario" in decisao["reason"]


def test_formulario_completo_libera(tmp_path):
    caminho = _transcript(
        tmp_path,
        [_humana(), _assistente(_uso("Write")), _assistente(_texto(FORMULARIO_COMPLETO))],
    )
    assert gancho.avaliar_parada(_entrada(caminho)) is None


def test_ultima_mensagem_da_entrada_tem_prioridade(tmp_path):
    caminho = _transcript(tmp_path, [_humana(), _assistente(_uso("Write"), _texto("pronto"))])
    entrada = _entrada(caminho, last_assistant_message=FORMULARIO_COMPLETO)
    assert gancho.avaliar_parada(entrada) is None


def test_turno_sem_edicao_libera(tmp_path):
    caminho = _transcript(tmp_path, [_humana(), _assistente(_texto("só conversa"))])
    assert gancho.avaliar_parada(_entrada(caminho)) is None


def test_edicao_de_turno_anterior_nao_conta(tmp_path):
    caminho = _transcript(
        tmp_path,
        [_humana(), _assistente(_uso("Edit")), _humana("outra"), _assistente(_texto("oi"))],
    )
    assert gancho.avaliar_parada(_entrada(caminho)) is None


def test_stop_hook_ativo_libera(tmp_path):
    caminho = _transcript(tmp_path, [_humana(), _assistente(_uso("Edit"), _texto("x"))])
    assert gancho.avaliar_parada(_entrada(caminho, stop_hook_active=True)) is None


def test_transcript_inexistente_libera(tmp_path):
    assert gancho.avaliar_parada(_entrada(tmp_path / "nao_existe.jsonl")) is None


def test_tool_result_nao_e_mensagem_humana(tmp_path):
    caminho = _transcript(
        tmp_path,
        [
            _humana(),
            _assistente(_uso("Edit")),
            _resultado(),
            _assistente(_texto("pronto")),
        ],
    )
    assert gancho.avaliar_parada(_entrada(caminho))["decision"] == "block"


def test_git_commit_por_bash_conta(tmp_path):
    caminho = _transcript(
        tmp_path,
        [_humana(), _assistente(_uso("Bash", command="git commit -m x"), _texto("feito"))],
    )
    assert gancho.avaliar_parada(_entrada(caminho))["decision"] == "block"


def test_bash_comum_nao_conta(tmp_path):
    caminho = _transcript(
        tmp_path, [_humana(), _assistente(_uso("Bash", command="ls"), _texto("feito"))]
    )
    assert gancho.avaliar_parada(_entrada(caminho)) is None


def test_cli_imprime_bloqueio(tmp_path, monkeypatch, capsys):
    caminho = _transcript(tmp_path, [_humana(), _assistente(_uso("Edit"), _texto("pronto"))])
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_entrada(caminho))))
    assert main(["formulario", "--verificar"]) == 0
    assert json.loads(capsys.readouterr().out)["decision"] == "block"


def test_cli_libera_sem_saida(tmp_path, monkeypatch, capsys):
    caminho = _transcript(tmp_path, [_humana(), _assistente(_texto("oi"))])
    monkeypatch.setattr("sys.stdin", io.StringIO(json.dumps(_entrada(caminho))))
    assert main(["formulario", "--verificar"]) == 0
    assert capsys.readouterr().out == ""


def test_cli_json_invalido_nao_bloqueia(monkeypatch, capsys):
    monkeypatch.setattr("sys.stdin", io.StringIO("isto não é json"))
    assert main(["formulario", "--verificar"]) == 0
    assert capsys.readouterr().out == ""
