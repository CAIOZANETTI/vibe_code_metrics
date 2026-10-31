# T005 — Perda de carga numa adutora de 5 km: NumPy, Polars ou híbrida?

## Problema
Calcular a linha piezométrica de uma adutora por gravidade, dividida em trechos, a partir de um
perfil (comprimento, cota do terreno, diâmetro e coeficiente C de Hazen-Williams por trecho),
da vazão e da cota do nível de montante. Saídas por trecho: perda de carga, perda acumulada,
cota piezométrica e pressão disponível (m.c.a.). Qual implementação é melhor em tempo, memória,
determinismo, exatidão e concisão?

Modelo (SI): `hf = 10,67 · L · Q^1,852 / (C^1,852 · D^4,87)`; perda acumulada = soma cumulativa;
`cota_piezometrica = cota_reservatorio − perda_acumulada` (no fim do trecho);
`pressao_disponivel_mca = cota_piezometrica − cota_terreno`.

## Alternativas
1. **NumPy puro**: colunas viram `ndarray` float64; operações vetorizadas e `np.cumsum`.
2. **Polars puro**: `pl.DataFrame` com expressões (`with_columns`, `cum_sum`), sem sair do Polars.
3. **Híbrida**: Polars para a tabela (entrada e saída) e NumPy para o cálculo.

Todas recebem e devolvem `pandas.DataFrame` (interface padronizada); a conversão faz parte do custo.

## Hipóteses (escritas ANTES de rodar)
- **H1 (tempo).** Em n = 1.000.000 trechos, o Polars puro tem tempo p50 pelo menos 20% menor que o
  NumPy puro (paralelismo e fusão de expressões). Em n ≤ 1.000, o NumPy puro é a alternativa mais
  rápida (menor sobrecarga fixa). Rejeitada se qualquer das duas metades falhar.
- **H2 (exatidão e determinismo).** As três alternativas ficam a ≤ 1e-9 m do gabarito em todos os
  tamanhos e produzem hash de saída idêntico nas 7 repetições. Rejeitada (e a alternativa
  eliminada) se alguma exceder a tolerância ou tiver mais de um hash.
- **H3 (memória e concisão).** Em n = 1.000.000, o NumPy puro tem o menor pico de memória medido por
  `tracemalloc`, e o Polars puro tem o menor SLOC da função `calcular`. Atenção: `tracemalloc`
  não enxerga a memória nativa (Rust) do Polars, então a metade de memória favorece NumPy por
  construção; ela é reportada com essa ressalva.

## Condições de validade
- Uma máquina, um processo, protótipo; resultados descritivos, não generalizáveis.
- Perfil sintético determinístico (semente 42); regime permanente, vazão única, sem perdas localizadas.
- Gabarito em Python puro (`math.fsum` exato) até 100.000 trechos; acima disso, compara-se com o NumPy
  (`referencia = numpy`), o que não valida o próprio NumPy nesses tamanhos.
- Status: `inconclusiva_preliminar`.
