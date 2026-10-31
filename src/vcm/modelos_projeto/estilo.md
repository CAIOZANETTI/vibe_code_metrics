# Estilo de código do repertório

> Regras do mantenedor. Valem para humanos e para **todos os agentes**. Não são negociáveis:
> uma alteração que as viola é revertida, mesmo que melhore as métricas.

## 1. As quatro regras

| # | Regra | Na prática |
|---|---|---|
| 1 | **Python em português** | Nomes de variáveis, funções, classes, módulos, docstrings, comentários e mensagens em português. Palavras-chave da linguagem e APIs de bibliotecas ficam como são. |
| 2 | **Python calcula** | Todo cálculo, agregação, estatística, conversão de unidade e decisão acontece em Python. Nenhum cálculo vai para outra linguagem. |
| 3 | **HTML/JS apresentam** | HTML, CSS e JavaScript só exibem o que o Python já calculou: tabelas, gráficos, navegação e filtros visuais. JS não soma, não converte, não decide. |
| 4 | **Sistema métrico (SI)** | Unidades do Sistema Internacional e as usuais no Brasil (m, mm, m³/s, L/s, kPa, m.c.a., kN, MPa, °C). Nada de pés, polegadas, psi ou galões, nem na entrada nem na saída. |

## 2. Python em português

```python
import numpy as np


def perda_de_carga_hazen_williams(
    vazao_m3s: np.ndarray,
    diametro_m: np.ndarray,
    comprimento_m: np.ndarray,
    coef_c: np.ndarray,
) -> np.ndarray:
    """Perda de carga distribuída por trecho (m), fórmula de Hazen-Williams (SI)."""
    return 10.67 * comprimento_m * vazao_m3s**1.852 / (coef_c**1.852 * diametro_m**4.87)
```

- Nomes descritivos e sem abreviação obscura: `vazao_m3s`, não `q`; `perda_total_m`, não `hf_t`.
- Acentos ficam fora dos identificadores (`vazao`, `pressao`, `funcao`) e dentro das docstrings e mensagens.
- Mensagens de erro e de log também em português: `raise ValueError("diâmetro deve ser positivo")`.
- Termos técnicos sem tradução consagrada podem ficar como estão (`hash`, `commit`, `parquet`, `worktree`).

## 3. Unidade no nome

Toda grandeza física leva a unidade como **sufixo** do nome. Isso evita a classe de erro mais
cara da engenharia, que é a de unidade.

| Grandeza | Sufixo | Exemplo |
|---|---|---|
| comprimento, cota, diâmetro | `_m`, `_mm` | `cota_terreno_m`, `diametro_mm` |
| área | `_m2` | `area_secao_m2` |
| vazão | `_m3s`, `_ls` | `vazao_m3s` |
| velocidade | `_ms` | `velocidade_ms` |
| pressão | `_kpa`, `_mca` | `pressao_mca` |
| força, tensão | `_kn`, `_mpa` | `carga_kn`, `tensao_mpa` |
| tempo | `_s`, `_ms`, `_min` | `tempo_execucao_ms` |
| memória | `_mb` | `pico_ram_mb` |
| adimensional | sem sufixo, nome explícito | `fator_atrito`, `coef_c` |

A conversão de unidade é feita **uma vez, na entrada**, por função explícita (`mm_para_m`).
O núcleo de cálculo trabalha só em SI.

## 4. Python calcula de forma vetorizada e determinística

- **NumPy primeiro** para cálculo numérico: operações vetorizadas e matriciais, sem laço Python sobre elementos.
- **pandas ou Polars** para dados tabulares: filtrar, juntar, agrupar. A escolha entre eles é **tese**, não gosto (ver T005).
- **Parquet** para persistir tabelas; YAML para configuração; JSON Lines para logs brutos.
- `dtype` explícito (`float64` para engenharia) e `np.random.default_rng(semente)` sempre com semente.
- Comparações numéricas com tolerância declarada (`np.testing.assert_allclose`), nunca `==` em float.
- Cota, coordenada e nível usam **tolerância absoluta** (m), não relativa.
- Funções puras no núcleo de cálculo: mesma entrada, mesma saída; nada de ler relógio, rede ou estado global.

## 5. HTML e JavaScript só apresentam

```text
Python (numpy/pandas) --calcula--> tabela/figura pronta --serializa--> HTML (+ Plotly JS)
```

- O Python gera o HTML, com Jinja2 para o texto e Plotly para gráficos, já com os valores finais.
- O JavaScript se limita a renderizar gráficos, alternar abas, ordenar e filtrar tabelas.
  Valores exibidos vêm prontos e formatados.
- Formatação brasileira na apresentação: vírgula decimal e ponto de milhar (`1.234,56`),
  datas `dd/mm/aaaa`. A formatação também é feita em Python (`vcm.formatacao`).

## 6. Verificação

O CI e a retrospectiva conferem estas regras automaticamente, na medida do possível:

| Regra | Verificação |
|---|---|
| Português | revisão; vocabulário de identificadores em inglês sinalizado na retrospectiva (Fase 1) |
| Python calcula | busca por operações aritméticas em `<script>` dos HTML gerados (Fase 4) |
| SI | busca por unidades imperiais (`inch`, `ft`, `psi`, `gal`) no código e nos relatórios |
| Unidade no nome | revisão; testes de unidade nas funções de cálculo |
