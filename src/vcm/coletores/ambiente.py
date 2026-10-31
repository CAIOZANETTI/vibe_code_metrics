"""Ambiente de execução do projeto medido (com `pyproject.toml`, só `requirements.txt` ou nenhum)."""

from __future__ import annotations

from pathlib import Path


def prefixo_uv(raiz: Path, extras: tuple[str, ...] = ()) -> list[str]:
    """Prefixo `uv run` para executar comandos no ambiente do projeto em `raiz`.

    - com `pyproject.toml`: `uv run --directory <raiz>` (o uv sincroniza o projeto);
    - só com `requirements.txt`: `--no-project` e `--with-requirements requirements.txt`;
    - sem nenhum dos dois: `--no-project`.
    `extras` viram `--with` em todos os casos.
    """
    raiz = Path(raiz)
    prefixo = ["uv", "run"]
    if (raiz / "pyproject.toml").is_file():
        prefixo += ["--directory", str(raiz)]
    elif (raiz / "requirements.txt").is_file():
        prefixo += ["--no-project", "--directory", str(raiz)]
        prefixo += ["--with-requirements", "requirements.txt"]
    else:
        prefixo += ["--no-project", "--directory", str(raiz)]
    for extra in extras:
        prefixo += ["--with", extra]
    return prefixo
