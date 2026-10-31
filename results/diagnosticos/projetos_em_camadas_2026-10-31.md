# Diagnóstico: projetos_em_camadas

> Linha de base do projeto antes de adotar o Vibe Code Metrics. **Só leitura**: nada foi alterado
> no repositório. Medido em 31/10/2026 no commit `5c2025c` (merge do PR #24), num contêiner Linux
> com 4 núcleos, Python 3.13.

## Resumo

O projeto está **saudável e bem acima da média**: 176 testes passando, régua de código própria
sem órfãs nem duplicatas, regras de domínio fora do código (`conceitos/*.json`) e um PDCA próprio
(índice IA × código, lições amarradas a testes, registro de agentes). Ele já pratica a maior parte
do método. O que falta é **reprodutibilidade de ambiente**, **cobertura nos módulos centrais** e
**complexidade concentrada em `prancha.py`**.

| Dimensão | Semáforo | Leitura |
|---|---|---|
| Robusto | 🔴 | 176 testes passam, mas 11 falham sem as dependências opcionais; cobertura de 58%; 3 alertas de segurança médios |
| Enxuto | 🟡 | complexidade média 6,85 (nota B); 3 funções nota E e 14 nota D; densidade boa (14,6 linhas por função) |
| Determinístico | 🟢 | cálculos de obras lineares reprodutíveis bit a bit (925 casos, 5 execuções, 1 hash) |
| Eficiente | ⚪ | ainda sem conjunto de referência no projeto (medido só no teste provisório: ~6 ms) |

Os limites do semáforo são os padrão do `vcm` (hipótese inicial) e podem ser calibrados para este
projeto no `vcm.yaml`.

## 1. Retrato medido

| Métrica | Valor | Como foi medido |
|---|---:|---|
| Commits na `main` | 100 em 5 dias (27 a 31/10) | `git log` |
| Commits com coautoria do Claude | 73 (68 Opus, 5 Sonnet) | trailers `Co-Authored-By` |
| Módulos em `camadas/` | 22 arquivos, 457 funções | radon |
| Linhas lógicas (SLOC) | 6.671 | radon |
| Linhas por função | 14,6 | radon |
| Complexidade média | 6,85 | radon cc (A 242 · B 117 · C 81 · D 14 · E 3) |
| Testes | 176 passam, 2 pulados | pytest, **com** pymupdf, rasterio e geopandas |
| Testes sem as opcionais | 128 passam, **11 falham**, 10 pulados | pytest só com `requirements.txt` |
| Cobertura de `camadas/` | 58,1% | coverage.py |
| Alertas de segurança (médio ou alto) | 3 | bandit |
| Reprodutibilidade (teste provisório) | 5 de 5 execuções idênticas | 925 casos de `obras_lineares` em processos separados |
| Régua própria (`afericao.py`) | ok: 0 órfãs, 0 duplicatas, 6 funções longas | script do projeto |
| Índice IA × código (`determinismo.py`) | 0,667 por etapas (meta 0,85) | script do projeto, última rodada |

### Cobertura por módulo (os mais baixos)

| Módulo | Cobertura | Papel |
|---|---:|---|
| `orcamento_sanepar.py` | 17% | orçamento Sanepar → escopo do contrato |
| `sfm.py` | 21% | 3D, ortofoto e MDS (depende de pycolmap) |
| `obra.py` | 32% | **pipeline completo** a partir do `obra.json` |
| `georef_prancha.py` | 34% | georreferenciamento de pranchas |
| `mosaico.py` | 41% | mosaico 2D georreferenciado |
| `diagnostico.py`, `drive.py`, `visualizador.py` | 49–50% | ferramentas de apoio |

Os mais altos: `extracao.py` 99%, `geo.py` 97%, `construtivos.py` 96%, `obras_lineares.py` 96%.

### Funções mais complexas

| Função | Complexidade | Arquivo |
|---|---:|---|
| `baloes` | 34 (E) | `prancha.py` |
| `ficha_hidraulica` | 33 (E) | `prancha.py` |
| `itens_da_tabela` | 33 (E) | `prancha.py` |
| `estacas_e_blocos` | 29 (D) | `prancha.py` |
| `extrair_custo_civil` | 25 (D) | `orcamento_sanepar.py` |

`prancha.py` concentra a complexidade (média 10,2 em 52 funções). O índice de manutenibilidade
(radon mi) dá nota C para `prancha.py`, `obra.py` e `escopo_obra.py`.

## 2. Pontos fortes (manter)

- **PDCA próprio e mais específico que o do `vcm`:**
  - régua de código que reprova piora;
  - índice IA × código por obra;
  - 15 lições, 13 delas com teste;
  - 14 execuções de agentes registradas.
- **Regras de domínio fora do código**, em `conceitos/*.json` com fonte. É o "Python calcula, regra editável" bem aplicado.
- **Seu estilo já está no código:** identificadores em português e unidade no nome (`prof_m`, `dn_mm`, `comp_m`, `largura`).
- **Escada de agentes por custo**, já definida em `docs/ARQUITETURA.md`: código → Haiku → Sonnet → Opus → Fable → você.
- **Cálculos de engenharia reprodutíveis:** largura de vala pelo MOS e quantificação de trecho deram o mesmo hash em 5 processos.

## 3. Achados, em ordem de prioridade

| # | Achado | Risco | Ação proposta | Agente |
|---|---|---|---|---|
| A | 11 testes falham quando `pymupdf` ou `rasterio` não estão instalados, embora sejam opcionais no `requirements.txt` | Falso vermelho em qualquer ambiente novo, inclusive no CI e no `vcm balanco` | `pytest.importorskip` nos testes que usam opcionais | Haiku |
| B | Sem `pyproject.toml` nem lockfile; versões só com `>=` | Ambiente não reproduzível: o mesmo commit pode dar resultado diferente meses depois | `pyproject.toml` com `uv`, extras `[pdf]`, `[sig]`, `[3d]` e `uv.lock`; `requirements.txt` mantido | Sonnet |
| C | Cobertura de 32% no `obra.py` (o pipeline) e de 17–41% em orçamento, georreferência e mosaico | Mudanças no pipeline passam sem teste | Testes de caracterização do pipeline com uma obra pequena congelada, antes de mexer | Sonnet |
| D | 3 funções nota E e 14 nota D, quase todas em `prancha.py` | Risco de regressão ao estender a leitura de pranchas | Não refatorar agora; usar o balanço para impedir que piorem e refatorar só quando a função for tocada | — |
| E | 3 alertas de segurança médios: SHA1 e MD5 sem `usedforsecurity=False` e `urlopen` sem validar o esquema | Baixo (hash usado como chave de cache), mas bloqueia o balanço | `usedforsecurity=False` e aceitar só `https:` no `drive.py` | Haiku |
| F | Medição interativa em JavaScript no visualizador (`medir`, `ll2utm`: distância, área, ângulo, UTM) | Tensão com a regra "HTML/JS só apresentam" | **Decisão sua** (abaixo) | — |
| G | Sem conjunto de referência bit a bit | O determinismo de resultado não é vigiado a cada iteração | `camadas/referencia.py` com obras lineares, escavação, valas e construtivos | Sonnet |
| H | O `.gitignore` não ignora `.venv/` nem `.claude/worktrees/` | Arquivos de ambiente e de agentes podem entrar em commit | Acrescentar | Haiku |

### Duas palavras para "determinismo"

No projeto, **determinismo** é o índice IA × código (quanto da obra sai do código). No `vcm`, é
**reprodutibilidade** (mesma entrada, mesmos bytes). As duas medidas se complementam. Sugestão:
chamar a do `vcm` de "reprodutibilidade" dentro deste projeto, para não confundir.

## 4. Decisões que dependem de você

1. **Medição interativa em JS (achado F).**
   - **(a)** Exceção documentada: "ferramentas interativas de medição no navegador", com teste de conferência. O `scripts/testar_visualizador.py` desenha um polígono conhecido e compara a área e o comprimento do JS com o Python (shapely e pyproj) dentro de uma tolerância absoluta. **Recomendado.**
   - **(b)** Manter a regra estrita: o JS só mostra, e cada medição volta ao Python. Inviável num HTML offline.
2. **Fable como gerente neste projeto.** O registro de agentes mostra o Fable como gerente e auditor de fechamento nas rodadas recentes. No `vibe_code_metrics` você decidiu não usar o Fable. Aqui, mantém o papel de auditor de fechamento ou passa para o Opus?
3. **Limite de cobertura.** Módulos que dependem de pycolmap ou OCR (`sfm.py`, partes de `georef_prancha.py`) são difíceis de testar. Duas opções:
   - limite global de 60%, mais "não pode cair" por módulo;
   - limites diferentes por módulo.

## 5. Como o vcm entra sem duplicar o que já existe

| Já existe no projeto | O vcm acrescenta | Como conviver |
|---|---|---|
| `afericao.py` (órfãs, duplicatas, longas, por rodada) | complexidade, densidade, segurança, cobertura e reprodutibilidade, **por iteração (commit/PR)** | os dois rodam; a régua continua sendo do projeto |
| `determinismo.py` (IA × código por obra) | reprodutibilidade bit a bit dos cálculos | nomes diferentes (ver acima) |
| `pdca/agentes.jsonl` | `vcm agentes` (tokens por tarefa aprovada, por modelo) | o `vcm` passa a ler o formato do projeto, sem um segundo registro |
| `pdca/licoes.jsonl` | lições do método no `vibe_code_metrics` | ficam onde estão |

## 6. Ajustes no vcm revelados por este projeto

Foram feitos no `vibe_code_metrics`, antes da adoção:

- suporte a projeto **sem `pyproject.toml`** (testes rodam com `requirements.txt` e as dependências são contadas a partir dele);
- `vcm iniciar` com o pacote **na raiz** (`camadas/`, sem `src/`);
- `vcm html`, que transforma um Markdown (como este diagnóstico) em HTML formatado;
- `vcm agentes` lendo também `pdca/agentes.jsonl`, sem duplicar o registro (proposto).

## 7. Plano de adoção proposto

Cada passo é um PR pequeno no `projetos_em_camadas`, com o balanço anexado:

| PR | Conteúdo | Agente | Muda comportamento? |
|---|---|---|---|
| 1 | `importorskip` nos 11 testes, `.gitignore` e os 3 alertas de segurança | Haiku | não |
| 2 | `pyproject.toml` com `uv` e extras opcionais, mais `uv.lock` | Sonnet | não (o ambiente fica fixado) |
| 3 | `vcm iniciar` adaptado: `vcm.yaml` com `pastas_fonte: [camadas]`, `CLAUDE.md` integrado à escada de agentes existente e `camadas/referencia.py` com os cálculos de engenharia | Opus + Sonnet | não |
| 4 | Testes de caracterização do pipeline (`obra.py`) com uma obra pequena congelada | Sonnet | não |
| — | Daqui em diante: cada funcionalidade nova com `vcm balanco` e cartão com radar de semáforo | — | — |

Depois do PR 3, o primeiro balanço (`5c2025c` → PR 3) passa a ser a **linha de base oficial** do projeto.
