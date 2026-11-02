"""Gancho `Stop` do Claude Code: confere se a resposta que relata trabalho segue o formulário."""

from __future__ import annotations

import json
from pathlib import Path

from vcm import formulario

FERRAMENTAS_DE_EDICAO = ("Edit", "Write", "NotebookEdit", "MultiEdit")


def _blocos(mensagem: dict) -> list[dict]:
    """Conteúdo da mensagem como lista de blocos (texto puro vira um bloco `text`)."""
    conteudo = (mensagem.get("message") or {}).get("content")
    if isinstance(conteudo, str):
        return [{"type": "text", "text": conteudo}]
    if isinstance(conteudo, list):
        return [b for b in conteudo if isinstance(b, dict)]
    return []


def _ler_transcript(caminho: str | None) -> list[dict]:
    """Mensagens user/assistant do transcript JSONL; vazio se ausente ou ilegível."""
    if not caminho:
        return []
    try:
        linhas = Path(caminho).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return []
    mensagens = []
    for linha in linhas:
        try:
            item = json.loads(linha)
        except ValueError:
            continue
        if isinstance(item, dict) and item.get("type") in ("user", "assistant"):
            mensagens.append(item)
    return mensagens


def _e_humana(mensagem: dict) -> bool:
    """Mensagem "user" com texto humano (não só `tool_result`)."""
    if mensagem.get("type") != "user":
        return False
    return any(b.get("type") == "text" for b in _blocos(mensagem))


def _turno_atual(mensagens: list[dict]) -> list[dict]:
    """Da última mensagem humana até o fim."""
    for posicao in range(len(mensagens) - 1, -1, -1):
        if _e_humana(mensagens[posicao]):
            return mensagens[posicao + 1 :]
    return mensagens


def _mexe_em_arquivo(bloco: dict) -> bool:
    """Bloco `tool_use` que edita arquivo ou faz `git commit`."""
    if bloco.get("type") != "tool_use":
        return False
    if bloco.get("name") in FERRAMENTAS_DE_EDICAO:
        return True
    comando = (bloco.get("input") or {}).get("command")
    return bloco.get("name") == "Bash" and isinstance(comando, str) and "git commit" in comando


def _mexeu_em_arquivos(turno: list[dict]) -> bool:
    """O turno editou arquivos ou fez commit."""
    return any(_mexe_em_arquivo(b) for m in turno if m["type"] == "assistant" for b in _blocos(m))


def _texto_final(turno: list[dict]) -> str:
    """Texto da última mensagem do assistente no turno."""
    for mensagem in reversed(turno):
        if mensagem["type"] == "assistant":
            return "\n".join(
                str(b.get("text", "")) for b in _blocos(mensagem) if b.get("type") == "text"
            )
    return ""


def _mensagem_de_bloqueio(faltando: list[str]) -> str:
    """Texto do bloqueio, em português."""
    campos = ", ".join(faltando)
    return (
        f"A resposta mexeu em arquivos, mas o formulário padrão está incompleto. Faltam: {campos}. "
        "Reescreva a resposta no formulário da skill vcm-formulario e rode "
        "`vcm rumo --formulario` para obter os números."
    )


def avaliar_parada(entrada: dict) -> dict | None:
    """Decide se o hook Stop deve bloquear; devolve o JSON de decisão ou None para liberar."""
    if entrada.get("stop_hook_active"):
        return None
    try:
        turno = _turno_atual(_ler_transcript(entrada.get("transcript_path")))
        if not _mexeu_em_arquivos(turno):
            return None
        texto = entrada.get("last_assistant_message")
        if not isinstance(texto, str) or not texto.strip():
            texto = _texto_final(turno)
        faltando = formulario.campos_faltando(texto)
    except Exception:  # noqa: BLE001 - o gancho nunca pode travar o agente por erro próprio
        return None
    if not faltando:
        return None
    return {"decision": "block", "reason": _mensagem_de_bloqueio(faltando)}


# --- Adesão ao formulário (medição, não bloqueio) ---


def _turnos(mensagens: list[dict]) -> list[list[dict]]:
    """Divide o transcript em turnos: cada um vai de uma mensagem humana até a próxima."""
    turnos: list[list[dict]] = []
    atual: list[dict] | None = None
    for mensagem in mensagens:
        if _e_humana(mensagem):
            if atual:
                turnos.append(atual)
            atual = []
        elif atual is not None:
            atual.append(mensagem)
    if atual:
        turnos.append(atual)
    return turnos


def _tokens_saida_final(turno: list[dict]) -> int:
    """Tokens de saída da última mensagem do assistente no turno (0 sem medição)."""
    for mensagem in reversed(turno):
        if mensagem["type"] == "assistant":
            uso = (mensagem.get("message") or {}).get("usage") or {}
            valor = uso.get("output_tokens")
            return int(valor) if isinstance(valor, int | float) else 0
    return 0


def adesao(caminho: str | Path) -> list[dict]:
    """Um registro por turno do transcript: se mexeu em arquivos, se o formulário veio completo
    e o tamanho da resposta final (caracteres e tokens de saída)."""
    registros = []
    for turno in _turnos(_ler_transcript(str(caminho))):
        texto = _texto_final(turno)
        if not texto.strip():
            continue
        registros.append(
            {
                "mexeu_em_arquivos": _mexeu_em_arquivos(turno),
                "com_formulario": not formulario.campos_faltando(texto),
                "caracteres_resposta": len(texto),
                "tokens_saida_resposta": _tokens_saida_final(turno),
            }
        )
    return registros
