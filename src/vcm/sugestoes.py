"""Correções sugeridas a partir das medições (o vcm sugere; nunca aplica).

Princípio do mantenedor: o repositório de métricas não arruma, sugere. Quem corrige é um
agente, com aprovação humana. Todo texto é montado aqui, em Python; o HTML só apresenta.

Cada sugestão é um dicionário com `prioridade` ("alta" | "média" | "baixa"), `dimensao`,
`metrica`, `o_que` (ação concreta), `por_que` (com o número medido) e `agente_sugerido`.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from radon.complexity import cc_rank, cc_visit

from vcm import formatacao as fmt
from vcm import semaforo as sem
from vcm.balanco import METRICAS_PADRAO
from vcm.coletores.codigo import _listar_arquivos_py
from vcm.config import carregar_config

FRASE_FIXA = (
    "Sugestões geradas pelo vcm a partir das medições; nada foi alterado. "
    "Aplicar exige aprovação humana."
)
ORDEM_PRIORIDADE = {"alta": 0, "média": 1, "baixa": 2}
LIMITE_LISTA = 5
METRICAS_EFICIENCIA = (
    "tempo_referencia_ms",
    "tempo_p50_ms",
    "tempo_p95_ms",
    "pico_ram_mb",
    "custo_usd",
)
FORA_DO_VERDE = ("amarelo", "vermelho")
PASTAS_FORA_DA_RAIZ = (".venv", "tests", ".git", ".claude", "results")

# Desvios do rumo: tipo -> (prioridade, ação, agente sugerido)
ACOES_RUMO = {
    "fora do plano": (
        "média",
        "registrar a mudança como etapa nova no rumo.yaml ou reverter o arquivo",
        "humano",
    ),
    "estouro": ("média", "dividir a etapa em partes menores ou recalibrar a estimativa", "opus"),
    "parada": (
        "alta",
        "verificar com o humano se há bloqueio e, se houver, marcar a etapa como bloqueada",
        "humano",
    ),
    "entregável ausente": (
        "alta",
        "criar o entregável ou corrigir o status da etapa",
        "sonnet",
    ),
}


def _sugestao(prioridade: str, metrica: str, o_que: str, por_que: str, agente: str) -> dict:
    return {
        "prioridade": prioridade,
        "dimensao": METRICAS_PADRAO[metrica].pergunta,
        "metrica": metrica,
        "o_que": o_que,
        "por_que": por_que,
        "agente_sugerido": agente,
    }


@dataclass
class _Contexto:
    """Medições já organizadas para as regras: tabela do balanço, estado e raiz opcional."""

    tabela: pd.DataFrame
    valores: pd.Series
    estado: pd.DataFrame
    raiz: Path | None

    def valor(self, metrica: str) -> float | None:
        if metrica not in self.valores.index or pd.isna(self.valores[metrica]):
            return None
        return float(self.valores[metrica])

    def piorou(self, metrica: str) -> bool:
        return metrica in self.tabela.index and self.tabela.loc[metrica, "veredito"] == "piorou"

    def cor(self, metrica: str) -> str:
        return self.estado.loc[metrica, "cor"] if metrica in self.estado.index else "cinza"

    def fora_do_verde(self, metrica: str) -> bool:
        return self.cor(metrica) in FORA_DO_VERDE

    def por_que(self, metrica: str) -> str:
        """Valor medido, cor e regra do semáforo e, se piorou, a variação do balanço."""
        valor = self.valor(metrica)
        casas = 0 if valor is not None and valor.is_integer() else 3
        texto = f"{metrica} = {fmt.numero(valor, casas)}"
        if self.cor(metrica) != "cinza":
            texto += f" ({self.cor(metrica)}; {self.estado.loc[metrica, 'regra']})"
        if self.piorou(metrica):
            linha = self.tabela.loc[metrica]
            texto += (
                f"; piorou de {fmt.numero(linha['antes'], casas)} para "
                f"{fmt.numero(linha['depois'], casas)} ({fmt.percentual(linha['variacao_pct'])})"
            )
        return texto


def _relativo(caminho: str | Path, raiz: Path) -> str:
    try:
        return Path(caminho).resolve().relative_to(Path(raiz).resolve()).as_posix()
    except ValueError:
        return str(caminho)


def _comando_bandit(raiz: Path) -> list[str]:
    """Comando do bandit sobre as pastas-fonte do projeto (vazio se não houver pasta)."""
    pastas_fonte = carregar_config(raiz).pastas_fonte
    pastas = [str(raiz / p) for p in pastas_fonte if (raiz / p).is_dir()]
    if not pastas:
        return []
    comando = [sys.executable, "-m", "bandit", "-r", *pastas, "-f", "json", "-q"]
    if any(Path(p).parts == () for p in pastas_fonte):  # raiz inteira: pular pastas não-fonte
        comando += ["-x", ",".join(str(raiz / n) for n in PASTAS_FORA_DA_RAIZ)]
    return comando


def _alertas_bandit(raiz: Path) -> list[str]:
    """Alertas MEDIUM/HIGH do bandit como 'arquivo:linha código' (vazio se não conseguir ler)."""
    raiz = Path(raiz)
    comando = _comando_bandit(raiz)
    if not comando:
        return []
    saida = subprocess.run(comando, capture_output=True, text=True, check=False).stdout
    try:
        achados = json.loads(saida).get("results", [])
    except json.JSONDecodeError:
        return []
    graves = [a for a in achados if a.get("issue_severity") in ("MEDIUM", "HIGH")]
    return [
        f"{_relativo(a['filename'], raiz)}:{a['line_number']} {a['test_id']}"
        for a in sorted(graves, key=lambda a: (a["filename"], a["line_number"]))
    ]


def _funcoes_do_arquivo(caminho: Path, raiz: Path) -> list[tuple[int, str, int, str]]:
    """(complexidade, arquivo, linha, nome) das funções e métodos de um arquivo."""
    try:
        blocos = cc_visit(caminho.read_text(encoding="utf-8"))
    except (SyntaxError, ValueError, UnicodeDecodeError, OSError):
        return []
    arquivo = _relativo(caminho, raiz)
    # Classes ficam de fora: seus métodos já aparecem como blocos próprios.
    return [
        (b.complexity, arquivo, b.lineno, b.fullname) for b in blocos if not hasattr(b, "methods")
    ]


def _funcoes_mais_complexas(raiz: Path, quantidade: int = LIMITE_LISTA) -> list[str]:
    """As piores funções por complexidade ciclomática: 'arquivo nome (nota, letra)'."""
    raiz = Path(raiz)
    funcoes = [
        f
        for caminho in _listar_arquivos_py(raiz, carregar_config(raiz).pastas_fonte)
        for f in _funcoes_do_arquivo(caminho, raiz)
    ]
    piores = sorted(funcoes, key=lambda f: (-f[0], f[1], f[2]))[:quantidade]
    return [f"{arq} {nome} ({nota}, {cc_rank(nota)})" for nota, arq, _, nome in piores]


def _com_lista(texto: str, itens: list[str]) -> str:
    return f"{texto}: {'; '.join(itens)}" if itens else texto


def _regra_testes(ctx: _Contexto) -> list[dict]:
    if (ctx.valor("testes_falhando") or 0) <= 0:
        return []
    return [
        _sugestao(
            "alta",
            "testes_falhando",
            "corrigir os testes que falham antes do merge (a decisão do balanço é REVERTER)",
            ctx.por_que("testes_falhando"),
            "sonnet",
        )
    ]


def _regra_seguranca(ctx: _Contexto) -> list[dict]:
    if (ctx.valor("alertas_seguranca") or 0) <= 0:
        return []
    alertas = _alertas_bandit(ctx.raiz) if ctx.raiz is not None else []
    o_que = _com_lista("corrigir os alertas de segurança do bandit", alertas[:LIMITE_LISTA])
    return [
        _sugestao("alta", "alertas_seguranca", o_que, ctx.por_que("alertas_seguranca"), "sonnet")
    ]


def _regra_determinismo(ctx: _Contexto) -> list[dict]:
    fracao = ctx.valor("frac_execucoes_identicas")
    if fracao is None or fracao >= 1:
        return []
    o_que = (
        "fixar a semente e o número de threads (por exemplo OPENBLAS_NUM_THREADS=1): "
        "o repertório do NumPy registra que a ordem das somas varia com as threads do BLAS"
    )
    por_que = ctx.por_que("frac_execucoes_identicas")
    return [_sugestao("alta", "frac_execucoes_identicas", o_que, por_que, "sonnet")]


def _regra_complexidade(ctx: _Contexto) -> list[dict]:
    metrica = "complexidade_media"
    if ctx.valor(metrica) is None or not (ctx.piorou(metrica) or ctx.fora_do_verde(metrica)):
        return []
    piores = _funcoes_mais_complexas(ctx.raiz) if ctx.raiz is not None else []
    o_que = _com_lista("refatorar as funções mais complexas", piores)
    return [_sugestao("média", metrica, o_que, ctx.por_que(metrica), "sonnet")]


def _regra_tamanho_de_funcao(ctx: _Contexto) -> list[dict]:
    metrica = "sloc_por_funcao"
    if ctx.valor(metrica) is None or not ctx.fora_do_verde(metrica):
        return []
    o_que = "quebrar as funções longas em funções menores, uma responsabilidade por função"
    return [_sugestao("média", metrica, o_que, ctx.por_que(metrica), "sonnet")]


def _regra_cobertura(ctx: _Contexto) -> list[dict]:
    metrica = "cobertura_testes"
    if ctx.valor(metrica) is None or not (ctx.piorou(metrica) or ctx.fora_do_verde(metrica)):
        return []
    o_que = "acrescentar testes nos módulos com menor cobertura"
    return [_sugestao("média", metrica, o_que, ctx.por_que(metrica), "sonnet")]


def _regra_dependencias(ctx: _Contexto) -> list[dict]:
    metrica = "n_dependencias"
    if not ctx.piorou(metrica):
        return []
    o_que = "justificar no PR a dependência nova ou removê-la"
    return [_sugestao("baixa", metrica, o_que, ctx.por_que(metrica), "humano")]


def _regra_eficiencia(ctx: _Contexto) -> list[dict]:
    return [
        _sugestao(
            "baixa",
            metrica,
            "perfilar o conjunto de referência para achar a origem da perda de eficiência",
            ctx.por_que(metrica),
            "sonnet",
        )
        for metrica in METRICAS_EFICIENCIA
        if ctx.piorou(metrica)
    ]


REGRAS = (
    _regra_testes,
    _regra_seguranca,
    _regra_determinismo,
    _regra_complexidade,
    _regra_tamanho_de_funcao,
    _regra_cobertura,
    _regra_dependencias,
    _regra_eficiencia,
)


def do_balanco(
    resultado: dict, raiz: Path | None = None, limites: dict | None = None
) -> list[dict]:
    """Sugestões a partir da tabela do balanço e do semáforo de estado, por prioridade.

    `limites` são sobreposições do projeto aos limites padrão (como em `vcm.cartao`).
    Com `raiz`, as sugestões listam os alvos concretos (alertas do bandit, funções complexas).
    """
    tabela = resultado["tabela"]
    valores = resultado.get("depois_valores")
    if valores is None:
        valores = tabela["depois"]
    estado = sem.avaliar_estado(valores, sem.carregar_limites(limites))
    ctx = _Contexto(tabela=tabela, valores=valores, estado=estado, raiz=raiz)
    sugestoes = [s for regra in REGRAS for s in regra(ctx)]
    return sorted(sugestoes, key=lambda s: ORDEM_PRIORIDADE[s["prioridade"]])


def do_rumo(desvios: list[dict]) -> list[dict]:
    """Sugestões a partir dos desvios do rumo (mesmo formato de `do_balanco`)."""
    sugestoes = []
    for desvio in desvios:
        prioridade, o_que, agente = ACOES_RUMO.get(
            desvio["tipo"], ("baixa", "examinar o desvio com o humano", "humano")
        )
        sugestoes.append(
            {
                "prioridade": prioridade,
                "dimensao": "rumo",
                "metrica": desvio.get("etapa") or desvio["tipo"],
                "o_que": o_que,
                "por_que": f"{desvio['tipo']}: {desvio['detalhe']}",
                "agente_sugerido": agente,
            }
        )
    return sorted(sugestoes, key=lambda s: ORDEM_PRIORIDADE[s["prioridade"]])


def _celula(texto: str) -> str:
    return texto.replace("|", "\\|")


def markdown(sugestoes: list[dict]) -> str:
    """Seção "Correções sugeridas" (tabela e a frase fixa)."""
    linhas = ["### Correções sugeridas", ""]
    if sugestoes:
        linhas += [
            "| Prioridade | O quê | Por quê | Agente |",
            "|---|---|---|---|",
            *[
                f"| {s['prioridade']} | {_celula(s['o_que'])} | {_celula(s['por_que'])} "
                f"| {s['agente_sugerido']} |"
                for s in sugestoes
            ],
        ]
    else:
        linhas.append("Nenhuma correção sugerida pelas medições.")
    linhas += ["", f"_{FRASE_FIXA}_", ""]
    return "\n".join(linhas)
