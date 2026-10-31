# Regras para agentes neste repositório

Este repositório é desenvolvido com o próprio método (tese T000). Antes de mudar algo, leia
`docs/arquitetura.md` (como funciona) e `docs/plano.md` (o que fazer a seguir).

## Ambiente
- Python gerenciado por `uv`: `uv sync`, `uv run pytest`, `uv run ruff check .`
- CLI: `uv run vcm --help`

## Regras
1. **Documentação viva:** ao editar `docs/*.md`, rode `uv run vcm docs` e faça commit do
   `docs/index.html` junto. Nunca edite `docs/index.html` à mão. O CI roda `vcm docs --check`.
2. **Plano:** ao concluir um item de `docs/plano.md`, marque o checkbox no mesmo PR.
3. **Avaliadores e gabaritos são trancados:** não altere `theses/*/avaliador.py`, `theses/*/gabarito/`
   nem `datasets/ground_truth/` sem pedido explícito do humano.
4. **Cálculo de engenharia é determinístico:** sem IA no caminho do resultado final; tolerâncias
   declaradas; cotas e coordenadas com tolerância absoluta.
5. **Retrospectiva:** a partir da Fase 1, todo PR inclui o balanço (`vcm balanco`). Se o resultado
   for `REVERTER`, não faça merge.
6. **Sem nomes de modelo fixos no código:** use `repertorio/modelos.yaml`.
7. **PRs pequenos**, com testes.
