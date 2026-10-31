# T005 — Decisão

**Status: `inconclusiva_preliminar`** (uma máquina, um protótipo, perfil sintético).
Evidências: `results/runs/T005/runs.parquet` (uma linha por alternativa x tamanho x repetição),
`results/runs/T005/resumo.parquet`, `results/reports/T005.html`.
Reprodução: `uv run python -m vcm.prototipos.perda_de_carga`.

## Ambiente
- `os.cpu_count()` = 4; RAM = 15,7 GiB (psutil); Linux 6.18 x86_64 (container).
- Python 3.13.18, NumPy 2.5.4, Polars 2.1.0, pandas 3.1.0.
- Protocolo: n em {100; 1.000; 10.000; 100.000; 1.000.000}, 1 aquecimento + 7 repetições,
  semente 42. Gabarito (Python puro, soma cumulativa exata) até 100.000 trechos; em 1.000.000 a
  referência é a alternativa NumPy (`referencia = numpy`).

## Resultados (p50 e p95 em ms; pico em MB por tracemalloc; erro em m)

| Alternativa | n trechos | p50 (ms) | p95 (ms) | Pico (MB) | Erro máx. (m) | Determ. | SLOC |
|---|---:|---:|---:|---:|---:|:-:|---:|
| numpy | 100 | 0,376 | 0,726 | 0,013 | 1,1e-13 | sim | 16 |
| polars | 100 | 2,990 | 3,168 | 0,013 | 1,1e-13 | sim | 19 |
| hibrida | 100 | 2,259 | 5,029 | 0,014 | 1,1e-13 | sim | 16 |
| numpy | 1.000 | 0,300 | 0,352 | 0,070 | 1,1e-13 | sim | 16 |
| polars | 1.000 | 2,387 | 2,700 | 0,013 | 1,1e-13 | sim | 19 |
| hibrida | 1.000 | 1,286 | 1,362 | 0,043 | 1,1e-13 | sim | 16 |
| numpy | 10.000 | 0,492 | 0,587 | 0,646 | 2,3e-13 | sim | 16 |
| polars | 10.000 | 4,745 | 5,083 | 0,026 | 2,3e-13 | sim | 19 |
| hibrida | 10.000 | 3,934 | 7,303 | 0,331 | 2,3e-13 | sim | 16 |
| numpy | 100.000 | 2,126 | 3,363 | 6,406 | 3,4e-13 | sim | 16 |
| polars | 100.000 | 8,706 | 9,746 | 0,029 | 3,4e-13 | sim | 19 |
| hibrida | 100.000 | 6,179 | 11,523 | 3,211 | 3,4e-13 | sim | 16 |
| numpy | 1.000.000 | 26,246 | 98,400 | 64,006 | 0 (ref.) | sim | 16 |
| polars | 1.000.000 | 66,512 | 91,806 | 0,032 | 2,7e-20 (vs numpy) | sim | 19 |
| hibrida | 1.000.000 | 24,837 | 26,116 | 32,011 | 0 (vs numpy) | sim | 16 |

Nenhuma alternativa foi eliminada: todos os erros contra o gabarito ficaram em ~1e-13 m (tolerância
1e-9 m) e cada combinação gerou um único hash de saída nas 7 repetições.

## Veredito das hipóteses

- **H1 (tempo): REJEITADA.** Em n = 1.000.000 o Polars puro foi 2,53x MAIS LENTO que o NumPy
  (66,5 ms contra 26,2 ms; o critério era ser pelo menos 20% mais rápido). A metade "NumPy é o mais
  rápido em n <= 1.000" se confirmou (0,30 ms contra 1,29 ms e 2,39 ms em n = 1.000), mas a hipótese
  exigia as duas. Em 1.000.000 a híbrida (24,8 ms) ficou empatada com o NumPy (26,2 ms): a diferença
  de 5% está dentro do ruído, pois o p95 do NumPy foi 98 ms. Parte do custo do Polars vem da conversão
  pandas -> Polars -> pandas exigida pela interface padronizada, e não só do cálculo.
- **H2 (exatidão e determinismo): CONFIRMADA** (nas condições do protocolo). Erro máximo 3,4e-13 m
  contra o gabarito até 100.000 trechos; hash único em todas as 15 combinações. Em 1.000.000 não há
  gabarito: a concordância Polars x NumPy (2,7e-20 m) não valida o NumPy em si.
- **H3 (memória e concisão): REJEITADA.** Em n = 1.000.000, o menor pico por tracemalloc foi o do
  Polars (0,03 MB), não o do NumPy (64,0 MB), mas isso é artefato: o tracemalloc não enxerga a memória
  nativa do Polars, portanto a medida de memória é inconclusiva para o Polars. O Polars também
  NÃO foi o mais conciso: 19 SLOC contra 16 do NumPy e da híbrida. Entre as medidas válidas
  (Python/NumPy), a híbrida usou metade do pico do NumPy (32 contra 64 MB), mas essa diferença não
  estava na hipótese.

## Leitura e limites
- No ponto de operação realista da adutora (centenas a poucos milhares de trechos) o NumPy puro é a
  melhor escolha medida: mais rápido por uma ordem de grandeza, determinístico, exato e com SLOC mínimo.
- Não houve ganho do Polars em nenhum tamanho testado. Não foram testadas entradas já em Polars
  (sem conversão), nem `LazyFrame`, nem controle de threads; o resultado vale para esta interface.
- Uma máquina, 4 CPUs, container, Python 3.13; ruído alto no p95 em n = 1.000.000.
- Memória por tracemalloc subestima a memória nativa do Polars; sem RSS/ru_maxrss por processo
  isolado a comparação de memória Polars x NumPy não é conclusiva.
- Perfil sintético, regime permanente, vazão única, sem perdas localizadas.
- Próximos passos se a tese for retomada: medir RSS em subprocesso, repetir em outra máquina e
  testar entrada nativa Polars.
