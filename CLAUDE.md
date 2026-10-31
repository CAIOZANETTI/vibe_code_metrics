# Regras para agentes neste repositório

Este repositório é desenvolvido com o próprio método (tese T000). Antes de mudar algo, leia:
- `docs/estilo.md`: **regras de código do mantenedor (obrigatórias)**
- `docs/arquitetura.md`: como funciona
- `docs/plano.md`: o que fazer a seguir

## Regras do mantenedor (não negociáveis)
1. **Python em português**: identificadores, docstrings, comentários e mensagens.
2. **Python calcula**: todo cálculo acontece em Python (NumPy vetorizado, pandas ou Polars).
3. **HTML/JS só apresentam** o que o Python calculou; nada de cálculo em JavaScript.
4. **Sistema métrico (SI)**; unidade como sufixo do nome (`comprimento_m`, `vazao_m3s`).

## Ambiente
- Python gerenciado por `uv`: `uv sync`, `uv run pytest`, `uv run ruff check .`, `uv run ruff format .`
- CLI: `uv run vcm --help`

## Agentes
- Gerente: a sessão principal (Opus). Executores: Sonnet (implementação com testes) e Haiku
  (tarefas mecânicas). O Fable não é usado neste momento, por decisão do mantenedor.
- Cada execução de agente é registrada em `results/agentes/execucoes.csv` (modelo, tokens,
  ferramentas, duração, aprovado), que é a base da tese T003.

## Regras de processo
1. **Documentação viva:** ao editar `docs/*.md`, rode `uv run vcm docs` e faça commit do
   `docs/index.html` junto. Nunca edite `docs/index.html` à mão. O CI roda `vcm docs --check`.
2. **Plano:** ao concluir um item de `docs/plano.md`, marque o checkbox no mesmo commit.
3. **Avaliadores e gabaritos são trancados:** não altere `theses/*/avaliador.py`, `theses/*/gabarito/`
   nem `datasets/ground_truth/` sem pedido explícito do humano.
4. **Cálculo de engenharia é determinístico:** sem IA no caminho do resultado final; tolerâncias
   declaradas; cotas e coordenadas com tolerância absoluta.
5. **Retrospectiva:** todo PR inclui o balanço (`vcm balanco`). `REVERTER` bloqueia o merge.
6. **Sem nomes de modelo fixos no código:** use `repertorio/modelos.yaml`.
7. **PRs pequenos**, com testes.
