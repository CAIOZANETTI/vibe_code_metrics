> **Comece por aqui:** [guia rápido para usar o vcm num protótipo](docs/guia.md).
> **Documentação viva:** [arquitetura de funcionamento](docs/arquitetura.md) · [plano de implementação](docs/plano.md) · versão HTML em [`docs/index.html`](docs/index.html) (gerada com `uv run vcm docs`).
> Pesquisa de referência: [reports/Métricas de desenvolvimento com IA.md](reports/Métricas%20de%20desenvolvimento%20com%20IA.md).

# Vibe Code Metrics — Método de Desenvolvimento Experimental com IA

Documento metodológico | v0.1 | 31/10/2026

Status: proposta a ser validada; não é ainda um framework implementado.

## 1. Propósito

Criar um repositório independente e reutilizável que transforme desenvolvimento assistido por IA (vibe coding) em um processo disciplinado: uma ideia vira hipótese falsificável, é dividida em experimentos pequenos, executada em rodadas controladas e julgada por métricas e evidências. O primeiro caso será o Projeto em Camadas — Memória Espacial, mas o método deve funcionar em outros projetos.

> **Princípio:** A IA propõe, o código executa, os testes verificam e as evidências sustentam as decisões. Não adotar ferramentas por gosto, marca ou demonstração isolada.

## 2. Separação de responsabilidades

| Repositório | Responsabilidade |
|---|---|
| vibe-code-metrics | Teses, protocolos, agentes, métricas, testes, governança, relatórios e decisões |
| projeto-em-camadas | Código e dados do protótipo geoespacial, integração, execução e resultados de engenharia |

O repositório metodológico não deve se tornar um monólito que implemente o produto. Cada projeto pode fornecer adaptadores, datasets, gabaritos e métricas específicas.

## 3. Ciclo de uma tese

1. **Problema:** enunciar uma necessidade mensurável e o cenário de uso.
2. **Hipótese:** escrever afirmação falsificável, alternativas e condições de validade.
3. **Critérios:** fixar restrições eliminatórias, métricas, tolerâncias e orçamento antes dos resultados.
4. **Decomposição:** quebrar em tarefas menores com entradas/saídas padronizadas.
5. **Rodadas:** executar alternativas sobre os mesmos casos; repetir testes e preservar falhas.
6. **Análise:** comparar qualidade, custo, tokens, latência, recursos, variância e riscos.
7. **Decisão:** aprovar, rejeitar ou declarar inconclusiva; registrar evidências e versão.
8. **Regressão:** repetir benchmarks quando modelos, dependências ou requisitos mudarem.

## 4. Agentes e roteamento

Testar modelos de diferentes capacidades (por exemplo, classes rápidas/econômicas, intermediárias, avançadas e locais). Não presumir disponibilidade ou desempenho de um nome específico. Um agente pode atuar como planejador, extrator, programador, revisor ou auditor; o mesmo modelo pode assumir vários papéis, e a separação entre agentes não garante independência.

O roteador deve registrar: task_id, tipo de tarefa, complexidade estimada, agente/modelo, versão, prompt, contexto enviado, tokens de entrada/saída/cache, número de chamadas, duração, custo, tentativas, taxa de aprovação e intervenções humanas.

Política experimental: começar pelo método de menor custo esperado que cumpra os critérios; escalar para modelo mais capaz quando o teste, a incerteza ou a criticidade exigir. Comparar custo por resultado validado, não apenas preço por milhão de tokens.

## 5. Determinismo — definição operacional

Meta inicial proposta: ≥80% das operações relevantes executadas por procedimentos determinísticos e verificáveis, ponderadas por criticidade, e 100% dos cálculos finais de engenharia realizados por código determinístico. Essa meta precisa ser testada e ajustada; não é uma garantia de qualidade.

Não medir por número de linhas Python. Distinguir:

- **Determinismo de execução:** mesmas entradas, parâmetros e versões produzem mesmo resultado calculado.
- **Cobertura determinística:** fração das operações críticas cobertas por código com testes e regras explícitas.
- **Dependência probabilística:** decisões baseadas em interpretação de IA, que requerem validação ou marcação de incerteza.
- **Correção:** mesmo um cálculo 100% reproduzível pode estar errado se a IA extraiu cotas erradas. Medir qualidade dos dados e do cálculo separadamente.

Para tornar o indicador auditável, atribuir pesos de criticidade a operações definidas no protocolo e calcular: `cobertura = soma(pesos das operações determinísticas verificadas) / soma(pesos de todas as operações elegíveis)`. Reportar também cobertura por classe crítica, sem esconder falhas em médias.

## 6. Métricas obrigatórias

| Dimensão | Indicadores |
|---|---|
| Qualidade | Precisão, recall, F1, erros críticos, validação de schema, retrabalho |
| IA e tokens | Tokens de entrada/saída/cache, chamadas, tentativas, tokens por tarefa aprovada |
| Tempo | Latência total e por etapa, p50/p95, throughput, tempo de revisão humana |
| Custo | API, computação local estimada, armazenamento, retrabalho, custo por resultado aprovado |
| Determinismo | Cobertura ponderada, reprodutibilidade, operações críticas verificadas |
| Infraestrutura | Pico de RAM, CPU/GPU, disco, I/O, escalabilidade, falhas e timeouts |
| Persistência | Tamanho por objeto, velocidade de gravação/consulta, consistência, atualização parcial |
| Governança | Proveniência, versionamento, gabarito, repetibilidade, aprovação de decisão |

Indicadores úteis:

- `tokens_por_aprovacao = tokens_totais / tarefas_aprovadas`;
- `custo_por_aprovacao = (custo_IA + custo_compute + custo_retrabalho) / tarefas_aprovadas`;
- `taxa_de_retrabalho = tarefas_reexecutadas / tarefas_totais`;
- `erro_relativo = abs(resultado - referencia) / abs(referencia)` quando referência ≠ 0.

## 7. Critério de escolha

Primeiro, restrições eliminatórias: segurança, qualidade mínima, precisão, rastreabilidade, integridade. Depois, fronteira de Pareto entre custo, tokens, latência, RAM e manutenção. Uma alternativa mais barata que falha em uma cota crítica não pode vencer. Não reduzir todos os resultados a uma nota única sem mostrar métricas e pesos.

Registrar limites, ambiente, versões, número de repetições e intervalos de confiança quando cabível. Para comparação justa, rodar métodos sobre os mesmos dados; distinguir inferência local de API hospedada e custo de API de custo real total.

## 8. Infraestrutura e armazenamento

O método deve avaliar arquitetura e não apenas prompts: Python, bibliotecas, formatos (JSON, Parquet, bancos SQL/espaciais), indexação, particionamento, cache, persistência, processamento incremental, consultas e concorrência. Testar em hardware identificado, inclusive limites de RAM e armazenamento. Evitar fixar uma stack antes de medir.

## 9. Estrutura proposta

```text
vibe-code-metrics/
  README.md
  docs/
    metodo.md
    criterios-decisao.md
    metricas.md
    agentes.md
  theses/
    T001-extracao-pranchas/
      hypothesis.md
      protocol.yaml
      experiments/
      decision.md
    T002-armazenamento-espacial/
  adapters/
    llm/
    storage/
    benchmark/
  src/
    runners/
    metrics/
    telemetry/
    validation/
  datasets/
    manifests/
    ground_truth/
  results/
    runs/
    reports/
  tests/
  pyproject.toml
```

## 10. Registro mínimo de cada execução

```yaml
run_id: "exemplo-001"
thesis_id: "T001"
project: "projeto-em-camadas"
input_hash: "sha256-a-preencher"
method: "hybrid-parser"
model: "modelo-e-versao-a-preencher"
prompt_version: "v1"
hardware: "ambiente-a-preencher"
metrics:
  input_tokens: null
  output_tokens: null
  cached_tokens: null
  latency_seconds: null
  peak_ram_mb: null
  cost_usd: null
  accuracy: null
  critical_errors: null
status: "not_run"
```

## 11. Referências metodológicas

- **Promptfoo:** avaliações automatizadas de modelos, prompts e aplicações LLM, integração em pipelines.
- **DeepEval:** avaliações de aplicações LLM e métricas em Python; verificar adequação e versões no início da implementação.
- **Airspeed Velocity (ASV):** histórico de benchmarks de desempenho por revisão de código; avaliar para regressões.
- **Document Parser Benchmark:** compara parsers, qualidade, tempo, falhas e preserva limitações metodológicas.
- **PDF Parser Benchmark:** entradas congeladas, métricas por componente, latência, custo e rastreabilidade de artefatos.

> **Cuidado:** são referências e possíveis componentes, não soluções completas nem escolhas aprovadas.

## 12. Primeiro programa experimental

- **T001 — Extração de pranchas:** comparar extração vetorial, OCR, visão e híbrida, com a mesma amostra de desenhos da adutora de 5 km; medir cotas, elementos, coordenadas, tokens, tempo e custo.
- **T002 — Armazenamento espacial:** comparar persistência e índices usando a mesma geometria normalizada; medir RAM, bytes por elemento, consultas, atualizações e exatidão.
- **T003 — Roteamento de agentes:** comparar modelos e distribuição de tarefas com orçamentos de tokens controlados.
- **T004 — Determinismo:** medir cobertura de regras e cálculos Python, dependência de IA, regressão e propagação de erros de extração.

Entregável do primeiro ciclo: relatório de decisões sustentado por experimentos reproduzíveis, não um produto completo.
