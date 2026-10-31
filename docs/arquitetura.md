# Arquitetura de funcionamento

> **Vibe Code Metrics** é um laboratório de decisões técnicas para desenvolvimento assistido por IA.
> A IA propõe, o código executa, os testes verificam, as métricas comparam e o humano decide.
> O próprio repositório é desenvolvido com o seu método (tese **T000**).

Versão 0.2 · 31/10/2026 · Status: protótipo em construção. Plano de execução: [plano.md](plano.md).

## 1. Ideia em uma página

O repositório não escolhe ferramentas por gosto. Ele mantém um **repertório** de alternativas
(NumPy, Polars, Parquet, NetworkX, JSON-LD, Haiku, Sonnet, Opus, Fable, Codex, modelos locais…),
testa essas alternativas em **teses** com gabarito próprio e usa as evidências para **recomendar**
o que usar em cada perfil de problema. Cada iteração de código termina com uma **retrospectiva
medida**: ficou mais eficiente, mais determinístico, mais enxuto, mais robusto? Perdeu algo?
Vale continuar?

```mermaid
flowchart TB
    subgraph Conhecimento
        R["Repertório<br/>alternativas por papel"]
        T["Teses<br/>hipótese + protocolo + gabarito"]
        E["Evidências<br/>runs em Parquet"]
        S["Recomendador<br/>perfil → alternativa"]
    end
    subgraph Motor["Motor PDCA"]
        P["Plan<br/>humano + gerente"]
        D["Do<br/>agentes executores"]
        C["Check<br/>avaliador Python trancado"]
        A["Act<br/>manter · reverter · decidir"]
    end
    subgraph Saida["Saída"]
        H["Relatórios HTML<br/>tese · iteração · histórico"]
    end
    R --> T --> P --> D --> C --> A
    C --> E --> S --> R
    A --> H
    E --> H
    A -->|"estagnou? sugerir alternativa"| R
```

## 2. Componentes

| Componente | O que é | Formato | Pasta |
|---|---|---|---|
| **Repertório** | Alternativas classificadas por **papel** (extração, cálculo, armazenamento, intercâmbio, apresentação, orquestração de IA). Só se compara o que cumpre o mesmo papel. | YAML | `repertorio/` |
| **Catálogo de modelos** | Modelos de IA disponíveis, preço, data de verificação e papéis sugeridos. Atualizado quando um fornecedor lança modelo novo, o que dispara regressão. | YAML | `repertorio/modelos.yaml` |
| **Tese** | Hipótese falsificável + protocolo (métricas, tolerâncias, orçamento, repetições) + gabarito congelado + decisão. | Markdown + YAML | `theses/Txxx-*/` |
| **Runner** | Executa alternativas sobre os mesmos casos, com repetições, isolamento em subprocesso, pico de RAM, hash de saída. | Python | `src/vcm/runners/` |
| **Coletores** | Medição passiva: telemetria do agente, git, análise estática, testes. | Python → Parquet | `src/vcm/coletores/` |
| **Avaliador** | Compara a saída com o gabarito por tolerância declarada. É código determinístico e os agentes não podem alterá-lo. | Python | `theses/*/avaliador.py` |
| **Balanço** | Retrospectiva de iteração: antes × depois, veredito por métrica e decisão proposta. | Python | `src/vcm/balanco.py` |
| **Recomendador** | Consulta as evidências por perfil de problema. | Python | `src/vcm/recomendador.py` |
| **Relatórios** | HTML autocontido com Plotly, um por tese, um por iteração e um painel histórico. | HTML | `results/reports/` |
| **Documentação** | Este Markdown é a fonte. `vcm docs` gera `docs/index.html`, e o CI garante que o HTML está em dia. | MD → HTML | `docs/` |

## 3. O ciclo PDCA de uma iteração

Uma **iteração** é um commit ou um PR. Ela pode ser feita por um humano, por um agente ou por
vários agentes coordenados por um gerente.

```mermaid
sequenceDiagram
    actor H as Humano
    participant G as Gerente (Fable/Opus)
    participant W as Executores (Haiku/Sonnet/Opus/Codex)
    participant C as Avaliador + coletores (Python)
    participant R as Histórico (Parquet) + HTML
    H->>G: tese, protocolo e orçamento (Plan)
    G->>W: tarefas pequenas, cada uma com modelo e orçamento
    W->>W: implementa em worktree isolada (Do)
    W->>C: entrega a alteração
    C->>C: confere o hash do avaliador e do gabarito
    C->>C: mede antes × depois (Check)
    C->>R: grava o run e o balanço
    C->>G: veredito por métrica + decisão proposta
    alt eliminatória piorou
        G->>W: reverter
    else melhorou sem perdas
        G->>R: manter (commit)
    else houve troca
        G->>H: decisão humana com a tabela de trocas
    end
    H->>R: aprova o que entra no repertório (Act)
```

### Quem faz o quê

| Etapa | Responsável | Regra que não se negocia |
|---|---|---|
| **Plan** | Humano + gerente | Protocolo, métricas, tolerâncias e gabarito commitados **antes** de rodar |
| **Do** | Executores | Cada um trabalha numa worktree isolada, com orçamento de tokens e de tempo |
| **Check** | **Código Python**, nunca uma IA | Avaliador e gabarito com hash conferido. Alteração detectada invalida o run. |
| **Act** | Regra automática + humano | Reverter e manter podem ser automáticos. Trocas e entradas no repertório exigem aprovação humana. |

## 4. Retrospectiva de iteração

Ao fim de cada iteração, o repositório faz as provocações abaixo. Primeiro responde com números,
depois a IA interpreta e, por fim, o humano decide.

| Pergunta | Métricas (antes × depois) | Coleta |
|---|---|---|
| Ficou **mais eficiente**? | tempo p50/p95, pico de RAM, custo da iteração | pytest-benchmark ou asv, psutil, telemetria |
| Ficou **mais determinístico**? | fração de execuções idênticas em N repetições, cobertura determinística ponderada | runner + numpy |
| Ficou **mais enxuto**? | SLOC, complexidade média, duplicação, nº de dependências | radon, ruff, `pyproject.toml` |
| Ficou **mais robusto**? | testes falhando, cobertura, mutation score, alertas de segurança | pytest, coverage, mutmut, bandit |
| **Perdeu** algo? | toda métrica que piorou além do ruído | `vcm.balanco` |
| Vale **continuar** nessa linha? | tendência das últimas k iterações e ganho ÷ custo | histórico em Parquet |

```mermaid
flowchart TD
    M["Medir antes × depois<br/>(variação além do ruído)"] --> E{"Alguma eliminatória piorou?<br/>testes · determinismo · segurança"}
    E -->|sim| REV["REVERTER"]
    E -->|não| P{"Alguma métrica piorou?"}
    P -->|sim| HUM["DECISÃO HUMANA<br/>troca registrada com justificativa"]
    P -->|não| G{"Alguma melhorou?"}
    G -->|sim| MAN["MANTER"]
    G -->|não| SG["SEM GANHO"]
    SG --> CV{"3 iterações seguidas sem ganho?"}
    CV -->|sim| PARE["PARAR esta linha<br/>consultar o repertório por alternativa"]
    CV -->|não| MAN2["seguir iterando"]
```

O **ruído** de cada métrica vem de repetições. O tempo de execução oscila alguns por cento,
enquanto SLOC não oscila nada. Uma variação dentro do ruído é declarada "igual", nunca
"melhorou". O critério de parada funciona como num método iterativo: quando o resíduo para de
cair, insistir só gasta tokens.

## 5. O que é medido passivamente e o que exige protocolo

| Passivo (basta instrumentar) | Exige protocolo de tese |
|---|---|
| Tokens, custo equivalente de API, latência por chamada (OpenTelemetry do Claude Code, logs de sessão) | Delimitação da tarefa e critério de "aprovada" |
| Edições aceitas e rejeitadas, tempo ativo, linhas, commits, PRs | Gabarito e tolerâncias por grandeza (cotas: tolerância **absoluta**) |
| Trailers `Co-Authored-By` (o que a IA escreveu) | Classificação das intervenções humanas |
| Testes, cobertura, complexidade e segurança no CI | Repetições, variância e intervalos de confiança |
| Histórico git: churn e retrabalho em 14 dias | Linha de base de sistema existente (testes de caracterização) |
|  | Pesos de criticidade do índice de determinismo |

Cada sessão de agente é marcada com `OTEL_RESOURCE_ATTRIBUTES="tese=T000,tarefa=..."`. É essa
marcação que liga a telemetria à tarefa e permite calcular **custo por tarefa aprovada**.
Em planos de assinatura, o custo medido é **equivalente de API**, não o gasto real. O relatório
precisa dizer isso.

## 6. Multiagente e catálogo de modelos

| Papel | Perfil de modelo (a validar na tese T003) | Por quê |
|---|---|---|
| Gerente / planejador | Mais capaz (Fable, Opus) | Decompor, priorizar, julgar trocas |
| Executor de tarefa bem especificada | Rápido e barato (Haiku) | Especificação clara e teste objetivo |
| Executor de tarefa com julgamento | Intermediário (Sonnet) | Bom equilíbrio entre custo e qualidade |
| Revisor | Outro modelo ou outro fornecedor (Codex) | Reduz erros correlacionados. Mesmo modelo não é revisão independente. |
| Dados confidenciais | Modelo local de pesos abertos | Desenho de cliente não sai da máquina |

Esta tabela é **hipótese**, não regra. A tese T003 mede custo por tarefa aprovada por papel e
modelo, e a tabela passa a ser derivada das evidências. Nenhum nome de modelo fica fixo no
código: tudo vem de `repertorio/modelos.yaml`.

## 7. Repertório: uma entrada

```yaml
# repertorio/calculo/numpy.yaml
id: numpy
papel: calculo
quando_considerar: [matriz densa, algebra linear, vetorizacao]
cuidados: [ordem de soma muda com threads do BLAS -> medir determinismo]
evidencias:
  - tese: T005-perda-de-carga
    perfil: {n_trechos: 5000, dtype: float64, operacao: cumsum}
    resultado: venceu
    metricas: {tempo_p50_ms: null, pico_ram_mb: null, deterministico: null}
    run: results/runs/T005/....parquet
status: em_teste   # em_teste | aprovado | rejeitado
```

Alternativas que não competem entre si não são comparadas. NumPy (cálculo matricial) e Polars
(tabelas) costumam **cooperar**: Polars filtra e junta, `.to_numpy()` calcula. NetworkX
(algoritmos em memória) e JSON-LD (intercâmbio semântico) estão em papéis diferentes.

## 8. Dados e formatos

| Dado | Formato | Por quê |
|---|---|---|
| Protocolos, repertório, catálogo de modelos | YAML | Legível, versionado em git, validado com schema |
| Runs, telemetria normalizada, histórico de iterações | Parquet | Colunar, tipado, lido direto por pandas e Polars |
| Telemetria bruta | JSON Lines | Como sai dos coletores, sem perda |
| Hash de entradas e saídas | SHA-256 sobre os **dados** (não sobre os bytes do arquivo) | Metadados do Parquet mudam sem os dados mudarem |
| Documentação e relatórios | Markdown → HTML | Markdown para editar e versionar, HTML para ler |

## 9. Estrutura do repositório

```text
vibe_code_metrics/
  README.md                 método (visão geral)
  CLAUDE.md                 regras para agentes que trabalham aqui
  docs/
    arquitetura.md          este documento (fonte)
    plano.md                plano de implementação (fonte)
    index.html              gerado por `vcm docs`
  repertorio/               alternativas por papel + modelos.yaml
  theses/
    T000-autodesenvolvimento/
    T001-extracao-pranchas/ ...
  src/vcm/
    balanco.py              retrospectiva de iteração
    docs.py                 Markdown -> HTML
    coletores/              git, código, testes, telemetria
    runners/                execução de teses
    relatorios/             HTML com Plotly
  results/
    iteracoes/              balanço de cada iteração (Parquet + HTML)
    runs/                   runs de teses
  tests/
  reports/, research_notes/ pesquisa de referência
```

## 10. Princípios invioláveis

1. **Cálculo final de engenharia é código determinístico**, com teste.
2. **Avaliador e gabarito são trancados**: hash conferido a cada run, e os agentes não têm permissão de escrita neles.
3. **Critérios são fixados antes dos resultados**, com commit do protocolo antes do run.
4. **Nada vira nota única**: as métricas aparecem lado a lado e as eliminatórias vêm primeiro.
5. **Toda variação é comparada com o ruído** medido em repetições.
6. **Orçamento por ciclo** (tokens, tempo e custo) com critério de parada.
7. **Entrada no repertório exige aprovação humana**, registrada em `decision.md`.
8. **Dados confidenciais** só vão para modelos autorizados pela política da tese.

## 11. O repositório como protótipo dele mesmo (T000)

O desenvolvimento do `vcm` é a primeira tese. Cada PR deste repositório passa pela retrospectiva
(seção 4), e o histórico mostra, ao longo do tempo:

- quanto custou cada funcionalidade e qual modelo a fez;
- se o código ficou mais enxuto, robusto e determinístico, ou se degradou;
- quando uma linha de trabalho convergiu e foi trocada.

Detalhes em [theses/T000-autodesenvolvimento](../theses/T000-autodesenvolvimento/hypothesis.md).

## 12. Como esta documentação se mantém atualizada

```mermaid
flowchart LR
    MD["docs/*.md<br/>(fonte)"] -->|"uv run vcm docs"| HTML["docs/index.html"]
    MD --> GH["GitHub renderiza o Markdown<br/>e os diagramas"]
    HTML --> CI{"CI: vcm docs --check"}
    CI -->|"desatualizado"| X["falha o build"]
    CI -->|"em dia"| OK["ok"]
```

A geração é **determinística**: sem data no arquivo, o mesmo Markdown sempre produz os mesmos
bytes. Assim o CI consegue detectar HTML desatualizado. A regra está em `CLAUDE.md`, para que
qualquer agente regenere o HTML ao editar a documentação.
