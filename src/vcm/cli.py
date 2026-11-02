"""Linha de comando `vcm`."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from vcm import docs


def _cmd_docs(args: argparse.Namespace) -> int:
    pasta = Path(args.pasta)
    if args.artefato:
        print(f"{docs.gerar_artefato(pasta, Path(args.artefato))} gerado (página para o claude.ai)")
        return 0
    ok = docs.gerar(pasta, check=args.check)
    if args.check and not ok:
        print(
            f"{pasta / docs.SAIDA_PADRAO} está desatualizado. Rode: uv run vcm docs",
            file=sys.stderr,
        )
        return 1
    print(f"{pasta / docs.SAIDA_PADRAO} {'verificado' if args.check else 'gerado'}")
    return 0


def _cmd_html(args: argparse.Namespace) -> int:
    saida = docs.gerar_avulso(Path(args.markdown), Path(args.saida) if args.saida else None)
    print(f"{saida} gerado")
    return 0


def _cmd_snapshot(args: argparse.Namespace) -> int:
    from vcm import snapshot as snap

    linha = snap.obter_snapshot(
        Path(args.repo),
        args.ref,
        refazer=args.refazer,
        repeticoes_determinismo=args.repeticoes,
        com_testes=not args.sem_testes,
    )
    print(linha.to_string())
    return 0


def _cmd_balanco(args: argparse.Namespace) -> int:
    from vcm import cartao
    from vcm import snapshot as snap

    repo = Path(args.repo)
    opcoes = {"repeticoes_determinismo": args.repeticoes, "com_testes": not args.sem_testes}
    antes = snap.obter_snapshot(repo, args.base, refazer=args.refazer, **opcoes)
    depois = snap.obter_snapshot(repo, args.alvo, refazer=args.refazer, **opcoes)
    from vcm import ruido
    from vcm.config import carregar_config

    config = carregar_config(repo)
    resultado = snap.retrospectiva(antes, depois, ruido_medido=ruido.carregar())
    if not args.sem_sessoes:
        resultado["custo_iteracao"] = _custo_iteracao(repo, antes, depois)
    caminhos = cartao.gravar(resultado, snap.PASTA_ITERACOES, limites=config.limites)
    print(cartao.markdown(resultado, limites=config.limites))
    print(f"Cartão HTML: {caminhos['html']}")
    if args.falhar_se_reverter and resultado["decisao"].value == "REVERTER":
        return 2
    return 0


def _custo_iteracao(repo: Path, antes, depois):
    """Gasto dos agentes entre os dois commits, a partir dos logs locais (None se não houver)."""
    import pandas as pd

    from vcm.coletores import sessoes

    if not sessoes.PASTA_PADRAO.is_dir():
        return None
    precos_arq = repo / "repertorio" / "modelos.yaml"
    if not precos_arq.exists():  # outro projeto: usa a cópia empacotada no vcm
        precos_arq = Path(__file__).with_name("modelos_precos.yaml")
    precos = sessoes.carregar_precos(precos_arq)
    chamadas = sessoes.ler_chamadas()
    inicio = pd.Timestamp(antes["data_commit"]).tz_convert("UTC")
    fim = pd.Timestamp(depois["data_commit"]).tz_convert("UTC")
    return sessoes.custo_da_iteracao(chamadas, repo, inicio, fim, precos)


def _cmd_agentes(args: argparse.Namespace) -> int:
    from vcm import agentes

    if args.pdca and args.arquivo:
        print("erro: use --pdca ou --arquivo, não os dois", file=sys.stderr)
        return 1
    if args.pdca:
        tabela = agentes.ler_pdca(Path(args.pdca))
    else:
        tabela = agentes.ler(Path(args.arquivo) if args.arquivo else agentes.ARQUIVO_PADRAO)
    print(agentes.resumo_por_modelo(tabela).to_string())
    return 0


def _cmd_sessoes(args: argparse.Namespace) -> int:
    import pandas as pd

    from vcm import formatacao
    from vcm.coletores import sessoes

    chamadas = sessoes.ler_chamadas(Path(args.pasta), args.projeto)
    if chamadas.empty:
        print("Nenhuma chamada encontrada.")
        return 0
    invalidas = chamadas.attrs.get("linhas_invalidas", 0)
    por_agente = sessoes.resumo_por_agente(chamadas)
    arquivo_precos = Path("repertorio/modelos.yaml")
    com_custo = arquivo_precos.exists()
    if com_custo:
        precos = sessoes.carregar_precos(arquivo_precos)
        chamadas["custo_usd"] = sessoes.custo_usd(chamadas, precos)
        custo_por_agente = chamadas.groupby(
            [chamadas["sessao_id"], chamadas["agente_id"].fillna("")]
        )["custo_usd"].sum(min_count=1)
        chaves = pd.MultiIndex.from_arrays(
            [por_agente["sessao_id"], por_agente["agente_id"].fillna("")]
        )
        por_agente["custo_usd"] = custo_por_agente.reindex(chaves).to_numpy()
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    chamadas.to_parquet(saida / "chamadas.parquet", index=False)
    por_agente.to_parquet(saida / "por_agente.parquet", index=False)

    tabela = pd.DataFrame(
        {
            "tipo": por_agente["tipo_agente"],
            "descricao": por_agente["descricao"].fillna("").str.slice(0, 40),
            "modelo": por_agente["modelo"],
            "chamadas": por_agente["chamadas"],
            "tokens_total": por_agente["tokens_total"],
            "duracao_s": por_agente["duracao_s"].round(1),
        }
    )
    por_modelo = por_agente.groupby("modelo")[["chamadas", "tokens_total"]].sum()
    if com_custo:
        tabela["custo_usd"] = por_agente["custo_usd"].round(2)
        por_modelo["custo_usd"] = (
            por_agente.groupby("modelo")["custo_usd"].sum(min_count=1).round(2)
        )
    print(tabela.to_string(index=False))
    print()
    print(por_modelo.to_string())
    print(f"\nChamadas únicas: {formatacao.numero(len(chamadas), 0)}")
    if invalidas:
        print(f"Linhas inválidas ignoradas: {invalidas}")
    if com_custo:
        print("Aviso: custo equivalente de API; em plano de assinatura não é o gasto real.")
    print(f"Gravado em {saida}")
    return 0


def _cmd_iniciar(args: argparse.Namespace) -> int:
    from vcm import iniciar

    destino = Path(args.destino)
    try:
        itens = iniciar.iniciar(destino, args.pacote, forcar=args.forcar)
    except ValueError as erro:
        print(f"erro: {erro}", file=sys.stderr)
        return 1
    for caminho, status in itens:
        print(f"{caminho} -> {status}")
    passos = []
    if not (destino / ".git").exists():
        passos.append(f"git init   (dentro de {destino})")
    raiz = iniciar.detectar_layout(destino, args.pacote) == "raiz"
    if (destino / "pyproject.toml").exists():
        passos.append("uv sync && uv run pytest -q")
    elif raiz:
        passos.append(
            f"preencha {args.pacote}/referencia.py com os seus cálculos e rode "
            f"python -m {args.pacote}.referencia"
        )
    else:
        passos.append(
            f"uv init --lib --name {args.pacote} . && uv add numpy pandas && uv add --dev pytest"
        )
        passos.append("uv sync && uv run pytest -q")
    passos.append("git add -A && git commit -m 'Adota o método Vibe Code Metrics'")
    passos.append("Após a primeira iteração: vcm balanco HEAD~1 HEAD")
    print("\nPróximos passos:")
    for numero, passo in enumerate(passos, start=1):
        print(f"  {numero}. {passo}")
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="vcm", description="Vibe Code Metrics")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("docs", help="gera docs/index.html a partir dos Markdown")
    d.add_argument("--pasta", default="docs")
    d.add_argument("--check", action="store_true", help="falha se o HTML estiver desatualizado")
    d.add_argument("--artefato", default=None, help="gera a versão para publicar no claude.ai")
    d.set_defaults(func=_cmd_docs)

    h = sub.add_parser("html", help="converte um Markdown (relatório) em HTML formatado")
    h.add_argument("markdown")
    h.add_argument("-o", "--saida", default=None)
    h.set_defaults(func=_cmd_html)

    def opcoes_medicao(sp: argparse.ArgumentParser) -> None:
        sp.add_argument("--repo", default=".")
        sp.add_argument(
            "--repeticoes",
            type=int,
            default=None,
            help="repetições de determinismo (padrão: vcm.yaml)",
        )
        sp.add_argument("--sem-testes", action="store_true", help="não roda a suíte de testes")
        sp.add_argument("--refazer", action="store_true", help="ignora o cache de snapshots")

    s = sub.add_parser("snapshot", help="mede as métricas do código num ref do git")
    s.add_argument("ref", nargs="?", default="HEAD")
    opcoes_medicao(s)
    s.set_defaults(func=_cmd_snapshot)

    b = sub.add_parser("balanco", help="retrospectiva da iteração entre dois refs")
    b.add_argument("base")
    b.add_argument("alvo", nargs="?", default="HEAD")
    b.add_argument("--falhar-se-reverter", action="store_true", help="código 2 se REVERTER")
    b.add_argument(
        "--sem-sessoes", action="store_true", help="não lê os logs locais de sessão (gasto)"
    )
    opcoes_medicao(b)
    b.set_defaults(func=_cmd_balanco)

    a = sub.add_parser("agentes", help="resumo das execuções de agentes por modelo")
    a.add_argument(
        "--pdca", metavar="CAMINHO", help="lê um pdca/agentes.jsonl (projetos_em_camadas)"
    )
    a.add_argument(
        "--arquivo",
        metavar="CAMINHO",
        help="lê um CSV de execuções (padrão: results/agentes/execucoes.csv)",
    )
    a.set_defaults(func=_cmd_agentes)

    se = sub.add_parser("sessoes", help="telemetria dos logs de sessão do Claude Code")
    se.add_argument("--pasta", default=str(Path.home() / ".claude" / "projects"))
    se.add_argument("--projeto", default=None, help="filtro (substring) do nome do projeto")
    se.add_argument("--saida", default="results/sessoes")
    se.set_defaults(func=_cmd_sessoes)

    i = sub.add_parser("iniciar", help="adota o método num projeto (novo ou existente)")
    i.add_argument("destino", nargs="?", default=".")
    i.add_argument("--pacote", required=True, help="nome do pacote Python em src/")
    i.add_argument("--forcar", action="store_true", help="sobrescreve arquivos existentes")
    i.set_defaults(func=_cmd_iniciar)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
