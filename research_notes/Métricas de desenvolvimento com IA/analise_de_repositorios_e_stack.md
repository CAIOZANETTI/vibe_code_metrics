# Análise de repositórios e stack Python para métricas de qualidade, evolução e contribuição de IA (greenfield e brownfield)

> Notas de pesquisa (estado: 31/out/2026). Legenda: **[V]** = verificado nesta sessão por busca ou fetch; **[NV]** = URL ou fato vindo de conhecimento prévio, sem verificação nesta sessão. O redator deve conferir os itens [NV] ou tratá-los como tal. Orçamento de pesquisa limitado (cerca de 15 chamadas), então várias versões e datas de release ficaram como lacunas.

## 1. Mineração de Git: PyDriller/GitPython, churn, retrabalho (definição GitClear), frequência, lead time, burndown (git-of-theseus/hercules)

### Takeaway
PyDriller (sobre GitPython) é a base mais prática em Python para extrair commits, arquivos e linhas adicionadas/removidas para DataFrames do pandas. O "churn" no sentido da GitClear (linhas revertidas ou alteradas pouco depois de escritas, janela de cerca de 2 semanas segundo fonte secundária) não sai pronto de nenhuma ferramenta open source. É preciso implementar rastreamento por linha (blame por commit ou diff hunks com idade da linha), o que dá para fazer em Python com PyDriller e `git blame`.

### Cited Findings
- **PyDriller**: a versão mais recente é a 2.7 (suporte a mailmap, checagem de Git > 2.38 e método que retorna linhas adicionadas e removidas por arquivo). Não achei release com tag em 2025, mas houve push no repositório em 28/dez/2025, então o projeto segue ativo, com cadência lenta. — [GitHub releases pydriller](https://github.com/ishepard/pydriller/releases?page=1) [V]; [gittrend](https://gittrend.io/repo/ishepard/pydriller) [V]; [Safety changelog](https://data.safetycli.com/packages/pypi/pydriller/changelog?page=4) [V]
- **hercules + labours** (Go + Python para plots): o "burndown" de projeto é "exatamente o que o git-of-theseus faz, porém muito mais rápido". Há burndown por arquivo e por pessoa. O build precisa de Go >= 1.11 e protoc. Não confirmei se o repositório src-d/hercules está arquivado. A src-d (source{d}) encerrou atividades por volta de 2020 [NV], e existem forks como akx/hercules. — [pkg.go.dev src-d/hercules](https://pkg.go.dev/github.com/src-d/hercules) [V]; [fork akx/hercules](https://github.com/akx/hercules) [V]
- **git-of-theseus** (Erik Bernhardsson): gera curvas de sobrevivência e coortes de linhas por ano. URL: https://github.com/erikbern/git-of-theseus [NV]. Manutenção baixa ou estável [NV].
- **gitinspector**: https://github.com/ejwa/gitinspector [NV]. Considerado **não mantido** (último release por volta de 2015–2016) [NV], então não deve ser recomendado.
- **GitClear: definições e números (relatório 2025)**: foram analisadas 211 milhões de linhas alteradas (2020–2024) de repositórios do Google, Microsoft, Meta e empresas. As linhas ligadas a refatoração ("moved") caíram de cerca de 25% (2021) para menos de 10% (2024). As linhas "copy/pasted (cloned)" subiram de 8,3% para 12,3%. A página do relatório **não** define a janela de churn nem explica como detecta clones ou código assistido por IA. — [GitClear AI Code Quality 2025](https://www.gitclear.com/ai_assistant_code_quality_2025_research) [V]
- "Moved code" na definição da GitClear (relatório 2023/24): linha recortada e colada em outro arquivo ou em outra função do mesmo arquivo. O churn de todas as linhas subiu de 3,3% (2021) para 5,7% (2024). A metodologia exclui ruído (mesmo código em vários branches, linhas em branco). — [resumo do relatório, Amplenote GitClear](https://public.amplenote.com/BL6RLiQo6qqwoP7HNf6gqcRo) [V, cópia publicada pela GitClear]; [devclass](https://devclass.com/2024/01/24/ai-assistance-is-leading-to-lower-code-quality-claim-researchers/) [V]
- Janela de churn da GitClear: "porcentagem de linhas revertidas ou modificadas em até duas semanas após serem escritas", atribuída ao relatório "Coding on Copilot" (2024). A fonte é **secundária**, um rascunho de enciclopédia. — [cavac.at Draft:GitClear](https://cavac.at/cavacopedia/Draft%3AGitClear) [V, fonte fraca]. A Minware usa definição própria: código revertido em até 1 dia ou "churned" em até 2 semanas. — [Minware Code Churn](https://www.minware.com/product/insights/quality/code-churn) [V]
- Um número de churn de 7,1% em 2025 atribuído à GitClear aparece só em fonte de terceiros, sem confirmação. — [Larridin](https://larridin.com/developer-productivity-hub/code-churn-ai-era-doubled) [V, não confirmado na fonte primária]
- A própria GitClear critica o churn como métrica isolada de produtividade. — [GitClear blog](https://www.gitclear.com/blog/minimize_technical_debt_and_churn) [V]

### Inferences
- **Coleta recomendada (Python)**: `pydriller.Repository(path, since=..., only_no_merge=True).traverse_commits()` produz uma linha por (commit, arquivo) com `hash, author_date, committer_date, added_lines, deleted_lines, nloc, complexity, change_type, msg`. O resultado vai para `pd.DataFrame` e é salvo como Parquet (`commits.parquet`, `file_changes.parquet`). PyDriller também expõe `dmm_unit_size/complexity/interfacing` (Delta Maintainability Model) por commit [NV, conferir docs: https://pydriller.readthedocs.io].
- **Churn / retrabalho no estilo GitClear (implementação própria)**: para cada commit C e arquivo F, use `modified_file.diff_parsed['deleted']` para pegar as linhas removidas ou alteradas. Rode `git blame -w -M -C --line-porcelain C^ -- F` para descobrir em qual commit e data cada linha nasceu. Se `C.date - origem.date <= 14 dias` (parâmetro N), a linha conta como retrabalho. `rework_rate = linhas_retrabalhadas / linhas_alteradas` por semana ou PR. Para separar "moved" de "copy/paste", use `git blame -M -C` (detecta movimento entre arquivos) ou `git diff --color-moved` [NV]. Para duplicação, use jscpd ou pylint (seção 2).
- **Frequência de commits**: `df.resample('W', on='author_date').size()`. **Lead time**: para PRs, use a API do GitHub (`gh pr list --state merged --json number,createdAt,mergedAt,commits`) e calcule `mergedAt - first_commit_date`. O commit-to-deploy (DORA) exige registro de deploy (tags ou releases).
- Burndown e sobrevivência de linhas: git-of-theseus é simples (`git-of-theseus-analyze repo` gera JSON que pode ser lido no pandas) [NV]. hercules é mais rápido, mas exige Go. Para projetos pessoais pequenos, uma implementação própria com `git blame` por snapshot mensal basta.

### Gaps
- Não consegui ler a definição primária e atual de churn da GitClear (janela exata e tratamento de moves) no site dela. Fica a fonte secundária.
- Status de arquivamento do src-d/hercules e do git-of-theseus em 2026 não verificado.
- Não verifiquei se existe biblioteca Python pronta que implemente "rework rate" por idade de linha. Até onde sei, não existe uma padrão.

## 2. Qualidade estática: radon/xenon, ruff, mypy/pyright, bandit/semgrep, vulture, duplicação (jscpd/pylint), wily

### Takeaway
Para um repositório Python de engenharia, o conjunto mínimo é ruff (lint, rápido, saída JSON), radon (CC, MI, Halstead em JSON), mypy ou pyright (type errors), bandit (segurança), vulture (código morto) e jscpd ou pylint `duplicate-code` (duplicação). wily serve para histórico por commit, mas está com manutenção irregular. Todos emitem JSON que vira DataFrame com `pd.json_normalize`.

### Cited Findings
- **radon** calcula complexidade ciclomática, métricas brutas (SLOC, comentários, linhas em branco), Halstead e Maintainability Index. A última versão vista no PyPI é a 6.0.1 (data não exibida no resultado). **xenon** é a contraparte de "monitoramento" (falha o build acima de um limiar), e radon é a ferramenta de "relatório". — [PyPI radon](https://pypi.org/project/radon) [V]; [ecosyste.ms rubik/radon](https://awesome.ecosyste.ms/projects/github.com%2Frubik%2Fradon) [V]. xenon: https://github.com/rubik/xenon [NV]. Ambos têm releases pouco frequentes (radon 6.0.1 de 2023 [NV]). São estáveis, mas com manutenção lenta.
- **wily** (Anthony Shaw) itera o histórico git e indexa a complexidade de arquivos Python com vários algoritmos (usa radon). Os resultados vão para console ou gráficos. Releases: 1.24.0 (out/2022), 1.24.2 (jul/2023), 1.25.0 (out/2023). Há pré-release 2.0.0a1 listada no piwheels com data de 26/abr/2026. Nenhum release encontrado em 2024–2025, então a manutenção é irregular. — [piwheels wily](https://www.piwheels.org/project/wily) [V]; [docs wily](https://wily.readthedocs.io/) [V]
- Ferramentas não verificadas nesta sessão (todas amplamente mantidas até onde sei):
  - ruff: https://github.com/astral-sh/ruff [NV]. Saída: `ruff check --output-format=json` [NV].
  - mypy: https://github.com/python/mypy [NV]. Saída: `--junit-xml` ou parse de texto. O mypy tem `--linecount-report`/`--txt-report` [NV].
  - pyright: https://github.com/microsoft/pyright [NV]. Saída: `pyright --outputjson` [NV].
  - bandit: https://github.com/PyCQA/bandit [NV]. Saída: `bandit -r src -f json` [NV].
  - semgrep: https://github.com/semgrep/semgrep [NV]. Saída: `semgrep --config auto --json` [NV]. Licença das regras mudou em 2024 e há o fork **opengrep** [NV].
  - vulture: https://github.com/jendrikseipp/vulture [NV]. Saída em texto, parse por regex ou `--make-whitelist` [NV].
  - jscpd: https://github.com/kucherenko/jscpd [NV]. Exige Node. Saída: `--reporters json` [NV].
  - pylint: `pylint --disable=all --enable=duplicate-code --output-format=json` [NV].
- Estudo DiD da CMU (MSR '26) sobre o Cursor: a adoção trouxe aumento grande, mas **transitório**, de velocidade, e aumento **substancial e persistente** de warnings de análise estática e de complexidade de código. Os aumentos de warnings e complexidade são fatores importantes da desaceleração de longo prazo (estimação em painel por GMM). — [arXiv 2511.04427, He, Miller, Agarwal, Kästner, Vasilescu](https://arxiv.org/abs/2511.04427) [V]

### Inferences
- Essas são exatamente as métricas que a literatura recente associa à degradação causada por IA (warnings estáticos, complexidade, duplicação, menos "moved"). Por isso merecem lugar no painel principal.
- **Coleta por snapshot**: `radon cc -j -s src/` gera `{arquivo: [{name, type, complexity, rank, lineno}]}`, que vira tabela com `pd.json_normalize` e uma coluna `file`. `radon mi -j src/` dá o MI por arquivo. `radon hal -j`. Tabela longa sugerida: `metrics_snapshot(commit, date, tool, file, symbol, metric, value)` salva em Parquet.
- **Histórico por commit**: em vez de depender do wily, rode um script próprio que faz `git worktree add /tmp/wt <sha>` para cada commit (ou a cada N commits ou por semana) e executa radon, ruff e bandit, no mesmo formato longo. É mais robusto e reprodutível.
- Em código de engenharia com numpy, configurar as regras `NPY` do ruff (deprecations do numpy) e `PD` (pandas-vet) é útil [NV].

### Gaps
- Datas exatas dos últimos releases de ruff, mypy, pyright, bandit, vulture e jscpd em 2026 não verificadas.
- Não confirmei se o wily 2.0 virou release estável.

## 3. Qualidade de testes: coverage.py, pytest, mutation testing (mutmut, cosmic-ray), hypothesis, golden/snapshot (numpy.testing, pytest.approx, syrupy)

### Takeaway
Cobertura de linhas e branches (coverage.py) mede o que foi **executado**, não o que foi **verificado**. Testes escritos por IA tendem a executar código sem asserts fortes, e o mutation score (mutmut) expõe isso. Para cálculos de engenharia, combine testes de referência (valores de norma ou exemplos resolvidos de livro com `numpy.testing.assert_allclose` e tolerâncias explícitas), testes de propriedade (hypothesis: monotonicidade, unidades, invariantes físicos) e snapshots (syrupy) para saídas tabulares completas.

### Cited Findings
- **mutmut 3.x**: foco em facilidade de uso, lembra o trabalho já feito (incremental) e roda em paralelo. Exige sistema com `fork`: no Windows, só via WSL. O mutmut 3 só muta código **dentro de funções**. Para mutar código fora de funções, a orientação é usar o mutmut 2. Versões vistas: 3.0.x a 3.3.1. A 3.3.1 pode exigir toolchain Rust para build em algumas plataformas (x86_64-darwin). — [PyPI mutmut](https://pypi.org/project/mutmut/?featured_on=pythonbytes) [V]; [PyPI mutmut 3.3.1](https://pypi.org/project/mutmut/3.3.1/) [V]
- **cosmic-ray**: https://github.com/sixty-north/cosmic-ray [NV]. Mais configurável, com sessão em SQLite e execução distribuída [NV]. Status de 2026 não verificado.
- coverage.py: https://github.com/nedbat/coveragepy [NV]. `coverage json` gera `files.<f>.summary.percent_covered`, com branches via `--branch` [NV].
- hypothesis: https://github.com/HypothesisWorks/hypothesis [NV]. Tem estratégias `hypothesis.extra.numpy` e `hypothesis.extra.pandas` [NV].
- syrupy: https://github.com/syrupy-project/syrupy [NV]. Snapshots com `assert x == snapshot`. Existe extensão JSON ou amostra própria para DataFrames [NV].
- numpy.testing (`assert_allclose(rtol, atol)`) e `pytest.approx`: https://numpy.org/doc/stable/reference/routines.testing.html [NV]; https://docs.pytest.org/en/stable/reference/reference.html#pytest-approx [NV].

### Inferences
- Métricas por PR: `line_cov`, `branch_cov`, `mutation_score = killed/(killed+survived)` (excluindo timeouts e suspeitos), `n_tests`, `n_asserts` (contados por AST), `assert_density = asserts/test`. A razão `mutation_score / line_cov` serve de indicador de "testes ocos".
- O mutmut é caro. Em CI, rode só nos arquivos alterados do PR ou em job noturno. Os resultados do mutmut 3 ficam em `mutants/` e são consultados com `mutmut results` [NV, conferir formato de exportação].
- Golden tests de engenharia: guarde casos de referência (entrada, saída esperada, fonte normativa e tolerância) em CSV ou Parquet versionado. Um único `pytest.mark.parametrize` lê esse arquivo. Isso mede "regressão numérica" de forma explícita quando a IA refatora.

### Gaps
- Não verifiquei o status do cosmic-ray em 2026 nem o formato de saída JSON do mutmut 3.
- Não achei estudo primário que quantifique o mutation score de testes gerados por IA frente a testes humanos. Isso fica como lacuna, não como fato.

## 4. Determinismo e reprodutibilidade: lockfiles (uv/pip-tools), hash de entradas, sementes, DVC, MLflow, registros JSON/Parquet

### Takeaway
Para apps de cálculo de engenharia, o essencial é: dependências travadas (uv.lock), versão exata do código (SHA), hash das entradas e saídas, e semente fixa onde houver aleatoriedade. Cada execução vira um "run record" em JSON ou Parquet. DVC e MLflow são opcionais e só se justificam com datasets grandes ou muitos experimentos.

### Cited Findings
- uv: https://github.com/astral-sh/uv [NV]. `uv lock` gera `uv.lock` multiplataforma e `uv sync --locked` falha se o lock estiver desatualizado [NV].
- pip-tools: https://github.com/jazzband/pip-tools [NV]. `pip-compile --generate-hashes` [NV].
- DVC: https://github.com/iterative/dvc [NV]. Versiona dados e pipelines (`dvc.yaml`, `dvc.lock` com md5 de deps e outs) [NV]. A Iterative foi adquirida pela lakeFS em 2025 [NV, conferir], e a continuidade do DVC deve ser verificada.
- MLflow: https://github.com/mlflow/mlflow [NV]. Tracking de runs com params, metrics e artifacts. `mlflow.search_runs()` já retorna `pandas.DataFrame` [NV].
- numpy: `np.random.default_rng(seed)` é a API recomendada de sementes [NV]. https://numpy.org/doc/stable/reference/random/generator.html

### Inferences
- Esquema de run record proposto (uma linha por execução, em Parquet): `run_id, timestamp, git_sha, git_dirty, uv_lock_sha256, python_version, input_sha256, params_json, seed, output_sha256, duration_s, ai_assisted(bool)`.
- Métrica de determinismo: rodar a suíte golden 2 vezes (ou em 2 SOs na matriz do CI) e comparar `output_sha256` ou `assert_allclose`. A taxa de divergência deve ser 0.
- Lockfile drift como métrica: número de dependências alteradas por PR (`git diff uv.lock`), útil porque agentes de IA costumam adicionar dependências.

### Gaps
- Não verifiquei nesta sessão o status corporativo e de manutenção do DVC em 2026.

## 5. CI: GitHub Actions por PR, artefatos, pre-commit, trailers de commit para marcar IA (Co-Authored-By) e como consultá-los

### Takeaway
A marcação de IA tem três níveis de precisão: (1) trailers de commit (`Co-authored-by: Claude ...`, inseridos por padrão pelo Claude Code; granularidade de commit, depende de disciplina); (2) **git-ai**, extensão open source em que os agentes registram as linhas exatas que escreveram, guardadas em git notes (granularidade de linha); (3) heurísticas de detecção, não recomendadas. Para um repositório pessoal, trailers e git-ai cobrem bem o problema.

### Cited Findings
- **Trailers**: o Claude Code adiciona o trailer `Co-authored-by` aos commits, e sessões na nuvem adicionam um link claude.ai. Consultas:
  - `git log --format='%h %(trailers:key=Co-authored-by,valueonly)'`
  - fallback com `git log -i --grep='^Co-authored-by:' --format='%h %an %s'`. O `-i` importa porque as ferramentas variam a capitalização.
  - `git log -1 --format=%B | git interpret-trailers --parse` para inspecionar um commit.
  - `git shortlog` e `--author` **não** enxergam coautores.
  — [SSD Nodes: Claude Code commit attribution](https://www.ssdnodes.com/learn/claude-code-commit-attribution) [V]
- Trailers customizados: há proposta de trailer de sessão (ex.: `Crow-Session:`). O crate Rust `whogitit` usa `AI-Session`, `AI-Model` e `AI-Lines` junto com `Co-Authored-By`. — [radiusmethod/crow issue #246](https://github.com/radiusmethod/crow/issues/246) [V]; [whogitit trailers.rs](https://docs.rs/crate/whogitit/latest/source/src/storage/trailers.rs) [V]
- **git-ai** (git-ai-project/git-ai, Apache 2.0, Rust, cerca de 2,9k stars, mais de 5,5k commits):
  - Os agentes chamam `git-ai checkpoint` ao escrever código, e a atribuição por linha (agente, modelo, prompts) é guardada em Git Notes no commit. Ela é preservada em rebase, squash, merge, reset, stash e cherry-pick.
  - **Não usa heurística**: só registra o que os agentes reportam.
  - Comandos: `git ai blame <file>`, `git ai stats --json`, `git ai stats <a>..<b> --json` (percentual de código de IA, linhas geradas vs. commitadas, taxa de aceitação, por ferramenta e modelo), `git log --show-notes="ai"`.
  - Agentes suportados incluem Claude Code, Codex, Cursor, GitHub Copilot, OpenCode, Windsurf, Gemini, Continue, Junie, entre outros.
  - Limitações: `git mv`, filter-branch/filter-repo e `git replace` não são rastreados. Squash-merge e rebase-merge no GitHub exigem a oferta paga Teams ou as CI Actions open source.
  — [GitHub git-ai-project/git-ai](https://github.com/git-ai-project/git-ai) [V]
- GitHub Actions: `actions/upload-artifact` para guardar JSON/Parquet por PR [NV, https://github.com/actions/upload-artifact]. pre-commit: https://github.com/pre-commit/pre-commit [NV]. Hook `commit-msg` pode exigir trailer `AI-Assisted: yes|no` [inferência].

### Inferences
- **Esquema de marcação recomendado**: o trailer padrão do agente (`Co-authored-by`) mais um trailer explícito `AI-Assisted: none|partial|full` e, opcionalmente, `AI-Tool:`, validados por hook `commit-msg` do pre-commit. Para carregar no pandas: `git log --format='%H%x1f%aI%x1f%(trailers:key=AI-Assisted,valueonly,separator=%x2C)%x1f%(trailers:key=Co-authored-by,valueonly,separator=%x2C)%x1e'`, depois `split` por `\x1e`/`\x1f` e `pd.DataFrame`. Ou via PyDriller: `commit.msg` e parse com regex `^([A-Za-z-]+):\s*(.+)$` nas últimas linhas.
- **Workflow por PR**: o job `metrics` roda em `pull_request` com `fetch-depth: 0`. Ele executa ruff, radon, bandit, vulture, coverage, mutmut (só arquivos alterados), git mining da faixa `base..head` e `git ai stats base..head --json`. Depois escreve `metrics/pr-<n>.parquet`, publica com upload-artifact e comenta um resumo no PR (gh CLI). Em `push` na main, faz append em um branch `metrics-data` ou em release assets para formar a série temporal.
- Atenção: squash-merge no GitHub reescreve commits. Os trailers dos commits individuais podem se perder se não forem copiados para a mensagem do squash. Prefira merge commit ou configure a mensagem de squash para incluir os trailers.

### Gaps
- Formato exato do trailer usado pelo GitHub Copilot coding agent não verificado.
- Ref exata das notes do git-ai (algo como `refs/notes/ai`) não confirmada na página do repositório.

## 6. Dashboards: Streamlit/Dash/Plotly e dashboards open source de métricas de IA

### Takeaway
Para quem já domina plotly e pandas, um app Streamlit (ou Dash) lendo os Parquets de métricas é o caminho natural. Não encontrei dashboard open source consolidado e específico de "métricas de código com IA". As opções existentes são o stats do git-ai (com o painel agregado em tier pago) e produtos comerciais (GitClear, Larridin, Minware).

### Cited Findings
- O "Stats Bot" e a agregação entre PRs, repositórios e organização do git-ai ficam em tier pago ou early-access, fora do core open source. — [resumo de busca sobre git-ai](https://www.sourcepulse.org/projects/22455837) [V, fonte secundária]
- Streamlit: https://github.com/streamlit/streamlit [NV]. Dash: https://github.com/plotly/dash [NV]. Plotly: https://github.com/plotly/plotly.py [NV].
- Datasets de referência para benchmark: **AIDev** tem 932.791 PRs agênticos (Codex, Devin, Copilot, Cursor, Claude Code) em 116.211 repositórios, com corte em 01/ago/2025, e um subconjunto curado de 33.596 PRs de 2.807 repositórios com mais de 100 stars (comentários, reviews, commits). Disponível em Hugging Face e Zenodo. — [arXiv 2602.09185 AIDev](https://arxiv.org/abs/2602.09185?context=cs) [V]

### Inferences
- Páginas sugeridas: (1) visão temporal (CC média e p90, MI, warnings ruff/bandit, cobertura, mutation score), com linha vertical na data de início do uso de IA; (2) churn e retrabalho por semana, separando commits IA e não IA; (3) tabela por PR; (4) reprodutibilidade (taxa de golden tests passando, drift de lockfile).
- O app pode ser publicado no próprio repositório, com GitHub Pages servindo HTML estático do plotly (`fig.write_html`) e dispensando servidor.

### Gaps
- Não achei, com o orçamento disponível, um dashboard open source mantido focado em métricas de IA além do git-ai. Recomenda-se uma busca adicional (ex.: "AI code metrics dashboard github").

## 7. Brownfield: baseline antes da IA, testes de caracterização, antes/depois, séries temporais interrompidas e diferenças-em-diferenças

### Takeaway
Em repositório existente, a metodologia é: (1) congelar uma **baseline** retroativa minerando o histórico (série semanal de métricas recalculada por snapshot com worktree); (2) escrever **testes de caracterização** (golden master) que capturam o comportamento atual antes de deixar a IA alterar código; (3) marcar o ponto de intervenção (data, tag ou trailer) e analisar com **série temporal interrompida (ITS)** e, havendo módulos ou repositórios sem IA como controle, **diferenças-em-diferenças (DiD)**. É o mesmo desenho usado nos estudos MSR recentes sobre Cursor e agentes.

### Cited Findings
- O estudo DiD sobre o Cursor (CMU, MSR '26) comparou projetos adotantes com controle pareado. A adoção foi identificada pelo primeiro commit de arquivos de configuração do Cursor: 806 repositórios adotantes (a maioria entre ago/2024 e mar/2025) e 1.380 de controle. O pico de linhas adicionadas no 1º mês desaparece após cerca de 2 meses. — [arXiv 2511.04427v2](https://arxiv.org/html/2511.04427v2) [V]; [arXiv abs](https://arxiv.org/abs/2511.04427) [V]
- Limitação apontada: o grupo de controle pode conter código de outros assistentes de IA, e a amostra é só open source. — [Rob Bowley, resumo](https://blog.robbowley.net/2025/12/04/ai-is-still-making-code-worse-a-new-cmu-study-confirms) [V, via agregador]
- Estudo ITS sobre agentes de código (arXiv 2607.05677): modelos ITS repositório-mês com efeitos fixos de repositório e erros-padrão clusterizados. Mostra um burst curto pós-adoção seguido de **queda significativa de commits**, sem aumento robusto de atividade ligada a defeitos, mas com **aumento substancial do tempo de resolução de issues**. — [arXiv 2607.05677](https://arxiv.org/pdf/2607.05677) [V, via snippet de busca; não li o PDF completo]
- Testes de caracterização: conceito de Michael Feathers (*Working Effectively with Legacy Code*) [NV]. Em Python, approvaltests (https://github.com/approvals/ApprovalTests.Python) [NV] e syrupy atendem.

### Inferences
- **Baseline retroativa**: para cada semana dos últimos 12–24 meses, faça checkout do último commit da semana (`git worktree`) e rode radon, ruff, bandit e vulture (e coverage, se a suíte rodar em código antigo). Isso gera `baseline.parquet` com o mesmo esquema longo da seção 2. Métricas puramente de git (churn, retrabalho, frequência) saem do PyDriller sem checkout.
- **Ponto de intervenção**: tag git `ai-start` ou a primeira ocorrência de trailer de IA (análogo ao "primeiro arquivo .cursor" do estudo da CMU).
- **ITS em Python**: `statsmodels.formula.api.ols('y ~ t + post + t_post', data=weekly)` (segmented regression) com erros HAC (`cov_type='HAC'`) por causa da autocorrelação [NV docs statsmodels]. **DiD intra-repositório**: tratamento = arquivos ou módulos tocados majoritariamente por IA (via git-ai ou trailers) e controle = módulos não tocados, com `y ~ treated*post + C(module) + C(week)` e erros clusterizados por módulo. Ressalva: a atribuição não é aleatória, pois a IA é usada nos módulos onde o desenvolvedor escolhe usá-la (viés de seleção).
- Diferença greenfield vs. brownfield: no greenfield não há "antes". As comparações possíveis são entre commits ou PRs com e sem IA no mesmo projeto (dentro do repositório) e contra benchmarks externos (AIDev, números da GitClear). No brownfield, a baseline histórica é o contrafactual principal.
- Com um único desenvolvedor e um repositório, o poder estatístico é baixo. Apresente efeitos com intervalos e evite afirmações causais fortes.

### Gaps
- Não li o PDF completo do arXiv 2607.05677 (autores, amostra exata).
- Não encontrei guia primário específico de "baseline antes de IA" em brownfield. A recomendação acima é inferência a partir dos desenhos de estudo MSR.

---

### Stack recomendada (resumo para o redator; tudo [V]/[NV] conforme seções acima)
| Camada | Ferramenta | Comando ou saída | Para pandas |
|---|---|---|---|
| Mineração git | PyDriller 2.7 (+ GitPython) | API Python | `pd.DataFrame(records)` → Parquet |
| Churn/retrabalho | script próprio (diff + `git blame -M -C`), N=14 dias | — | tabela linha a linha |
| Atribuição IA | trailers + git-ai | `git log --format=%(trailers...)`, `git ai stats --json` | `pd.read_json` / `json_normalize` |
| Complexidade/MI | radon (+ xenon como gate) | `radon cc -j`, `radon mi -j` | `json_normalize` |
| Lint/tipos | ruff, mypy ou pyright | `--output-format=json`, `--outputjson` | `pd.read_json` |
| Segurança | bandit (+ semgrep/opengrep opcional) | `-f json`, `--json` | `json_normalize(results)` |
| Código morto/duplicação | vulture, jscpd ou pylint duplicate-code | texto ou JSON | regex / `json_normalize` |
| Histórico de complexidade | wily (manutenção irregular) ou script com worktree | — | Parquet |
| Testes | pytest + coverage.py, mutmut 3, hypothesis, syrupy, numpy.testing | `coverage json`, `mutmut results` | `json_normalize` |
| Reprodutibilidade | uv.lock, hashes sha256, run records; DVC/MLflow opcionais | — | Parquet / `mlflow.search_runs()` |
| CI | GitHub Actions + upload-artifact + pre-commit (commit-msg) | artefatos Parquet por PR | concat |
| Análise | statsmodels (ITS/DiD) | — | — |
| Dashboard | Streamlit ou Dash + plotly | — | — |
