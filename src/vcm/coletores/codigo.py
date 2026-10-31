"""Coletor de métricas estáticas de código: tamanho, complexidade, dependências e segurança."""

from __future__ import annotations

import json
import subprocess
import sys
import tomllib
from pathlib import Path

from radon.complexity import cc_visit
from radon.raw import analyze

from vcm.config import carregar_config

_PASTAS_IGNORADAS = {".venv", "__pycache__"}
# Ignoradas adicionalmente quando a pasta-fonte é a própria raiz ("."):
_PASTAS_IGNORADAS_NA_RAIZ = {"tests", ".git", ".claude", "results"}


def _listar_arquivos_py(raiz: Path, pastas_fonte: tuple[str, ...]) -> list[Path]:
    """Lista, em ordem determinística, os .py das pastas-fonte, ignorando .venv e __pycache__."""
    arquivos: set[Path] = set()
    for pasta in pastas_fonte:
        base = raiz / pasta
        if not base.is_dir():
            continue
        for caminho in base.rglob("*.py"):
            partes = caminho.relative_to(raiz).parts
            ignoradas = set(_PASTAS_IGNORADAS)
            if Path(pasta).parts == ():  # "." -> raiz do projeto
                ignoradas |= _PASTAS_IGNORADAS_NA_RAIZ
            if not ignoradas.intersection(partes[:-1]):
                arquivos.add(caminho)
    return sorted(arquivos)


def _contar_dependencias(raiz: Path) -> int:
    """Conta as entradas de [project].dependencies do pyproject.toml; sem ele, as linhas
    válidas do requirements.txt (sem comentários, vazias ou opções `-`); 0 se ausentes."""
    caminho = raiz / "pyproject.toml"
    if not caminho.is_file():
        requisitos = raiz / "requirements.txt"
        if not requisitos.is_file():
            return 0
        linhas = (
            linha.split("#", 1)[0].strip()
            for linha in requisitos.read_text(encoding="utf-8").splitlines()
        )
        return sum(1 for linha in linhas if linha and not linha.startswith("-"))
    with caminho.open("rb") as arquivo:
        dados = tomllib.load(arquivo)
    return len(dados.get("project", {}).get("dependencies", []))


def _contar_alertas_seguranca(raiz: Path, pastas_fonte: tuple[str, ...]) -> int:
    """Roda o bandit em subprocesso e conta alertas de severidade MEDIUM ou HIGH."""
    pastas = [str(raiz / p) for p in pastas_fonte if (raiz / p).is_dir()]
    if not pastas:
        return 0
    excluir: list[str] = []
    if any(Path(p).parts == () for p in pastas_fonte):  # raiz inteira: pular pastas não-fonte
        nomes = _PASTAS_IGNORADAS | _PASTAS_IGNORADAS_NA_RAIZ
        excluir = ["-x", ",".join(str(raiz / n) for n in sorted(nomes))]
    # bandit devolve código 1 quando encontra problemas; isso não é erro
    resultado = subprocess.run(
        [sys.executable, "-m", "bandit", "-r", *pastas, *excluir, "-f", "json", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        dados = json.loads(resultado.stdout)
    except json.JSONDecodeError as erro:
        raise RuntimeError(f"saída do bandit inválida: {resultado.stderr.strip()}") from erro
    return sum(1 for r in dados.get("results", []) if r.get("issue_severity") in ("MEDIUM", "HIGH"))


def medir_codigo(raiz: Path, pastas_fonte: tuple[str, ...] | None = None) -> dict[str, float]:
    """Mede o código Python em raiz/<pastas_fonte>.

    Se `pastas_fonte` for None, usa `carregar_config(raiz).pastas_fonte`.

    Retorna:
        sloc: linhas lógicas de código-fonte (radon raw, soma de 'sloc').
        complexidade_media: média da complexidade ciclomática de funções e métodos
            (0.0 se não houver funções).
        n_dependencias: entradas em [project].dependencies do pyproject.toml (sem pyproject: linhas do requirements.txt).
        alertas_seguranca: alertas do bandit com severidade MEDIUM ou HIGH.
        n_funcoes: funções e métodos (cada um contado uma vez).
        sloc_por_funcao: sloc / n_funcoes (0.0 se não houver funções).
        n_arquivos_py: arquivos .py medidos (parseados com sucesso).
        arquivos_com_erro: arquivos .py que não puderam ser lidos ou parseados.
    """
    raiz = Path(raiz)
    if pastas_fonte is None:
        pastas_fonte = carregar_config(raiz).pastas_fonte
    sloc = 0
    complexidades: list[int] = []
    n_arquivos = 0
    n_erros = 0
    for caminho in _listar_arquivos_py(raiz, pastas_fonte):
        try:
            codigo = caminho.read_text(encoding="utf-8")
            sloc_arquivo = analyze(codigo).sloc
            blocos = cc_visit(codigo)
        except (SyntaxError, ValueError, UnicodeDecodeError, OSError):
            n_erros += 1
            continue
        n_arquivos += 1
        sloc += sloc_arquivo
        for bloco in blocos:
            if hasattr(bloco, "methods"):  # classe: seus métodos são contados à parte
                continue
            complexidades.append(bloco.complexity)
    n_funcoes = len(complexidades)
    complexidade_media = sum(complexidades) / len(complexidades) if complexidades else 0.0
    return {
        "sloc": float(sloc),
        "complexidade_media": float(complexidade_media),
        "n_dependencias": float(_contar_dependencias(raiz)),
        "alertas_seguranca": float(_contar_alertas_seguranca(raiz, pastas_fonte)),
        "n_funcoes": float(n_funcoes),
        "sloc_por_funcao": float(sloc / n_funcoes) if n_funcoes else 0.0,
        "n_arquivos_py": float(n_arquivos),
        "arquivos_com_erro": float(n_erros),
    }
