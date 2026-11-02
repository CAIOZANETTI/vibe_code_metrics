"""Configuração do projeto medido (`vcm.yaml` na raiz), com autodetecção quando ausente."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

NOME_ARQUIVO = "vcm.yaml"
_PASTAS_NAO_PACOTE = {"tests", "test", ".venv", ".git", ".claude", "results", "__pycache__"}


@dataclass(frozen=True)
class Config:
    """Configuração de medição de um projeto."""

    projeto: str
    pastas_fonte: tuple[str, ...]
    pasta_testes: str
    comando_referencia: tuple[str, ...] | None
    repeticoes: int
    limites: dict
    dependencias_extras: tuple[str, ...] = ()


def _detectar_pastas_fonte(raiz: Path) -> tuple[str, ...]:
    """`src` se existir; senão pastas da raiz com `__init__.py`; senão a própria raiz."""
    if (raiz / "src").is_dir():
        return ("src",)
    pacotes = sorted(
        pasta.name
        for pasta in raiz.iterdir()
        if pasta.is_dir()
        and pasta.name not in _PASTAS_NAO_PACOTE
        and (pasta / "__init__.py").is_file()
    )
    return tuple(pacotes) if pacotes else (".",)


def _lista_de_textos(valor: object, campo: str) -> tuple[str, ...]:
    if not isinstance(valor, list) or not valor or not all(isinstance(v, str) for v in valor):
        raise ValueError(f"vcm.yaml: '{campo}' deve ser uma lista não vazia de textos")
    return tuple(valor)


def _texto_nao_vazio(valor: object, campo: str) -> str:
    if not isinstance(valor, str) or not valor:
        raise ValueError(f"vcm.yaml: '{campo}' deve ser um texto não vazio")
    return valor


def _mapeamento(valor: object, campo: str) -> dict:
    if not isinstance(valor, dict):
        raise ValueError(f"vcm.yaml: '{campo}' deve ser um mapeamento")  # noqa: TRY004
    return valor


def _inteiro_positivo(valor: object, campo: str) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int) or valor < 1:
        raise ValueError(f"vcm.yaml: '{campo}' deve ser um inteiro >= 1")
    return valor


def _textos_nao_vazios_ou_nada(valor: object, campo: str) -> tuple[str, ...]:
    if valor is None:
        return ()
    if isinstance(valor, list) and all(isinstance(e, str) and e for e in valor):
        return tuple(valor)
    raise ValueError(f"vcm.yaml: '{campo}' deve ser uma lista de textos")


def _ler_dados(arquivo: Path) -> dict:
    """Lê o YAML (se existir); vazio vira mapa vazio e a raiz precisa ser um mapa."""
    if not arquivo.is_file():
        return {}
    try:
        lido = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
    except yaml.YAMLError as erro:
        raise ValueError(f"vcm.yaml: YAML inválido: {erro}") from erro
    if lido is None:
        return {}
    if not isinstance(lido, dict):
        raise ValueError("vcm.yaml: o conteúdo deve ser um mapeamento (chave: valor)")  # noqa: TRY004
    return lido


def _validar_referencia(dados: dict) -> tuple[tuple[str, ...] | None, int]:
    """Valida o bloco `referencia` e devolve (comando, repeticoes)."""
    referencia = _mapeamento(dados.get("referencia") or {}, "referencia")
    comando = referencia.get("comando")
    comando_referencia = (
        None if comando is None else _lista_de_textos(comando, "referencia.comando")
    )
    repeticoes = _inteiro_positivo(referencia.get("repeticoes", 5), "referencia.repeticoes")
    return comando_referencia, repeticoes


def carregar_config(raiz: Path) -> Config:
    """Lê `vcm.yaml` em `raiz`; campos ausentes recebem valores autodetectados ou padrão."""
    raiz = Path(raiz)
    dados = _ler_dados(raiz / NOME_ARQUIVO)
    projeto = _texto_nao_vazio(dados.get("projeto", raiz.resolve().name), "projeto")
    if dados.get("pastas_fonte") is None:
        pastas_fonte = _detectar_pastas_fonte(raiz)
    else:
        pastas_fonte = _lista_de_textos(dados["pastas_fonte"], "pastas_fonte")
    pasta_testes = _texto_nao_vazio(dados.get("pasta_testes", "tests"), "pasta_testes")
    comando_referencia, repeticoes = _validar_referencia(dados)
    limites = _mapeamento(dados.get("limites") or {}, "limites")
    dependencias_extras = _textos_nao_vazios_ou_nada(
        dados.get("dependencias_extras"), "dependencias_extras"
    )
    return Config(
        projeto=projeto,
        pastas_fonte=pastas_fonte,
        pasta_testes=pasta_testes,
        comando_referencia=comando_referencia,
        repeticoes=repeticoes,
        limites=dict(limites),
        dependencias_extras=dependencias_extras,
    )
