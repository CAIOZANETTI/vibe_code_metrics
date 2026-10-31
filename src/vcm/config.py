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


def carregar_config(raiz: Path) -> Config:
    """Lê `vcm.yaml` em `raiz`; campos ausentes recebem valores autodetectados ou padrão."""
    raiz = Path(raiz)
    arquivo = raiz / NOME_ARQUIVO
    dados: dict = {}
    if arquivo.is_file():
        try:
            lido = yaml.safe_load(arquivo.read_text(encoding="utf-8"))
        except yaml.YAMLError as erro:
            raise ValueError(f"vcm.yaml: YAML inválido: {erro}") from erro
        if lido is None:
            lido = {}
        if not isinstance(lido, dict):
            raise ValueError("vcm.yaml: o conteúdo deve ser um mapeamento (chave: valor)")
        dados = lido

    projeto = dados.get("projeto", raiz.resolve().name)
    if not isinstance(projeto, str) or not projeto:
        raise ValueError("vcm.yaml: 'projeto' deve ser um texto não vazio")

    if dados.get("pastas_fonte") is None:
        pastas_fonte = _detectar_pastas_fonte(raiz)
    else:
        pastas_fonte = _lista_de_textos(dados["pastas_fonte"], "pastas_fonte")

    pasta_testes = dados.get("pasta_testes", "tests")
    if not isinstance(pasta_testes, str) or not pasta_testes:
        raise ValueError("vcm.yaml: 'pasta_testes' deve ser um texto não vazio")

    referencia = dados.get("referencia") or {}
    if not isinstance(referencia, dict):
        raise ValueError("vcm.yaml: 'referencia' deve ser um mapeamento")  # noqa: TRY004
    comando = referencia.get("comando")
    comando_referencia = (
        None if comando is None else _lista_de_textos(comando, "referencia.comando")
    )
    repeticoes = referencia.get("repeticoes", 5)
    if isinstance(repeticoes, bool) or not isinstance(repeticoes, int) or repeticoes < 1:
        raise ValueError("vcm.yaml: 'referencia.repeticoes' deve ser um inteiro >= 1")

    limites = dados.get("limites") or {}
    if not isinstance(limites, dict):
        raise ValueError("vcm.yaml: 'limites' deve ser um mapeamento")  # noqa: TRY004

    return Config(
        projeto=projeto,
        pastas_fonte=pastas_fonte,
        pasta_testes=pasta_testes,
        comando_referencia=comando_referencia,
        repeticoes=repeticoes,
        limites=dict(limites),
    )
