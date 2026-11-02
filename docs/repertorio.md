# Repertório de ferramentas

> Premissas de uso de cada ferramenta: quando considerar, quando evitar e os cuidados.
> Só se comparam ferramentas do **mesmo papel**; a escolha entre elas é tese, não gosto.
> Licença e versão foram conferidas na fonte (PyPI e repositório) na data indicada.
> Página gerada a partir de `repertorio/*/*.yaml` por `vcm docs`; edite os YAML.

| Papel | Ferramentas |
|---|---|
| Cálculo numérico | NumPy, SciPy |
| Dados tabulares | DuckDB, pandas, Polars |
| Armazenamento | GeoParquet, Parquet, SQLite |
| Grafos | NetworkX, rustworkx |
| Intercâmbio de dados | JSON-LD |
| Apresentação | Jinja2, Plotly |

## Cálculo numérico

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [NumPy](https://numpy.org/doc/stable/) | em uso | — | — | — |
| [SciPy](https://docs.scipy.org/doc/scipy/) | candidato | — | — | — |

### NumPy

Arrays N-dimensionais e álgebra linear vetorizada em Python.

_Coopera com `pandas`, `polars`, `plotly`._

**Quando considerar**

- cálculo matricial e vetorizado
- álgebra linear

**Quando evitar**

- dados tabulares heterogêneos com junções e agrupamentos

**Cuidados**

- a ordem das somas pode variar com o número de threads do BLAS; medir determinismo
- {'medido em 31/10/2026 (vcm.coletores.determinismo, 4 núcleos)': 'produto matricial 500×500 e solve 200×200 mudam de hash entre 1 thread e o padrão; com threads fixas, 100% estável; cumsum não muda. Fixar OPENBLAS_NUM_THREADS quando o resultado precisar ser reprodutível bit a bit'}

### SciPy

Algoritmos científicos sobre NumPy, como otimização, interpolação, estatística e álgebra linear esparsa.

_Coopera com `numpy`, `pandas`._

**Quando considerar**

- otimização numérica
- interpolação
- estatística
- álgebra linear esparsa

**Quando evitar**

- manipulação de tabelas com junções e agrupamentos

**Cuidados**

- solvers iterativos dependem de tolerância e critério de parada; declarar ambos

## Dados tabulares

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [DuckDB](https://duckdb.org/docs/) | candidato | — | — | — |
| [pandas](https://pandas.pydata.org/docs/) | em uso | — | — | — |
| [Polars](https://docs.pola.rs/) | em teste | — | — | — |

### DuckDB

Banco SQL analítico embutido no processo, que lê arquivos Parquet e CSV diretamente.

_Compete com `pandas`, `polars`; coopera com `parquet`, `pandas`, `polars`._

**Quando considerar**

- consultas SQL sobre arquivos grandes
- junções e agregações complexas
- operação sem servidor

**Quando evitar**

- muitos processos escrevendo ao mesmo tempo
- aplicações transacionais de alta frequência de escrita

**Cuidados**

- um arquivo de banco aceita um processo escritor por vez

### pandas

Biblioteca de DataFrames para filtrar, juntar e agrupar dados tabulares em Python.

_Compete com `polars`, `duckdb`; coopera com `numpy`, `parquet`, `plotly`._

**Quando considerar**

- dados tabulares com junções e agrupamentos
- ecossistema maduro e amplamente documentado
- integração direta com NumPy e Parquet

**Quando evitar**

- volumes que não cabem com folga na memória
- pipelines que se beneficiam de execução preguiçosa otimizada

**Cuidados**

- o comportamento de valores ausentes e os tipos dependem do dtype; definir dtype explícito
- algumas operações copiam os dados

### Polars

Biblioteca de DataFrames com motor escrito em Rust, baseada em Apache Arrow e com API de expressões.

_Compete com `pandas`, `duckdb`; coopera com `numpy`, `parquet`, `plotly`._

**Quando considerar**

- tabelas grandes
- agregações e junções em paralelo
- execução preguiçosa com otimização de consulta

**Quando evitar**

- código existente que depende fortemente da API do pandas
- bibliotecas que aceitam apenas pandas

**Cuidados**

- a API difere do pandas, pois não há índice de linha
- na execução preguiçosa, o resultado só existe após collect()

## Armazenamento

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [GeoParquet](https://geoparquet.org/) | candidato | — | — | — |
| [Parquet](https://arrow.apache.org/docs/python/parquet.html) | em uso | — | — | — |
| [SQLite](https://docs.python.org/3/library/sqlite3.html) | candidato | — | — | — |

### GeoParquet

Parquet com metadados geoespaciais padronizados, lido e escrito com GeoPandas.

_Compete com `sqlite`; coopera com `pandas`, `parquet`._

**Quando considerar**

- tabelas com geometrias trocadas entre ferramentas
- preservar colunas e tipos do Parquet

**Quando evitar**

- consultas espaciais complexas e frequentes, para as quais um banco espacial é mais adequado
- dados sem geometria

**Cuidados**

- a versão da especificação de metadados precisa ser declarada
- o sistema de referência de coordenadas precisa ser declarado

### Parquet

Formato de arquivo colunar, lido e escrito em Python pelo pacote pyarrow.

_Compete com `sqlite`; coopera com `pandas`, `polars`, `duckdb`._

**Quando considerar**

- persistir tabelas grandes
- leitura seletiva de colunas
- compressão por coluna

**Quando evitar**

- edição linha a linha
- arquivos pequenos que são reescritos com muita frequência

**Cuidados**

- declarar os tipos explicitamente ao gravar
- o arquivo não é alterado no lugar; ele é reescrito por inteiro

### SQLite

Banco relacional em arquivo único, embutido, disponível pela biblioteca padrão do Python.

_Compete com `parquet`, `geoparquet`; coopera com `pandas`, `duckdb`._

**Quando considerar**

- armazenar tabelas pequenas e médias com consultas SQL
- não exigir dependência extra

**Quando evitar**

- volumes analíticos grandes com varreduras de colunas
- muitos escritores concorrentes

**Cuidados**

- aceita um escritor por vez
- os tipos são dinâmicos, não rígidos
- a verificação de chaves estrangeiras precisa ser ativada explicitamente

## Grafos

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [NetworkX](https://networkx.org/documentation/stable/) | candidato | — | — | — |
| [rustworkx](https://www.rustworkx.org/) | candidato | — | — | — |

### NetworkX

Biblioteca de grafos em Python puro, com grande conjunto de algoritmos e API flexível.

_Compete com `rustworkx`; coopera com `numpy`, `pandas`._

**Quando considerar**

- prototipar algoritmos de grafos
- grafos de tamanho moderado
- atributos arbitrários em nós e arestas

**Quando evitar**

- grafos muito grandes em que o tempo de execução é o fator limitante

**Cuidados**

- a implementação em Python é mais lenta que a de bibliotecas com núcleo nativo
- a ordem de iteração segue a ordem de inserção; fixá-la para resultados reproduzíveis

### rustworkx

Biblioteca de grafos com núcleo em Rust e API em Python.

_Compete com `networkx`; coopera com `numpy`, `pandas`._

**Quando considerar**

- grafos grandes
- algoritmos de grafos com execução em código nativo

**Quando evitar**

- quando os nós precisam ser identificados diretamente por rótulos de domínio
- quando é preciso o ecossistema mais amplo de algoritmos do NetworkX

**Cuidados**

- os nós são referenciados por índices inteiros; mapear os identificadores de domínio para esses índices

## Intercâmbio de dados

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [JSON-LD](https://json-ld.org/) | candidato | — | — | — |

### JSON-LD

Formato de dados ligados em JSON, em que um contexto associa termos a identificadores globais (IRIs).

**Quando considerar**

- intercambiar dados semânticos com vocabulário compartilhado
- publicar metadados vinculados a outros conjuntos de dados

**Quando evitar**

- troca interna simples, em que um JSON comum basta

**Cuidados**

- a expansão de contexto pode buscar URLs remotos; usar carregador local e controlado

## Apresentação

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [Jinja2](https://jinja.palletsprojects.com/) | em uso | — | — | — |
| [Plotly](https://plotly.com/python/) | em uso | — | — | — |

### Jinja2

Motor de templates para gerar texto e HTML a partir de dados já calculados em Python.

_Coopera com `plotly`._

**Quando considerar**

- montar relatórios HTML com laços e blocos reutilizáveis
- separar apresentação do cálculo

**Quando evitar**

- lógica de negócio dentro do template

**Cuidados**

- o autoescape vem desligado por padrão no Environment; ligá-lo para HTML

### Plotly

Gráficos interativos gerados em Python e renderizados no navegador pelo Plotly.js.

_Coopera com `jinja2`, `numpy`, `pandas`, `polars`._

**Quando considerar**

- gráficos interativos em HTML autocontido
- receber DataFrames de pandas e Polars

**Quando evitar**

- figuras estáticas para publicação impressa, em que uma ferramenta de figura estática é mais simples

**Cuidados**

- o HTML gerado inclui JavaScript; o JavaScript só exibe valores já calculados
