# Repertório de ferramentas

> Premissas de uso de cada ferramenta: quando considerar, quando evitar e os cuidados.
> Só se comparam ferramentas do **mesmo papel**; a escolha entre elas é tese, não gosto.
> Licença e versão foram conferidas na fonte (PyPI e repositório) na data indicada.
> Página gerada a partir de `repertorio/*/*.yaml` por `vcm docs`; edite os YAML.

| Papel | Ferramentas |
|---|---|
| Cálculo numérico | Numba, NumPy, SciPy, SymPy, xarray |
| Dados tabulares | DuckDB, pandas, Polars |
| Armazenamento | GeoParquet, Parquet, SQLite |
| Validação e unidades | pandera, Pint, Pydantic |
| Geoespacial | GeoPandas, pyproj, rasterio, Shapely |
| CAD, BIM e 3D | ezdxf, IfcOpenShell, Open3D, pycolmap |
| Grafos | NetworkX, python-igraph, rustworkx |
| Intercâmbio de dados | JSON-LD, RDFLib |
| Documentos e OCR | Docling, PaddleOCR, pdfplumber, PyMuPDF, pytesseract |
| Apresentação | Jinja2, Matplotlib, Plotly |
| Qualidade e testes | Hypothesis, mutmut, pytest-benchmark |

## Cálculo numérico

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [Numba](https://numba.readthedocs.io/en/stable/) | candidato | BSD-2-Clause | 0.68.1 (2026-10) | 2026-11-02 |
| [NumPy](https://numpy.org/doc/stable/) | em uso | BSD-3-Clause | 2.5.4 (2026-10) | 2026-11-02 |
| [SciPy](https://docs.scipy.org/doc/scipy/) | candidato | BSD-3-Clause | 1.18.1 (2026-08) | 2026-11-02 |
| [SymPy](https://docs.sympy.org/latest/) | candidato | BSD-3-Clause | 1.14.0 (2025-04) | 2026-11-02 |
| [xarray](https://docs.xarray.dev/) | candidato | Apache-2.0 | 2026.9.0 (2026-09) | 2026-11-02 |

### Numba

Compilador JIT que traduz funções Python e NumPy em código de máquina via LLVM.

_Coopera com `numpy`, `scipy`, `sympy`._

**Quando considerar**

- laços numéricos escalares que não vetorizam bem em NumPy (marcha de cálculo trecho a trecho, iterações com dependência entre passos)
- funções chamadas muitas vezes sobre arrays grandes, em que o custo de compilação se paga
- paralelismo simples em laços independentes com prange
- manter o código Python legível em vez de reescrevê-lo em C ou Rust

**Quando evitar**

- funções curtas ou chamadas poucas vezes, em que a compilação custa mais que o ganho
- código que usa DataFrames, strings, objetos Python ou bibliotecas fora do subconjunto suportado
- cálculo que já se expressa em operações vetorizadas de NumPy

**Cuidados**

- a primeira chamada compila e é lenta; cache=True guarda a compilação em disco
- fastmath=True permite reordenar operações de ponto flutuante e pode mudar o resultado; evitar quando o resultado precisar ser reprodutível
- com parallel=True a ordem das reduções pode variar entre execuções; medir determinismo antes de adotar
- o Numba aceita só algumas versões do NumPy e do Python; conferir a compatibilidade antes de atualizar o NumPy
- variáveis globais são tratadas como constantes no momento da compilação
- erros de tipagem são difíceis de ler; testar a função também com NUMBA_DISABLE_JIT para depurar

Repositório: <https://github.com/numba/numba>

### NumPy

Arrays N-dimensionais e álgebra linear vetorizada em Python.

_Coopera com `pandas`, `polars`, `plotly`, `scipy`, `numba`, `xarray`, `pint`._

**Quando considerar**

- cálculo matricial e vetorizado
- álgebra linear
- base comum do ecossistema numérico (pandas, SciPy e Plotly trocam dados com arrays NumPy)
- cálculo elemento a elemento sobre milhares de seções, trechos ou nós sem laços em Python
- dtype explícito (float64, int32) torna o comportamento numérico previsível e documentável

**Quando evitar**

- dados tabulares heterogêneos com junções e agrupamentos
- dados com dimensões nomeadas e coordenadas (tempo, cota, estação), em que o rótulo evita erro de eixo (considerar xarray)
- laços escalares que não vetorizam, em que um compilador JIT pode ser mais adequado (considerar numba)

**Cuidados**

- a ordem das somas pode variar com o número de threads do BLAS; medir determinismo
- {'medido em 31/10/2026 (vcm.coletores.determinismo, 4 núcleos)': 'produto matricial 500×500 e solve 200×200 mudam de hash entre 1 thread e o padrão; com threads fixas, 100% estável; cumsum não muda. Fixar OPENBLAS_NUM_THREADS quando o resultado precisar ser reprodutível bit a bit'}
- float32 acumula erro diferente de float64; declarar o dtype e a tolerância absoluta ou relativa nos testes (np.testing.assert_allclose com atol e rtol explícitos)
- o NumPy 2 mudou as regras de promoção de tipos (NEP 50) e removeu aliases antigos; código escrito para 1.x pode mudar de dtype
- fatias são vistas, não cópias; alterar uma fatia altera o array original

Repositório: <https://github.com/numpy/numpy>

### SciPy

Algoritmos científicos sobre NumPy, como otimização, interpolação, estatística e álgebra linear esparsa.

_Coopera com `numpy`, `pandas`, `sympy`, `numba`, `xarray`._

**Quando considerar**

- otimização numérica
- interpolação
- estatística
- álgebra linear esparsa
- sistemas grandes e esparsos (redes de tubulação, malhas, matrizes de rigidez) com scipy.sparse
- integração numérica e equações diferenciais ordinárias (scipy.integrate) com tolerâncias declaradas
- raízes e ajuste de curvas (scipy.optimize) para equações implícitas, como Colebrook-White

**Quando evitar**

- manipulação de tabelas com junções e agrupamentos
- álgebra simbólica ou derivação exata (considerar sympy)
- quando uma operação simples de NumPy já resolve

**Cuidados**

- solvers iterativos dependem de tolerância e critério de parada; declarar ambos
- rotinas de otimização podem convergir para mínimo local ou falhar sem lançar erro; verificar o campo success do resultado e registrar o ponto inicial
- interpoladores tratam de formas diferentes o que está fora do intervalo dos dados (erro, constante, extrapolação); declarar o comportamento escolhido
- herda do NumPy a variação de somas com threads do BLAS; fixar threads quando o resultado precisar ser reprodutível bit a bit
- a versão 1.18 exige Python 3.12 ou mais recente; conferir a versão do Python do projeto
- algoritmos estocásticos (por exemplo, evolução diferencial) exigem semente fixa para serem determinísticos

Repositório: <https://github.com/scipy/scipy>

### SymPy

Álgebra simbólica em Python puro, com derivação, integração, resolução de equações e geração de código.

_Coopera com `numpy`, `scipy`, `numba`, `pint`._

**Quando considerar**

- deduzir e conferir uma fórmula de engenharia (derivadas, integrais, simplificação) antes de implementá-la
- gerar a função numérica a partir da expressão simbólica com lambdify, mantendo a fórmula documentada e testável
- obter por solução exata um caso de teste que o código numérico deve reproduzir
- resolver sistemas pequenos de equações com solução em forma fechada

**Quando evitar**

- cálculo numérico pesado sobre arrays grandes, em que o simbólico é lento (usar numpy ou scipy)
- caminho de produção sensível a tempo, se a expressão simbólica for montada a cada chamada
- equações sem solução fechada, melhor resolvidas por métodos numéricos (scipy)

**Cuidados**

- simplify e solve podem demorar muito ou devolver formas diferentes entre versões; fixar a versão e não depender da forma textual do resultado
- lambdify gera função NumPy; conferir o módulo de destino e o dtype
- usar Rational ou inteiros em vez de float dentro da expressão evita erro de arredondamento antes da hora
- a última versão publicada (1.14.0) é de 2025-04; verificar se há versão mais nova antes de adotar

Repositório: <https://github.com/sympy/sympy>

### xarray

Arrays N-dimensionais com dimensões nomeadas, coordenadas e atributos, sobre NumPy e pandas.

_Coopera com `numpy`, `pandas`, `pint`._

**Quando considerar**

- dados em grade ou multidimensionais (tempo × estação, tempo × cota × posição, séries de chuva, campos de modelo)
- operar por nome de dimensão, sem depender da ordem dos eixos, o que reduz erros de eixo
- ler e gravar NetCDF e Zarr, formatos comuns de dados hidrológicos e climáticos
- manter metadados e unidades declaradas junto dos valores (atributos)

**Quando evitar**

- dados tabulares simples, melhor atendidos por pandas ou Polars
- cálculo sobre um array sem coordenadas, em que NumPy basta

**Cuidados**

- o alinhamento automático por coordenadas faz junção implícita; coordenadas float diferentes por arredondamento geram eixo vazio ou NaN sem aviso
- depende de NumPy e pandas; o cálculo de fundo é do NumPy e herda sua variação de threads
- arrays com Dask são preguiçosos e o resultado só existe após compute()
- as unidades ficam em atributos de texto e não são verificadas; para checagem, combinar com pint
- a versão segue o calendário (2026.9.0) e a API muda entre versões; fixar a versão

Repositório: <https://github.com/pydata/xarray>

## Dados tabulares

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [DuckDB](https://duckdb.org/docs/) | candidato | MIT | 2.0.0 (2026-10) | 2026-11-02 |
| [pandas](https://pandas.pydata.org/docs/) | em uso | BSD-3-Clause | 3.1.0 (2026-10) | 2026-11-02 |
| [Polars](https://docs.pola.rs/) | em teste | MIT | 2.1.0 (2026-10) | 2026-11-02 |

### DuckDB

Banco SQL analítico embutido no processo, que lê arquivos Parquet e CSV diretamente.

_Compete com `pandas`, `polars`; coopera com `parquet`, `pandas`, `polars`, `sqlite`._

**Quando considerar**

- consultas SQL sobre arquivos grandes
- junções e agregações complexas
- operação sem servidor
- consultar Parquet em disco sem carregar tudo na memória, com SQL
- consultar DataFrames do pandas ou Polars já em memória com SQL, sem cópia explícita
- SQL com funções de janela para consultas analíticas sobre séries e resumos

**Quando evitar**

- muitos processos escrevendo ao mesmo tempo
- aplicações transacionais de alta frequência de escrita
- cálculo numérico de engenharia, que deve ficar em NumPy; o DuckDB serve para consulta e agregação

**Cuidados**

- um arquivo de banco aceita um processo escritor por vez
- a versão 2.0 é recente; fixar a versão e conferir a compatibilidade do formato de arquivo de banco ao atualizar
- somas de ponto flutuante em paralelo podem variar na última casa; ordenar e usar DECIMAL ou arredondamento declarado quando o resultado precisar ser reprodutível
- o limite de memória e o diretório temporário para derramamento em disco são configuráveis; declarar ambos em consultas grandes

Repositório: <https://github.com/duckdb/duckdb-python>

### pandas

Biblioteca de DataFrames para filtrar, juntar e agrupar dados tabulares em Python.

_Compete com `polars`, `duckdb`; coopera com `numpy`, `parquet`, `plotly`, `pandera`, `xarray`, `scipy`._

**Quando considerar**

- dados tabulares com junções e agrupamentos
- ecossistema maduro e amplamente documentado
- integração direta com NumPy e Parquet
- séries temporais com índice de datas e reamostragem (medições, vazões, precipitação)
- bibliotecas de terceiros (Plotly, GeoPandas, pandera) que aceitam DataFrame do pandas

**Quando evitar**

- volumes que não cabem com folga na memória
- pipelines que se beneficiam de execução preguiçosa otimizada
- junções e agregações muito grandes, em que Polars ou DuckDB tendem a usar melhor a memória (medir antes)

**Cuidados**

- o comportamento de valores ausentes e os tipos dependem do dtype; definir dtype explícito
- algumas operações copiam os dados
- o pandas 3 adotou copy-on-write e removeu a atribuição encadeada; usar df.loc[mascara, coluna] = valor
- o pandas 3 infere colunas de texto como dtype str (antes object) e a resolução de datas passou a ser inferida (microssegundos para texto); converter data para inteiro sem fixar a unidade (as_unit) dá valores diferentes
- arredondamento e somas em ponto flutuante dependem da ordem das linhas; ordenar de forma explícita antes de agregar quando o resultado precisar ser reprodutível

Repositório: <https://github.com/pandas-dev/pandas>

### Polars

Biblioteca de DataFrames com motor escrito em Rust, baseada em Apache Arrow e com API de expressões.

_Compete com `pandas`, `duckdb`; coopera com `numpy`, `parquet`, `plotly`, `duckdb`, `pandera`._

**Quando considerar**

- tabelas grandes
- agregações e junções em paralelo
- execução preguiçosa com otimização de consulta
- expressões preguiçosas otimizam junções e filtros em tabelas grandes, lendo Parquet com seleção de colunas e filtro empurrados para a leitura
- tipos estritos e valores nulos explícitos, sem conversões silenciosas de inteiro para float

**Quando evitar**

- código existente que depende fortemente da API do pandas
- bibliotecas que aceitam apenas pandas
- código que depende do índice de linha do pandas (alinhamento por índice, reindex)

**Cuidados**

- a API difere do pandas, pois não há índice de linha
- na execução preguiçosa, o resultado só existe após collect()
- o paralelismo pode alterar a ordem das linhas em agregações e junções; ordenar explicitamente (ou usar maintain_order) quando a ordem importar
- a API ainda evolui entre versões; fixar a versão no projeto
- a conversão para pandas ou NumPy (to_pandas, to_numpy) pode copiar dados e exige pyarrow ou numpy instalados

Repositório: <https://github.com/pola-rs/polars>

## Armazenamento

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [GeoParquet](https://geoparquet.org/) | candidato | BSD-3-Clause | 1.2.0 (2026-09) | 2026-11-02 |
| [Parquet](https://arrow.apache.org/docs/python/parquet.html) | em uso | Apache-2.0 | 26.0.0 (2026-10) | 2026-11-02 |
| [SQLite](https://docs.python.org/3/library/sqlite3.html) | candidato | blessing | 3.54.1 (2026-10) | 2026-11-02 |

### GeoParquet

Parquet com metadados geoespaciais padronizados, lido e escrito com GeoPandas.

_Compete com `sqlite`; coopera com `pandas`, `parquet`, `shapely`, `pyproj`, `geopandas`._

**Quando considerar**

- tabelas com geometrias trocadas entre ferramentas
- preservar colunas e tipos do Parquet
- guardar atributos e geometria juntos, com o sistema de coordenadas gravado no arquivo

**Quando evitar**

- consultas espaciais complexas e frequentes, para as quais um banco espacial é mais adequado
- dados sem geometria

**Cuidados**

- a versão da especificação de metadados precisa ser declarada
- o sistema de referência de coordenadas precisa ser declarado
- geopandas depende de bibliotecas nativas (GEOS, PROJ) trazidas por shapely e pyproj; conferir a instalação em cada ambiente
- a versão e a licença informadas são do pacote geopandas; a especificação GeoParquet tem versionamento próprio e não foi verificada em 2026-11-02

Repositório: <https://github.com/geopandas/geopandas>

### Parquet

Formato de arquivo colunar, lido e escrito em Python pelo pacote pyarrow.

_Compete com `sqlite`; coopera com `pandas`, `polars`, `duckdb`, `geoparquet`, `pandera`._

**Quando considerar**

- persistir tabelas grandes
- leitura seletiva de colunas
- compressão por coluna
- trocar tabelas entre pandas, Polars e DuckDB preservando os tipos
- guardar resultados de cálculo com esquema explícito (tipos, nulos) e metadados do arquivo

**Quando evitar**

- edição linha a linha
- arquivos pequenos que são reescritos com muita frequência
- dados que precisam ser lidos por pessoas em editor de texto (usar CSV)

**Cuidados**

- declarar os tipos explicitamente ao gravar
- o arquivo não é alterado no lugar; ele é reescrito por inteiro
- o hash do arquivo pode mudar entre versões do pyarrow ou com metadados e compressão diferentes; para reprodutibilidade, comparar o conteúdo (tabela) e não os bytes, ou fixar versão e opções de escrita
- a escrita via pandas grava o índice e metadados do pandas por padrão; declarar index=False quando não for desejado
- carimbos de data e hora têm resolução e fuso próprios; declarar a unidade ao gravar

Repositório: <https://github.com/apache/arrow>

### SQLite

Banco relacional em arquivo único, embutido, disponível pela biblioteca padrão do Python.

_Compete com `parquet`, `geoparquet`; coopera com `pandas`, `duckdb`, `pydantic`._

**Quando considerar**

- armazenar tabelas pequenas e médias com consultas SQL
- não exigir dependência extra
- guardar estado de aplicação web de cálculo (cadastros, execuções, parâmetros) com transações
- atualizar linhas no lugar, o que o Parquet não faz

**Quando evitar**

- volumes analíticos grandes com varreduras de colunas
- muitos escritores concorrentes
- tabelas largas lidas por coluna em grande volume (preferir Parquet)

**Cuidados**

- aceita um escritor por vez
- os tipos são dinâmicos, não rígidos
- a verificação de chaves estrangeiras precisa ser ativada explicitamente
- a versão do SQLite embutida depende do Python instalado, não do pacote; funcionalidades novas podem faltar em Pythons antigos
- a licença é de domínio público (identificador SPDX blessing, usado nos fontes do SQLite); a versão do pacote Python não se aplica, pois sqlite3 é módulo da biblioteca padrão

Repositório: <https://sqlite.org/src>

## Validação e unidades

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [pandera](https://pandera.readthedocs.io/) | candidato | MIT | 0.35.0 (2026-10) | 2026-11-02 |
| [Pint](https://pint.readthedocs.io/) | candidato | BSD-3-Clause | 0.26.2 (2026-10) | 2026-11-02 |
| [Pydantic](https://pydantic.dev/docs/validation/latest/get-started/) | candidato | MIT | 2.14.2 (2026-10) | 2026-11-02 |

### pandera

Validação de DataFrames por esquemas declarados (tipos, faixas, nulos, unicidade e checagens estatísticas).

_Compete com `pydantic`; coopera com `pandas`, `polars`, `parquet`._

**Quando considerar**

- conferir tabelas de entrada e saída (colunas, dtype, faixas físicas, ausência de nulos, unicidade de chaves) antes e depois do cálculo
- detectar na leitura um Parquet ou CSV com coluna faltando ou dtype trocado
- coletar todas as falhas de uma tabela de uma vez com validate(lazy=True)
- esquema único para pandas e Polars, quando os dois estiverem em uso

**Quando evitar**

- validar um registro isolado ou um formulário (usar pydantic)
- tabelas muito pequenas e estáveis, em que um assert simples basta

**Cuidados**

- {'a validação não é preguiçosa por padrão': 'sem lazy=True para no primeiro erro'}
- o suporte é dividido em extras (pandera[pandas], pandera[polars]); instalar o extra do motor usado
- desde a 0.29 importar de pandera.pandas; a importação pelo módulo raiz está obsoleta
- checagens de dados percorrem a tabela inteira e custam tempo em tabelas grandes; validar na fronteira, não a cada passo
- a API ainda é 0.x e muda entre versões; fixar a versão

Repositório: <https://github.com/pandera-dev/pandera>

### Pint

Biblioteca de grandezas físicas com unidades, que converte e recusa operações dimensionalmente inconsistentes.

_Coopera com `numpy`, `pandas`, `xarray`, `sympy`, `pydantic`._

**Quando considerar**

- fronteiras do sistema (entrada de usuário, planilhas, arquivos de terceiros) em que as unidades chegam misturadas e precisam virar SI
- fórmulas de engenharia em que um erro de unidade (mm × m, L/s × m3/s) é um risco real
- testes que conferem consistência dimensional da fórmula, não só o valor numérico
- converter para SI na entrada e trabalhar com arrays NumPy puros no miolo do cálculo

**Quando evitar**

- laços internos de cálculo pesado, em que o objeto com unidade atrapalha o desempenho e a vetorização
- código que já segue a regra de unidade SI como sufixo do nome e não recebe dados em outras unidades
- quando as unidades só precisam constar como metadado (atributos do xarray ou nome da coluna)

**Cuidados**

- unidades com deslocamento (graus Celsius) têm regras próprias; somar duas temperaturas absolutas gera erro e diferenças usam delta_degC
- usar um único registro de unidades (UnitRegistry) em todo o projeto; quantidades de registros diferentes não se misturam
- o resultado de Quantity.magnitude é um número ou array NumPy sem unidade; converter para a unidade SI esperada antes de extraí-lo
- nem toda função do NumPy e do pandas preserva as unidades; testar as operações usadas
- a versão atual exige Python 3.12 ou mais recente

Repositório: <https://github.com/hgrecco/pint>

### Pydantic

Validação de dados por esquemas declarados com anotações de tipo, com erros detalhados e exportação de JSON Schema.

_Compete com `pandera`; coopera com `pint`, `sqlite`, `pandas`._

**Quando considerar**

- validar parâmetros de entrada de um cálculo (formulário web, JSON, YAML) antes de executá-lo
- declarar faixas e restrições físicas dos campos (valor positivo, diâmetro mínimo) com mensagens de erro claras
- gerar o JSON Schema do contrato de dados entre o cálculo em Python e a interface
- registros e configurações com poucos campos, validados um a um

**Quando evitar**

- validar milhões de linhas de um DataFrame, em que um modelo por linha é lento (usar pandera)
- cálculo numérico; o Pydantic valida estrutura e tipos, não faz a conta
- quando uma dataclass simples e testes já bastam

**Cuidados**

- o modo padrão é permissivo e converte tipos (a string "123" vira inteiro 123); usar strict=True quando uma conversão silenciosa for inaceitável
- float aceita NaN e infinito por padrão; restringir com allow_inf_nan=False quando o valor entrar em cálculo
- a versão 2 mudou a API em relação à 1 (validadores, model_validate, model_dump); código e tutoriais antigos podem não valer
- o núcleo de validação é compilado (Rust), com wheels nativas por plataforma
- a página da documentação oficial migrou de docs.pydantic.dev para pydantic.dev/docs

Repositório: <https://github.com/pydantic/pydantic>

## Geoespacial

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [GeoPandas](https://geopandas.org) | em uso | BSD-3-Clause | 1.2.0 (2026-09) | 2026-11-02 |
| [pyproj](https://pyproj4.github.io/pyproj/) | em uso | MIT | 3.8.0 (2026-09) | 2026-11-02 |
| [rasterio](https://rasterio.readthedocs.io/) | em uso | BSD-3-Clause | 1.5.2 (2026-09) | 2026-11-02 |
| [Shapely](https://shapely.readthedocs.io/) | em uso | BSD-3-Clause | 2.2.0 (2026-10) | 2026-11-02 |

### GeoPandas

Tabelas do pandas com coluna de geometria (Shapely) e CRS, com leitura e escrita de formatos vetoriais.

_Coopera com `shapely`, `pyproj`, `pandas`, `geoparquet`, `rasterio`._

**Quando considerar**

- tabela de lotes, trechos de rede, sondagens ou pranchas com atributos e geometria juntos
- junção espacial (sjoin, sjoin_nearest) para ligar trecho de tubo à sondagem mais próxima
- reprojetar uma camada inteira com to_crs
- ler e gravar GeoPackage, GeoJSON, Shapefile e GeoParquet

**Quando evitar**

- quando só se precisa de poucas geometrias soltas; shapely basta
- ambientes em que a instalação de dependências nativas (GDAL ou Pyogrio) é um problema
- volumes grandes de dados tabulares sem geometria

**Cuidados**

- to_crs reprojeta; set_crs apenas rotula. Trocar um pelo outro corrompe as coordenadas sem dar erro
- medir área e comprimento só em CRS métrico (UTM); em graus o resultado não é metro
- nas geometrias a ordem é x=leste/longitude, y=norte/latitude
- a leitura depende de Pyogrio ou Fiona (GDAL); registrar a versão da GDAL que veio na roda
- Shapefile trunca nomes de coluna para 10 caracteres e tem limites de tipos; preferir GeoPackage ou GeoParquet
- sjoin e overlay podem reordenar linhas; ordenar por chave explícita antes de gravar para ter resultado determinístico
- geometrias inválidas fazem overlay falhar; validar antes

Repositório: <https://github.com/geopandas/geopandas>

### pyproj

Interface Python para a biblioteca PROJ, para transformar coordenadas entre sistemas de referência.

_Coopera com `shapely`, `geopandas`, `rasterio`, `numpy`._

**Quando considerar**

- converter SIRGAS 2000 geográfico (EPSG:4674) para UTM SIRGAS 2000 (zonas EPSG:31978 a 31985 no Brasil) e o inverso
- converter coordenadas de EXIF de drone (WGS 84, EPSG:4326) para o UTM do projeto
- declarar o sistema de coordenadas de cada camada (ortofoto, pranchas, rede) e transformar entre elas de forma explícita
- cálculo geodésico (distância e azimute sobre o elipsoide) com a classe Geod

**Quando evitar**

- quando o projeto é puramente local e todas as camadas já estão no mesmo CRS métrico
- quando se quer manipular geometrias inteiras; combinar com shapely ou geopandas

**Cuidados**

- usar Transformer.from_crs(origem, destino, always_xy=True); sem isso, a ordem dos eixos segue a definição da autoridade (latitude, longitude para EPSG:4326 e 4674) e o ponto sai invertido
- SIRGAS 2000 e WGS 84 diferem por poucos decímetros; tratar como iguais só se a tolerância do projeto permitir, e declarar a escolha
- a transformação depende da base de dados do PROJ (grades, datum shifts); registrar a versão do PROJ embutida na roda para reprodutibilidade
- grades de datum opcionais podem não estar instaladas; conferir a operação escolhida (Transformer.description) e se a precisão é a esperada
- a zona UTM deve ser escolhida pela longitude ou fixada no projeto; coordenadas fora da zona natural distorcem a escala
- a PROJ vem embarcada nas rodas binárias; compilar do código-fonte exige PROJ instalada no sistema
- fixar o EPSG como constante nomeada e usar sufixo de unidade nos nomes (leste_m, norte_m)

Repositório: <https://github.com/pyproj4/pyproj>

### rasterio

Leitura e escrita de rasters georreferenciados (GeoTIFF e outros) sobre a GDAL, com arrays NumPy.

_Coopera com `numpy`, `pyproj`, `shapely`, `geopandas`, `xarray`, `pycolmap`._

**Quando considerar**

- ler ortofoto e MDS em GeoTIFF como arrays NumPy, com a transformação afim (pixel para UTM) e o CRS
- amostrar o valor do MDS em pontos de uma rede ou de um perfil (sample)
- recortar a ortofoto por polígono (mask) ou por janela, sem carregar o arquivo inteiro
- reprojetar ou reamostrar um raster (warp)

**Quando evitar**

- imagens sem georreferenciamento; PIL ou OpenCV bastam
- rasters multidimensionais em NetCDF ou Zarr; considerar xarray
- quando não se pode depender da GDAL (embarcada nas rodas binárias, mas pesada)

**Cuidados**

- a transformação afim (transform) leva (coluna, linha) para (x, y); a linha cresce para o sul, então a altura do pixel costuma ser negativa
- o valor nodata deve ser lido do arquivo e mascarado; tratá-lo como altitude real contamina volumes e perfis
- ler em janelas (Window) para ortofotos grandes; ler tudo de uma vez pode estourar a RAM
- o CRS do arquivo pode estar ausente ou errado; conferir contra o esperado (por exemplo UTM SIRGAS 2000) antes de usar
- bandas uint8 (RGB) e float32 (MDS) têm tratamento diferente; não misturar na média
- a reamostragem (nearest, bilinear, cubic) altera valores; escolher e registrar o método
- a GDAL embarcada na roda pode diferir da do sistema; registrar a versão para reprodutibilidade

Repositório: <https://github.com/rasterio/rasterio>

### Shapely

Geometrias planas (pontos, linhas, polígonos) e operações geométricas, sobre a biblioteca GEOS.

_Coopera com `pyproj`, `geopandas`, `numpy`, `rasterio`, `ezdxf`._

**Quando considerar**

- área, comprimento, interseção, união, buffer e distância de polígonos e polilinhas em coordenadas métricas (UTM)
- recortar trechos de rede (obra linear) por polígono de lote ou de pavimento
- operações vetorizadas sobre arrays de geometrias (Shapely 2.x), em vez de laços Python
- índice espacial (STRtree) para consultas de vizinhança entre muitas geometrias

**Quando evitar**

- quando as coordenadas estão em graus (SIRGAS 2000 geográfico) e a medida deve ser em metros; projetar para UTM antes
- quando é preciso 3D de verdade (volumes, interseção de sólidos); a biblioteca é essencialmente 2D
- quando a tabela de atributos é o foco; usar geopandas, que embrulha o Shapely

**Cuidados**

- a ordem das coordenadas é (x, y), isto é, (leste, norte) ou (longitude, latitude); misturar com (latitude, longitude) inverte o ponto
- não conhece sistema de coordenadas; guardar o EPSG ao lado (geopandas ou pyproj) e nunca medir área ou comprimento em graus
- a coordenada Z é carregada, mas as operações (área, distância, interseção) a ignoram
- polígonos inválidos (autointerseção, anel aberto) dão resultado errado ou erro; checar is_valid e corrigir com make_valid
- coordenadas UTM têm 6 a 7 dígitos; comparar com tolerância absoluta declarada, não com igualdade exata
- set_precision altera a geometria; usar de forma explícita
- {'determinismo': 'a mesma versão do GEOS dá o mesmo resultado; versões diferentes podem divergir em casos de borda'}

Repositório: <https://github.com/shapely/shapely>

## CAD, BIM e 3D

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [ezdxf](https://ezdxf.readthedocs.io) | candidato | MIT | 1.4.5 (2026-10) | 2026-11-02 |
| [IfcOpenShell](https://docs.ifcopenshell.org) | candidato | LGPL-3.0-or-later | 0.9.0.post1 (2026-10) | 2026-11-02 |
| [Open3D](https://www.open3d.org/docs) | candidato | MIT | 0.20.0 (2026-09) | 2026-11-02 |
| [pycolmap](https://colmap.github.io/) | em uso | BSD-3-Clause | 4.2.1 (2026-09) | 2026-11-02 |

### ezdxf

Leitura, criação e edição de arquivos DXF (CAD 2D e 3D) em Python, sem depender do AutoCAD.

_Coopera com `shapely`, `pymupdf`, `ifcopenshell`, `pyproj`._

**Quando considerar**

- extrair linhas, polilinhas, blocos, textos e camadas (layers) de pranchas exportadas em DXF
- gerar um DXF com a rede projetada (polilinhas por camada) para abrir no CAD
- ler o desenho por nome de camada, para ligar elementos a conceitos (rede de esgoto, tubo, estaca)

**Quando evitar**

- arquivos DWG, formato proprietário; converter antes para DXF (por exemplo com o ODA File Converter, que o ezdxf pode chamar em ezdxf.addons.odafc)
- pranchas em PDF vetorial; usar pymupdf para extrair os caminhos
- modelo BIM com semântica de objetos; usar IFC

**Cuidados**

- DWG não é lido diretamente; a conversão externa é uma etapa a mais e deve ser registrada na proveniência
- o DXF não guarda CRS de forma confiável; as coordenadas podem estar em UTM, em coordenadas locais ou em unidades de desenho; confirmar e registrar a unidade (INSUNITS)
- polilinhas com arco (bulge), splines e hatches precisam ser achatadas para virar geometria Shapely; declarar a tolerância do achatamento
- blocos (INSERT) trazem escala, rotação e ponto de inserção; expandir com virtual_entities em vez de tratar como ponto
- entidades extrudadas usam o OCS e o desenho pode usar UCS; aplicar a extrusão ao ler, senão o sentido do eixo pode ficar invertido
- arquivos corrompidos ou gerados por outros softwares podem exigir ezdxf.recover
- o DXF guarda coordenadas como texto em ponto flutuante; confirmar a precisão ao exportar coordenadas UTM de 6 a 7 dígitos

Repositório: <https://github.com/mozman/ezdxf>

### IfcOpenShell

Biblioteca para ler, criar e editar modelos IFC (BIM), com geometria e propriedades dos objetos.

_Coopera com `ezdxf`, `open3d`, `shapely`, `pandas`._

**Quando considerar**

- ler modelo BIM em IFC (paredes, tubos, equipamentos) com propriedades e quantitativos
- extrair a geometria 3D dos elementos para cruzar com a nuvem de pontos ou com a rede
- gerar IFC de saída a partir de dados calculados (por exemplo trechos de rede com diâmetro e cota)
- consultar a posição georreferenciada do modelo (IfcMapConversion e IfcProjectedCRS, no IFC4)

**Quando evitar**

- desenho CAD 2D sem semântica; usar ezdxf
- quando só se precisa de nuvem de pontos ou malha; usar open3d
- distribuição de software fechado sem avaliar a obrigação da LGPL

**Cuidados**

- licença LGPL-3.0-or-later nas bibliotecas principais; componentes como o Bonsai usam GPL-3.0-or-later; verificar a compatibilidade antes de distribuir
- o IFC costuma estar em coordenadas locais do projeto; a conversão para UTM depende de IfcMapConversion, que pode estar ausente ou errada
- coordenadas de 6 a 7 dígitos podem perder precisão na geometria processada; trabalhar com origem deslocada e somar o deslocamento depois
- as unidades do modelo (milímetro, metro) vêm de IfcUnitAssignment; converter para SI explicitamente
- esquemas suportados na leitura são IFC2x3, IFC4, IFC4x1, IFC4x2 e IFC4x3; a geometria cobre menos esquemas que a leitura (IFC2x3 e IFC4)
- o pacote tem dependência nativa (geometria) e restrição de versão do Python (de 3.10 a 3.15 na roda 0.9.0.post1)
- a API de alto nível (ifcopenshell.api) evolui entre versões; fixar a versão

Repositório: <https://github.com/ifcopenshell/ifcopenshell>

### Open3D

Biblioteca de processamento 3D para nuvens de pontos, malhas, registro (ICP) e reconstrução de superfícies.

_Coopera com `numpy`, `pycolmap`, `rasterio`, `ifcopenshell`, `shapely`._

**Quando considerar**

- filtrar, reduzir (voxel downsample), remover ruído e estimar normais da nuvem de pontos do SfM
- alinhar duas nuvens, ou a nuvem a pontos de controle, com ICP
- reconstruir malha (Poisson, ball pivoting) a partir da nuvem densa
- visualizar nuvem e malha de forma interativa durante a depuração

**Quando evitar**

- cálculo de MDS raster; usar rasterio e numpy sobre a nuvem
- modelo BIM com semântica; usar IFC
- nuvens muito grandes sem tratamento por blocos

**Cuidados**

- coordenadas UTM de 6 a 7 dígitos em float32 perdem precisão; subtrair uma origem local, trabalhar em float64 e somar a origem ao salvar
- o ICP depende da posição inicial e da distância máxima de correspondência; pode convergir para mínimo local; conferir o resultado contra pontos de controle
- voxel downsample e estimativa de normais mudam o resultado; registrar os parâmetros
- parte das operações tem versão em GPU (CUDA) que exige roda e hardware específicos; a CPU é mais previsível
- paralelismo e amostragem aleatória podem alterar o resultado entre execuções; fixar semente e checar determinismo
- o suporte a versões novas do Python costuma atrasar; conferir os requisitos da roda antes de atualizar
- a janela de visualização exige ambiente gráfico; em servidor, exportar ou renderizar fora da tela

Repositório: <https://github.com/isl-org/Open3D>

### pycolmap

Ligações Python do COLMAP para estrutura a partir de movimento (SfM) e estéreo multivista, a partir de fotos.

_Coopera com `open3d`, `rasterio`, `numpy`, `pyproj`._

**Quando considerar**

- reconstruir poses de câmera e nuvem esparsa a partir de fotos de drone (nadirais e oblíquas)
- rodar extração de características, correspondência e mapeamento incremental em CPU
- obter o ajuste de feixes (bundle adjustment) e usar o resultado para gerar MDS e ortofoto
- reaproveitar o GPS do EXIF de fotos DJI como posição aproximada das câmeras

**Quando evitar**

- quando já há fluxo fotogramétrico fechado com pontos de controle de campo e exigência formal de precisão; usar software dedicado
- quando a densificação estéreo é essencial e não há GPU NVIDIA
- quando a reconstrução precisa ser idêntica bit a bit entre máquinas

**Cuidados**

- o SfM entrega modelo com escala e orientação arbitrárias; georreferenciar com GPS do EXIF ou pontos de controle (transformação de similaridade) antes de usar em UTM
- o GPS do EXIF de drone tem erro de metros; sem pontos de controle, a precisão absoluta é limitada, mesmo que a relativa seja boa
- o repositório do COLMAP oferece o pacote separado pycolmap-cuda12 com rodas CUDA; o pacote pycolmap comum é o caminho para CPU, e passos que exigem CUDA (como a densificação) devem ser confirmados na documentação antes de planejar o fluxo
- threads e RANSAC podem variar entre execuções; fixar semente e número de threads, e comparar com tolerância em vez de bytes
- misturar fotos oblíquas e nadirais exige cuidado na correspondência; o modelo de câmera e a calibração afetam a deformação (prédio torto)
- a licença do COLMAP é BSD-3-Clause, mas dependências de terceiros têm licenças próprias
- memória e tempo crescem com o número de fotos e a resolução; reduzir o tamanho máximo da imagem em testes

Repositório: <https://github.com/colmap/colmap>

## Grafos

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [NetworkX](https://networkx.org/documentation/stable/) | candidato | BSD-3-Clause | 3.7 (2026-09) | 2026-11-02 |
| [python-igraph](https://python.igraph.org) | candidato | GPL-2.0 | 1.0.0 (2025-10) | 2026-11-02 |
| [rustworkx](https://www.rustworkx.org/) | candidato | Apache-2.0 | 0.18.1 (2026-07) | 2026-11-02 |

### NetworkX

Biblioteca de grafos em Python puro, com grande conjunto de algoritmos e API flexível.

_Compete com `rustworkx`, `igraph`; coopera com `numpy`, `pandas`, `geopandas`, `shapely`, `rustworkx`._

**Quando considerar**

- prototipar algoritmos de grafos
- grafos de tamanho moderado
- atributos arbitrários em nós e arestas
- rede de água ou esgoto como grafo dirigido (trechos como arestas, poços de visita como nós), com caminho de jusante, componentes conectados e ordenação topológica
- nós identificados por rótulos de domínio (código do poço de visita, nome do trecho), sem mapeamento para índices
- integrar com geopandas e shapely, em que cada aresta carrega geometria e comprimento_m

**Quando evitar**

- grafos muito grandes em que o tempo de execução é o fator limitante
- fluxo de trabalho que exige determinismo estrito sem tratar a ordem de iteração
- algoritmos de grafos que não existem na biblioteca e exigem núcleo nativo

**Cuidados**

- a implementação em Python é mais lenta que a de bibliotecas com núcleo nativo
- a ordem de iteração segue a ordem de inserção; fixá-la para resultados reproduzíveis
- em redes de esgoto, o sentido da aresta deve seguir o escoamento por gravidade (montante para jusante); usar DiGraph e conferir ciclos com is_directed_acyclic_graph
- grafos multi-aresta (MultiGraph, MultiDiGraph) são necessários quando há trechos paralelos entre os mesmos nós
- pesos de aresta com unidade no nome (comprimento_m); o algoritmo de caminho mínimo usa o atributo indicado em weight, e o padrão é peso 1 por aresta
- alguns algoritmos têm desempate arbitrário (caminhos de mesmo custo); não depender de um caminho específico sem fixar o critério
- a série 3.x requer versão recente do Python (>=3.12 na versão 3.7); fixar a versão do pacote

Repositório: <https://github.com/networkx/networkx>

### python-igraph

Interface Python para a biblioteca igraph em C, com algoritmos de grafos e análise de redes.

_Compete com `networkx`, `rustworkx`; coopera com `numpy`, `pandas`._

**Quando considerar**

- análise de redes grandes com algoritmos nativos (centralidade, comunidades, caminhos mínimos)
- nós identificados por índices inteiros e atributos guardados em vetores
- comparação de desempenho e de resultados com NetworkX e rustworkx em uma tese de benchmark

**Quando evitar**

- quando a licença GPL é incompatível com a distribuição do projeto
- quando se quer a API mais flexível, com nós por rótulo de domínio; NetworkX é mais direto
- ecossistema de integração com geopandas, em que NetworkX tem mais exemplos

**Cuidados**

- licença GPL (o repositório indica GPL-2.0; a cláusula "ou posterior" não foi verificada em 2026-11-02); avaliar o efeito sobre a distribuição antes de adotar
- os nós são índices inteiros de 0 a n-1; reindexados quando vértices são removidos, o que invalida os índices guardados
- o nome do pacote no PyPI é igraph, enquanto o repositório se chama python-igraph; instalar pelo nome do PyPI
- dependência nativa (biblioteca C); usar rodas binárias e registrar a versão
- grafos dirigidos exigem o argumento directed explícito em vários métodos; conferir o padrão de cada função
- determinismo de algoritmos aleatórios (por exemplo comunidades) exige fixar a semente do módulo random

Repositório: <https://github.com/igraph/python-igraph>

### rustworkx

Biblioteca de grafos com núcleo em Rust e API em Python, originada no projeto Qiskit.

_Compete com `networkx`, `igraph`; coopera com `numpy`, `pandas`, `networkx`._

**Quando considerar**

- grafos grandes
- algoritmos de grafos com execução em código nativo
- redes com muitos trechos em que a lentidão do Python puro se torna o gargalo medido
- cargas de trabalho que se beneficiam de índices inteiros contíguos e de arrays NumPy

**Quando evitar**

- quando os nós precisam ser identificados diretamente por rótulos de domínio
- quando é preciso o ecossistema mais amplo de algoritmos do NetworkX
- redes pequenas, em que a diferença de tempo não compensa a conversão de índices

**Cuidados**

- os nós são referenciados por índices inteiros; mapear os identificadores de domínio para esses índices
- ao remover nós, os índices livres podem ser reaproveitados; não guardar índices antigos como identificador estável
- a API é parecida com a do NetworkX, mas não idêntica; funções de mesmo nome podem ter assinatura ou retorno diferentes
- há ponte de conversão para NetworkX, mas ela custa tempo e perde detalhes de atributos; testar o caminho de ida e volta
- o desempenho só deve ser afirmado com medição própria (tese de benchmark), não por suposição

Repositório: <https://github.com/Qiskit/rustworkx>

## Intercâmbio de dados

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [JSON-LD](https://json-ld.org/) | candidato | BSD-3-Clause | 3.3.0 (2026-09) | 2026-11-02 |
| [RDFLib](https://rdflib.readthedocs.org/) | candidato | BSD-3-Clause | 7.6.0 (2026-02) | 2026-11-02 |

### JSON-LD

Formato de dados ligados em JSON, em que um contexto associa termos a identificadores globais (IRIs).

_Coopera com `rdflib`, `pydantic`._

**Quando considerar**

- intercambiar dados semânticos com vocabulário compartilhado
- publicar metadados vinculados a outros conjuntos de dados
- descrever o projeto, as camadas e os arquivos com identificadores estáveis e vocabulário explícito
- manter um JSON legível por pessoas que também possa ser lido como grafo RDF

**Quando evitar**

- troca interna simples, em que um JSON comum basta
- tabelas grandes de dados numéricos; usar parquet

**Cuidados**

- a expansão de contexto pode buscar URLs remotos; usar carregador local e controlado
- o pacote Python é pyld; a leitura de JSON-LD em grafo RDF também é possível com rdflib
- o resultado da canonicalização (URDNA2015) é determinístico, mas deve ser usado quando se quer comparar bytes ou assinar
- coordenadas e unidades precisam de termos explícitos no contexto (por exemplo, o EPSG e a unidade no nome); sem isso, o número perde significado
- para dados geográficos, GeoJSON é mais adequado como formato de geometria; o JSON-LD pode apenas descrevê-lo

Repositório: <https://github.com/digitalbazaar/pyld>

### RDFLib

Biblioteca Python para trabalhar com RDF, com leitura e escrita em vários formatos e consultas SPARQL.

_Coopera com `json-ld`, `pydantic`, `networkx`._

**Quando considerar**

- montar um grafo de conhecimento do projeto (obra, camadas, pranchas, arquivos) e consultá-lo com SPARQL
- ler e gravar RDF em Turtle, N-Triples, RDF/XML e JSON-LD
- ligar elementos da obra a vocabulários externos (por exemplo, o ifcOWL para IFC)

**Quando evitar**

- dados tabulares ou numéricos; usar pandas, polars ou parquet
- troca interna simples, em que um JSON comum basta
- grafos de tamanho grande com alto desempenho, pois a biblioteca guarda os dados em memória

**Cuidados**

- o armazenamento padrão é em memória; para volumes maiores é preciso um backend de armazenamento
- literais numéricos precisam de tipo explícito (XSD) e a unidade deve constar no vocabulário, senão o valor perde significado
- a ordem de serialização pode variar; para comparar bytes, usar a canonicalização (rdflib.compare) ou ordenar
- consultas SPARQL mal formadas retornam resultados vazios sem erro óbvio; testar com dados pequenos
- carregar contextos JSON-LD ou ontologias remotas pode acessar a rede; preferir cópias locais
- fixar a versão do pacote; a API de plugins de formato e de armazenamento muda entre versões principais

Repositório: <https://github.com/RDFLib/rdflib>

## Documentos e OCR

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [Docling](https://docling-project.github.io/docling/) | candidato | MIT | 2.145.0 (2026-10) | 2026-11-02 |
| [PaddleOCR](https://github.com/PaddlePaddle/PaddleOCR/blob/main/README.md) | candidato | Apache-2.0 | 3.7.0 (2026-06) | 2026-11-02 |
| [pdfplumber](https://github.com/jsvine/pdfplumber#readme) | candidato | MIT | 0.11.10 (2026-06) | 2026-11-02 |
| [PyMuPDF](https://pymupdf.readthedocs.io/) | em uso | AGPL-3.0-only | 2.0 (2026-10) | 2026-11-02 |
| [pytesseract](https://github.com/madmaze/pytesseract#readme) | em uso | Apache-2.0 | 0.3.13 (2024-08) | 2026-11-02 |

### Docling

Conversão de documentos (PDF, imagens, Office) em estrutura com layout, tabelas e ordem de leitura, usando modelos de análise de layout.

_Compete com `pymupdf`, `pdfplumber`; coopera com `pymupdf`, `pytesseract`, `paddleocr`, `pandas`._

**Quando considerar**

- documentos de texto corrido com tabelas (memoriais, especificações, relatórios), em que a ordem de leitura e a estrutura de tabelas importam
- PDF misto, com partes escaneadas, convertido em um único modelo de documento exportável para Markdown ou JSON
- comparar com pymupdf e pdfplumber a extração de tabelas que eles erram

**Quando evitar**

- {'pranchas de desenho técnico': 'o modelo de layout foi pensado para documentos, não para desenho CAD com cotas e hachuras'}
- ambiente sem rede ou sem espaço para baixar modelos
- quando é preciso resultado byte a byte idêntico e coordenadas exatas de traços

**Cuidados**

- licença MIT do pacote conforme o PyPI; os modelos baixados têm licenças próprias, conferir cada um antes de distribuir
- baixa pesos de modelos de repositórios externos na primeira execução; fixar o diretório de artefatos para uso offline
- dependência pesada (PyTorch e outros); em CPU é lento, a GPU acelera mas exige instalação própria
- o OCR é delegado a motores configuráveis (por exemplo Tesseract, EasyOCR, RapidOCR); configurar o idioma português explicitamente
- o determinismo depende da versão dos modelos e do hardware; registrar versões e comparar saídas em teste antes de adotar
- lançamentos muito frequentes (2.145.0 em 2026-10); fixar a versão

Repositório: <https://github.com/docling-project/docling>

### PaddleOCR

OCR por redes neurais (detecção e reconhecimento de texto) do ecossistema PaddlePaddle, com suporte a vários idiomas.

_Compete com `pytesseract`; coopera com `pymupdf`, `pdfplumber`, `docling`, `numpy`._

**Quando considerar**

- {'texto escaneado em que o Tesseract falha': 'fundo ruidoso, texto inclinado ou girado, fontes irregulares'}
- comparar com pytesseract nas mesmas regiões de carimbo e tabelas de uma amostra de pranchas reais, medindo o acerto contra valores conferidos à mão
- há GPU disponível, ou a quantidade de páginas compensa o custo de instalação

**Quando evitar**

- texto vetorial extraível direto do PDF
- {'ambiente enxuto ou de CI leve': 'a dependência é grande'}
- quando o resultado precisa ser idêntico entre máquinas diferentes sem validação

**Cuidados**

- licença Apache-2.0 conforme o PyPI; os modelos de cada idioma têm origem e termos próprios, conferir antes de distribuir
- exige também o framework PaddlePaddle, instalado em separado, com variantes para CPU e GPU; a instalação costuma ser a parte difícil
- baixa modelos na primeira execução; para uso offline fixar o diretório dos modelos
- para português usa-se o modelo de alfabeto latino; confirmar na amostra o reconhecimento de acentos e cedilha
- o resultado pode variar com a versão do modelo, o hardware e a GPU; registrar versões e validar em Python os números lidos
- a API mudou entre as séries 2.x e 3.x; fixar a versão (3.7.0 em 2026-06)

Repositório: <https://github.com/PaddlePaddle/PaddleOCR>

### pdfplumber

Extração de texto, linhas, retângulos e tabelas de PDF com camada de texto, construída sobre pdfminer.six.

_Compete com `pymupdf`, `docling`; coopera com `pymupdf`, `pandas`, `polars`, `pytesseract`, `paddleocr`._

**Quando considerar**

- tabelas de materiais e quantitativos em PDF vetorial, com extract_table e extract_tables ajustando as estratégias de linha (lines) ou de texto (text)
- depurar visualmente a detecção de tabela (page.to_image com debug_tablefinder) antes de confiar nos números
- recortar uma região (crop) da prancha, como o carimbo, e extrair só dali
- precisar de licença permissiva (MIT) em ferramenta que será distribuída

**Quando evitar**

- {'PDF escaneado': 'não há texto a extrair, só imagem'}
- pranchas grandes com muitos traços de desenho, em que o processamento é lento
- quando a velocidade e a leitura de layers do CAD são o foco (pymupdf)

**Cuidados**

- licença MIT conforme classificação do PyPI; o pdfminer.six é dependência
- as configurações de tabela (table_settings) mudam o resultado; congelá-las no código e testar com tabelas reais
- células mescladas e tabelas sem bordas costumam sair truncadas ou deslocadas; conferir a contagem de linhas contra o esperado
- o texto sai como cadeias de caracteres; números no formato brasileiro (vírgula decimal, ponto de milhar) são convertidos em Python, com teste
- mesmo arquivo, mesma versão e mesmas configurações dão o mesmo resultado

Repositório: <https://github.com/jsvine/pdfplumber>

### PyMuPDF

Leitura rápida de PDF vetorial e escaneado (textos com posição, traços, imagens, layers) sobre a biblioteca MuPDF.

_Compete com `pdfplumber`, `docling`; coopera com `pdfplumber`, `pytesseract`, `paddleocr`, `docling`, `shapely`, `numpy`, `pandas`, `polars`._

**Quando considerar**

- prancha de projeto em PDF vetorial exportada de CAD, em que se quer textos com posição (get_text com blocos e spans), traços (get_drawings) e a camada (layer/OCG) de cada elemento
- carimbo e legendas em coordenadas conhecidas da página, recortando por retângulo para ler só a região do carimbo
- extrair imagens embutidas ou renderizar a página em pixmap com resolução controlada para entregar ao OCR
- páginas grandes (formatos A1/A0) em que a velocidade e o baixo uso de memória importam

**Quando evitar**

- distribuição de software fechado ou serviço em rede sem avaliar a licença AGPL ou contratar a licença comercial
- tabelas com bordas implícitas em que a reconstrução de linhas e colunas é o problema principal (pdfplumber ou docling tratam melhor)
- PDF escaneado sem camada de texto, em que só há imagem; é preciso OCR (pytesseract ou paddleocr) depois da renderização

**Cuidados**

- {'LICENÇA': 'dupla, GNU AGPL 3.0 ou licença comercial da Artifex. Uso interno e pesquisa é simples; distribuir ou oferecer como serviço em rede exige abrir o código derivado ou comprar a licença comercial. Decisão de licenciamento é do mantenedor.'}
- o texto vetorial de CAD costuma vir quebrado em spans por fonte e por caractere; agrupar por proximidade em Python antes de interpretar
- as coordenadas são em pontos tipográficos (1/72 pol) com origem no canto superior esquerdo; converter para mm uma vez, na entrada, e carregar o sufixo no nome
- nome de layer só existe se o PDF preservou os grupos de conteúdo opcionais (OCG); conferir em cada exportação de CAD
- versão major 2.0 recente (2026-10) pode ter mudado API; fixar a versão no lockfile e rodar os testes de extração
- para o mesmo arquivo e a mesma versão a extração é determinística; registrar a versão junto do resultado

Repositório: <https://github.com/pymupdf/pymupdf>

### pytesseract

Interface Python para o motor de OCR Tesseract, que lê texto de imagens e devolve também posição e confiança por palavra.

_Compete com `paddleocr`; coopera com `pymupdf`, `pdfplumber`, `paddleocr`, `docling`, `numpy`._

**Quando considerar**

- prancha escaneada ou texto rasterizado sem camada de texto, depois de renderizar a página em imagem (por exemplo com pymupdf)
- ler o carimbo e tabelas por região recortada, com image_to_data para obter caixa e confiança de cada palavra
- texto em português, com os dados de idioma (traineddata "por") instalados
- conferência cruzada de um valor lido do vetor contra o mesmo valor lido por OCR

**Quando evitar**

- texto vetorial do CAD, que se extrai exato direto do PDF sem OCR
- tabelas complexas ou texto girado sobre desenho denso, em que o Tesseract perde muito; avaliar paddleocr
- cotas pequenas em desenho, sem pré-processamento

**Cuidados**

- {'o pytesseract é apenas o invólucro': 'o programa Tesseract precisa estar instalado no sistema (apt, brew ou instalador no Windows) e o idioma português baixado em separado'}
- licença Apache-2.0 do invólucro conforme o PyPI; a licença do Tesseract em si não foi verificada em 2026-11-02, conferir na distribuição usada
- última versão publicada 0.3.13 em 2024-08, ritmo de manutenção baixo; acompanhar o repositório
- o resultado depende da resolução, do contraste e do modo de segmentação (psm); fixar os parâmetros e a resolução de renderização no código
- para o mesmo binário, a mesma imagem e os mesmos parâmetros espera-se a mesma saída; registrar a versão do Tesseract
- confusões típicas entre 0/O, 1/l e vírgula/ponto em números exigem validação em Python (formato, faixa, soma)
- cada chamada abre um subprocesso, o que pesa em muitas regiões pequenas

Repositório: <https://github.com/madmaze/pytesseract>

## Apresentação

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [Jinja2](https://jinja.palletsprojects.com/) | em uso | BSD-3-Clause | 3.1.6 (2025-03) | 2026-11-02 |
| [Matplotlib](https://matplotlib.org/stable/) | candidato | LicenseRef-Matplotlib | 3.11.2 (2026-09) | 2026-11-02 |
| [Plotly](https://plotly.com/python/) | em uso | MIT | 7.1.0 (2026-09) | 2026-11-02 |

### Jinja2

Motor de templates para gerar texto e HTML a partir de dados já calculados em Python.

_Coopera com `plotly`, `matplotlib`._

**Quando considerar**

- montar relatórios HTML com laços e blocos reutilizáveis
- {'separar apresentação do cálculo': 'o template recebe valores prontos, já formatados com unidade'}
- herança de templates para manter o mesmo cabeçalho e estilo em vários relatórios

**Quando evitar**

- lógica de negócio dentro do template
- cálculo, soma ou conversão de unidade no template, o que viola a regra de que o HTML só apresenta

**Cuidados**

- o autoescape vem desligado por padrão no Environment; ligá-lo para HTML
- usar StrictUndefined para que variável ausente falhe em vez de sair vazia no relatório
- a formatação de número com vírgula decimal (padrão brasileiro) deve ser feita em Python, antes do template
- licença BSD-3-Clause segundo o repositório da Pallets; o PyPI traz só a classificação BSD, o identificador SPDX exato não foi verificado em 2026-11-02

Repositório: <https://github.com/pallets/jinja>

### Matplotlib

Figuras estáticas (PNG, SVG, PDF) geradas em Python, com controle fino de eixos, escala e anotações.

_Compete com `plotly`; coopera com `numpy`, `pandas`, `polars`, `jinja2`, `shapely`._

**Quando considerar**

- figuras estáticas para relatório impresso ou PDF, inclusive em SVG vetorial
- desenhos técnicos simples com escala igual nos eixos (aspect equal), como planta de trechos ou perfil
- imagens embutidas no HTML (SVG ou PNG em base64) quando não se quer JavaScript no relatório, coerente com a regra de que o HTML só apresenta
- figuras reproduzíveis em CI, sem navegador

**Quando evitar**

- gráficos que o leitor precisa explorar com zoom e passagem do mouse (plotly)
- painéis com muitos elementos interativos

**Cuidados**

- em servidor ou CI usar o backend não interativo (Agg) para não depender de tela
- licença própria baseada na PSF (classificação PSF no PyPI), permissiva; o identificador SPDX exato não foi verificado em 2026-11-02, por isso o campo usa LicenseRef
- a saída em PNG pode variar levemente entre versões e fontes do sistema; fixar a versão e a fonte para comparar imagens em teste
- rótulos e unidades dos eixos vêm de variáveis com sufixo de unidade; texto em português com acentos exige fonte que os tenha
- o cálculo é feito antes, em Python; a figura só desenha valores prontos

Repositório: <https://github.com/matplotlib/matplotlib>

### Plotly

Gráficos interativos gerados em Python e renderizados no navegador pelo Plotly.js.

_Compete com `matplotlib`; coopera com `jinja2`, `numpy`, `pandas`, `polars`, `matplotlib`._

**Quando considerar**

- gráficos interativos (zoom, passagem do mouse) em HTML autocontido
- receber DataFrames de pandas e Polars
- mostrar séries e perfis já calculados em Python, deixando ao navegador só o desenho

**Quando evitar**

- figuras estáticas para publicação impressa, em que uma ferramenta de figura estática é mais simples (matplotlib)
- desenho técnico com escala rigorosa e muitos elementos geométricos

**Cuidados**

- {'o HTML gerado inclui JavaScript; o JavaScript só exibe valores já calculados (regra do mantenedor': 'Python calcula, HTML/JS só apresenta)'}
- o HTML autocontido carrega a biblioteca Plotly.js inteira (vários MB) em cada arquivo, a menos que se use CDN, que exige rede
- licença MIT conforme o PyPI
- não usar agregações ou transformações feitas no navegador; entregar a figura com os números prontos e unidades nos rótulos

Repositório: <https://github.com/plotly/plotly.py>

## Qualidade e testes

| Ferramenta | Situação | Licença | Última versão | Verificado em |
|---|---|---|---|---|
| [Hypothesis](https://hypothesis.readthedocs.io/) | candidato | MPL-2.0 | 6.170.14 (2026-10) | 2026-11-02 |
| [mutmut](https://mutmut.readthedocs.io/) | candidato | BSD-3-Clause | 3.8.1 (2026-10) | 2026-11-02 |
| [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) | candidato | BSD-2-Clause | 5.3.1 (2026-11) | 2026-11-02 |

### Hypothesis

Testes baseados em propriedades, que geram entradas variadas e reduzem o caso que falha ao menor exemplo.

_Coopera com `numpy`, `pandas`, `pydantic`, `pint`, `pytest-benchmark`._

**Quando considerar**

- {'funções de cálculo com propriedades claras': 'conversão de unidade que volta ao valor original, resultado não negativo, monotonicidade, invariância por translação de coordenadas'}
- leitores de texto (números em formato brasileiro, códigos de prancha), em que entradas estranhas escapam de testes por exemplo
- casos de borda em geometria (polígonos degenerados, áreas nulas) com estratégias que geram coordenadas

**Quando evitar**

- funções cujo resultado esperado só se conhece por tabela de gabarito; usar teste por exemplo
- código lento por chamada, em que centenas de execuções pesam

**Cuidados**

- licença MPL-2.0 (copyleft por arquivo) conforme o PyPI; afeta só modificações nos arquivos do próprio Hypothesis
- a geração é aleatória; para CI reproduzível usar perfil com derandomize ou fixar a semente, e guardar os exemplos que falharam
- cria o diretório .hypothesis com a base de exemplos; avaliar o .gitignore
- estratégias de float precisam restringir faixa e excluir NaN e infinito quando o domínio físico os proíbe, senão o teste acusa falsos erros
- o limite de tempo por exemplo (deadline) pode dar falha intermitente em máquina lenta

Repositório: <https://github.com/HypothesisWorks/hypothesis>

### mutmut

Teste de mutação, que altera o código de forma controlada e verifica se os testes percebem; mutantes que sobrevivem apontam testes fracos.

_Coopera com `hypothesis`, `pytest-benchmark`._

**Quando considerar**

- avaliar se os testes de uma função de cálculo criada por agente realmente detectam erro, além de a cobertura de linhas ser alta
- módulos pequenos e críticos (fórmulas hidráulicas, geometria), com testes rápidos
- complementar a cobertura no balanço de qualidade

**Quando evitar**

- {'suíte lenta ou código grande': 'cada mutante roda os testes de novo'}
- código sem testes automáticos, em que tudo sobrevive

**Cuidados**

- licença BSD-3-Clause conforme o PyPI
- é preciso configurar quais caminhos mutar; suporte a Windows não foi verificado em 2026-11-02 (conferir a documentação da versão usada)
- mutantes equivalentes (que não mudam o comportamento) sobrevivem sem indicar teste fraco; exige leitura humana
- o tempo total cresce com o número de mutantes; limitar a módulos e rodar fora do CI de cada commit
- guarda resultados em diretório local; avaliar o .gitignore
- em testes numéricos, tolerância larga demais deixa sobreviver mutantes pequenos; é um sinal útil, não um defeito

Repositório: <https://github.com/boxed/mutmut>

### pytest-benchmark

Plugin do pytest que mede o tempo de execução de trechos de código por teste, com estatísticas e comparação entre execuções.

_Coopera com `hypothesis`, `numpy`, `pandas`, `polars`._

**Quando considerar**

- medir o tempo por função crítica a cada iteração e comparar com a execução salva (--benchmark-compare), alimentando o balanço antes e depois
- decidir entre implementações (por exemplo laço contra NumPy vetorizado) com a mesma entrada
- detectar regressão de tempo no CI com limite declarado (--benchmark-compare-fail)

**Quando evitar**

- medir pipeline de ponta a ponta com disco e rede, em que a variação é grande
- máquinas compartilhadas e ruidosas sem repetição suficiente

**Cuidados**

- licença BSD-2-Clause conforme o PyPI
- o tempo depende da máquina e da carga; comparar só resultados do mesmo ambiente e registrar o ambiente
- o plugin repete a função até estabilizar; funções com efeito colateral ou cache precisam de preparação a cada rodada (modo pedantic)
- salva resultados em .benchmarks; decidir se entram no repositório
- não mede memória
- em execução paralela de testes os tempos ficam instáveis; desligar o benchmark nesse modo

Repositório: <https://github.com/ionelmc/pytest-benchmark>
