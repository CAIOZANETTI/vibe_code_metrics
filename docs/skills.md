# Skills

> As ferramentas dizem **com o que** calcular; as skills dizem **como o agente conduz**
> uma tarefa: o passo a passo, quem executa e os cuidados. Cada skill aponta as
> ferramentas do [repertório](repertorio.md) que usa.
> Página gerada a partir de `repertorio/skills/` por `vcm docs`; edite os YAML.

## Como as skills funcionam

Verificado em 2026-11-02 nas fontes citadas. O que não foi confirmado está marcado [não verificado].

### O que é uma skill
- Pasta com um `SKILL.md`: frontmatter YAML entre `---` + instruções em markdown. Pode ter arquivos de apoio (`reference.md`, `examples.md`, `scripts/`). Fonte: https://code.claude.com/docs/en/skills (2026-11-02).
- Frontmatter na plataforma: `name` (até 64 caracteres; só minúsculas, números e hífen; sem as palavras reservadas `anthropic` e `claude`) e `description` (não vazia, até 1.024 caracteres) são exigidos. Fonte: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview (2026-11-02).
- No Claude Code todos os campos são opcionais (só `description` é recomendado); `name` padrão é o nome da pasta. Outros campos: `when_to_use`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context: fork`, `model`, `paths`, `license`. Campos desconhecidos são ignorados sem erro. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- A descrição combinada (`description` + `when_to_use`) é truncada em 1.536 caracteres na listagem: colocar o caso de uso principal no começo. Fonte: idem.
- Carregamento progressivo: nível 1, só nome e descrição (cerca de 100 tokens por skill) ficam sempre no contexto; nível 2, o corpo do `SKILL.md` entra quando a descrição casa com o pedido; nível 3, arquivos de apoio são lidos só se necessários e scripts rodam via bash, entrando no contexto apenas a saída. Fonte: platform.claude.com/.../agent-skills/overview (2026-11-02).
- Depois de carregada, a skill permanece no contexto nos turnos seguintes; por isso, corpo curto (menos de 500 linhas). Também pode ser chamada direto com `/nome-da-skill`. Fonte: code.claude.com/docs/en/skills (2026-11-02).

### Onde ficam (Claude Code)
- Pessoal: `~/.claude/skills/<skill>/SKILL.md` (todos os projetos da máquina).
- Projeto: `.claude/skills/<skill>/SKILL.md` (versionado no repositório; vale para quem clonar).
- Também: corporativa (managed settings), aninhada em subpastas, `--add-dir` e plugins (`<plugin>/skills/...`, invocada como `/plugin:skill`).
- Precedência para o mesmo nome: corporativa > pessoal > projeto. Skill de plugin tem namespace e não colide. Skill do usuário substitui skill embutida de mesmo nome. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- Skills não sincronizam entre superfícies: claude.ai (zip em Configurações), API (`/v1/skills`) e Claude Code (sistema de arquivos) são separados. As skills prontas de documentos (pptx, xlsx, docx, pdf) não vêm no Claude Code. Fonte: platform.claude.com/.../agent-skills/overview (2026-11-02).
- Sessões em nuvem não carregam plugins instalados na sua máquina nem os habilitados no `.claude/settings.json`. Fonte: https://code.claude.com/docs/en/discover-plugins (2026-11-02). Se skills de `.claude/skills/` do repositório valem na nuvem: [não verificado].

### Instalar skills de terceiros
- Marketplace de plugins: `/plugin marketplace add anthropics/skills`, depois `/plugin install document-skills@anthropic-agent-skills` ou `example-skills@anthropic-agent-skills`. Fonte: https://github.com/anthropics/skills (2026-11-02).
- Forma geral: `/plugin install <plugin>@<marketplace>`; no shell, `claude plugin install ...` (escopo user por padrão; `--scope project` para o repositório). Fonte: code.claude.com/docs/en/discover-plugins (2026-11-02).
- Cópia de pasta: colocar a pasta da skill em `~/.claude/skills/` ou `.claude/skills/`. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- Seção específica sobre instalar skills soltas na página de skills: [não verificado] (os últimos ~18 mil caracteres da página não foram lidos).

### Segurança
- Oficial: usar skills só de fontes confiáveis (criadas por você ou da Anthropic); uma skill maliciosa pode mandar o Claude chamar ferramentas ou rodar código fora do propósito declarado, com risco de vazamento de dados. Auditar todos os arquivos (SKILL.md, scripts, recursos), procurar chamadas de rede inesperadas; tratar como instalar software. Fonte: platform.claude.com/.../agent-skills/overview (2026-11-02).
- `allowed-tools` pode pré-aprovar ferramentas e a confiança do workspace não barra isso: revisar o campo em skills versionadas antes de rodar. `` !`comando` `` no corpo executa shell antes de o Claude ver o texto; `disableSkillShellExecution` desliga. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- Regra do projeto: ler `SKILL.md` e `scripts/` antes de instalar qualquer skill de terceiros.

### Boas práticas oficiais de escrita
Fonte: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (2026-11-02).
- Descrição em terceira pessoa, dizendo o que faz e quando usar, com termos-chave; evitar "ajuda com documentos".
- Ser conciso: só o que o Claude ainda não sabe; dar um padrão-padrão em vez de lista de opções.
- Graus de liberdade: instruções livres para tarefas flexíveis; script exato e sem parâmetros para operações frágeis.
- Preferir scripts prontos para o que é repetível (mais confiáveis, economizam tokens); deixar claro se é para executar ou só ler; tratar erros no script.
- Divulgação progressiva: arquivos de apoio a um nível de profundidade do `SKILL.md`; índice em arquivos com mais de 100 linhas; caminhos com barra normal.
- Fluxos com checklist e laço validar-corrigir; plano intermediário validado por script em operações em lote.
- Criar avaliações antes (mínimo de três cenários), comparar com e sem a skill e testar com Haiku, Sonnet e Opus.
- Listar dependências; na API não há rede nem instalação de pacotes, no claude.ai depende da configuração, no Claude Code há rede total.

## Do projeto (versionadas no repositório)

| Skill | Para quê | Agente sugerido | Situação |
|---|---|---|---|
| `drive-ingestao` | Inventariar e baixar pastas de obra do Google Drive (metadados recursivos e download em lote) para dados/<obra>/. | Haiku | em uso |
| `escopo-etapas` | Extrair o escopo de materiais e serviços do contrato, com quantidades por etapa e sem preço, conferindo cada código no cadastro de materiais Sanepar. | — | em uso |
| `georef-pranchas` | Georreferenciar pranchas de projeto em PDF vetorial pela malha impressa, por afim absoluta, por prancha irmã (CAD × CAD) ou por pontos de controle com ICP. | — | em uso |
| `ler-prancha` | Ler prancha de projeto em PDF vetorial em camadas de entendimento: identidade, vistas, tabelas por OCR, elementos, vínculos e serviços. | — | em uso |
| `modelo-3d-drone` | Reconstruir o 3D por SfM com pycolmap em CPU e gerar ortofoto verdadeira e MDS a partir de fotos de drone DJI. | — | em uso |
| `mosaico-drone` | Montar mosaico georreferenciado (SIRGAS 2000 / UTM) a partir de fotos nadirais de drone DJI com GPS no EXIF. | — | em uso |
| `obra-em-camadas` | Orquestrar uma obra inteira do Drive ao HTML em camadas: fotos, 3D, pranchas vetoriais por layer CAD, etapas, escopo de materiais e sondagens. | — | em uso |
| `obras-lineares` | Calcular a vala de cada trecho de tubo pelo MOS Sanepar (largura, escoramento, escavação, reaterro, bota-fora, supressão e pavimento), com solo e NA da sondagem mais próxima. | — | em uso |
| `projeto-em-camadas` | Gerar o visualizador HTML único que sobrepõe mosaico de drone, satélite e pranchas de projeto (civil, hidromecânica, elétrica) em camadas, com medições em UTM e anotações. | — | em uso |
| `vcm-formulario` | Toda resposta do agente ao humano segue o mesmo formulário (objetivo, o que estou fazendo, onde estamos, agentes, precisa de você, campo livre), com os números preenchidos por vcm rumo --formulario. | qualquer | em teste |
| `vcm-rumo` | Manter objetivo, etapas da WBS, estimado × real e desvios em rumo.yaml e informar o humano a cada rodada, com comentário no PR. | qualquer | em teste |

### Ingestão do Google Drive

`drive-ingestao` · projetos_em_camadas/.claude/skills/drive-ingestao

**Quando usar**

- link de pasta do Drive com fotos de drone, PDFs de projeto ou planilhas
- baixar ou organizar arquivos do Drive de uma obra

**Quando evitar**

- conteúdo de PDF já baixado: usar ler-prancha

**Cuidados**

- arquivo acima de 10 MB é recusado pelo conector; de 5,5 a 10 MB costuma derrubar a conexão: usar link direto (camadas/drive.py)
- só um processo varre tool-results/ por vez
- conferir %PDF e tamanho depois do download
- dados/ fica fora do git (material do cliente)

### Escopo por etapa

`escopo-etapas` · projetos_em_camadas/.claude/skills/escopo-etapas

**Quando usar**

- etapas da obra, recorte de escopo ou quantitativos
- lista de materiais, cotação ou 'o que entra na 1ª etapa'

**Quando evitar**

- qualquer valor de preço: a skill não extrai preço (decisão de 28/10/2026)

**Cuidados**

- itens sem etapa (equipamentos, válvulas, civil global) ficam como 'verificar'
- quantidade do orçamento diferente da 1ª etapa é divergência a listar
- código fora do cadastro Sanepar ou unidade diferente da cadastrada gera alerta
- tabela só da 2ª etapa fica fora do escopo até confirmar com o TR
- serviço sem quantidade: estimativa com premissa declarada, que nunca substitui a quantidade do contrato

### Georreferenciar pranchas

`georef-pranchas` · projetos_em_camadas/.claude/skills/georef-pranchas

_Ferramentas: PyMuPDF, pytesseract._

**Quando usar**

- sobrepor pranchas 'sem escala' ou sem malha de coordenadas
- diagnosticar prancha desalinhada, torta, espelhada ou com escala errada

**Quando evitar**

- prancha que já tem georreferência aceita no obra.json

**Cuidados**

- a matriz final contém reflexão: não usar similaridade direta de pt para UTM
- conferir sempre visualmente sobre a ortofoto; número bom com imagem ruim é rejeitado
- escala medida na foto é pouco confiável: preferir prancha irmã ou malha
- folha de detalhe em outra escala não é irmã: conferir a escala do título
- rótulo errado pode existir no próprio desenho: decidir pela continuidade com a folha vizinha
- conferir contra testemunha independente (malha, GEOPLANTA, marcos E/N), não contra a própria foto

### Ler prancha

`ler-prancha` · projetos_em_camadas/.claude/skills/ler-prancha

_Ferramentas: PyMuPDF, pytesseract._

**Quando usar**

- saber o que uma prancha contém
- ligar elementos do desenho a itens de tabela ou serviços
- georreferenciar estrutura sem malha
- criar ou ajustar sinônimos de layer

**Quando evitar**

- PDF escaneado sem vetor: usar o fluxo raster (v1) de projeto-em-camadas

**Cuidados**

- texto SHX é traço: get_text vem vazio, por isso OCR
- letra de 16 a 18 px lê bem; a 25 px o tesseract trocou 3 por 5
- célula numérica é relida com --psm 7 e lista de caracteres permitidos
- número de balão precisa de um dígito por glifo
- folha com várias vistas não tem afim única
- rótulo sem leitura não se deduz

### Modelo 3D do drone

`modelo-3d-drone` · projetos_em_camadas/.claude/skills/modelo-3d-drone

_Ferramentas: pycolmap._

**Quando usar**

- fotos de fotogrametria ou em perspectiva
- pedido de 3D, nuvem de pontos, ortofoto ou MDS
- prédio torto ou costura na ortofoto

**Quando evitar**

- SfM falha por poucas fotos ou pouca sobreposição: usar mosaico-drone

**Cuidados**

- usar fotos nadirais e oblíquas juntas
- Z da nuvem é altura sobre a decolagem: corrigir a cota com controle vertical
- reprojeção abaixo de 1 px e todas as fotos registradas indicam SfM bom
- pares estéreo com desvio acima de 1 m são descartados
- sem GPU não há MVS denso do COLMAP; fachadas ficam pobres
- prédio torto indica falta de dados no telhado: pedir mais pares

### Mosaico de drone

`mosaico-drone` · projetos_em_camadas/.claude/skills/mosaico-drone

**Quando usar**

- montar, refazer ou diagnosticar mosaico de fotos de drone de uma obra

**Quando evitar**

- fotos oblíquas ou prédios altos: preferir a ortofoto de modelo-3d-drone

**Cuidados**

- GSD ajustado deve ficar a ±10 % do GSD do EXIF
- RMSE vs GPS em torno de 1 m é o normal para o GPS do drone
- costura mediana abaixo de ~15 cm (a 2 cm/px) é bom; pares com resíduo acima de 0,5 m merecem olhar
- não é ortofoto: há paralaxe de árvores e telhados
- posição absoluta depende do GPS (~1 m); precisão centimétrica exige controle em campo
- modelo fora de SENSOR_MM exige a largura do sensor para calcular o GSD

### Obra em camadas

`obra-em-camadas` · projetos_em_camadas/.claude/skills/obra-em-camadas

_Ferramentas: pycolmap, PyMuPDF, pytesseract._

**Quando usar**

- pedido 'faça o mesmo para a obra X'
- pasta do Drive de obra nova
- pedido de HTML em camadas completo

**Quando evitar**

- tarefa de uma etapa só: usar a skill específica da etapa

**Cuidados**

- inventário primeiro, de todos os arquivos; nunca dizer que um documento não existe sem procurar no inventário
- manter o vetor: nada de rasterizar para o HTML
- escopo sem preço: nenhum valor unitário, total ou fornecedor
- irmãs de pranchas com malha devem ser enraizadas numa prancha absoluta
- relatar lacunas explicitamente (ex.: etapa no desenho que o TR não menciona)
- não deixar dois agentes varrerem tool-results/ ao mesmo tempo
- a divisão Haiku/Sonnet/Opus é por subtarefa, não uma só para a skill

### Obras lineares

`obras-lineares` · projetos_em_camadas/.claude/skills/obras-lineares

**Quando usar**

- obras lineares, vala, escoramento ou esgotamento
- tubulação dentro da ETA
- MND/HDD
- supressão vegetal ou recomposição de pavimento de uma rede

**Quando evitar**

- qualquer preço: a skill é só geometria e serviço associado

**Cuidados**

- largura L = D + SL + X + Y; X = 0,10 m só se escorado
- escoramento acima de 1,25 m de profundidade
- NA mais raso que o fundo da vala indica esgotamento
- diferença acima de 1 % frente à planilha é alerta
- trecho sem profundidade distorce o reaterro
- paver e lajota só pelo usuário
- MND: citar as orientações de HDD, sem dimensionar pelo executor

### Projeto em camadas

`projeto-em-camadas` · projetos_em_camadas/.claude/skills/projeto-em-camadas

_Ferramentas: ezdxf._

**Quando usar**

- montar, atualizar ou estender o HTML de projeto em camadas de uma obra

**Quando evitar**

- obra com pranchas vetoriais e pipeline completo: usar obra-em-camadas (fluxo v2)

**Cuidados**

- coordenadas sempre em UTM no Python; o navegador só converte para exibir
- com DXF ou DWG, preferir camadas vetoriais por layer (ezdxf)
- PDF chapado: renderizar, separar por cor e gravar webp sem perdas
- conferir no Chromium: sem erros de console e folha alinhada à foto em zoom alto
- para publicar como Artifact, usar a versão CDN sem documento

### Formulário padrão de interação

`vcm-formulario` · vibe_code_metrics/.claude/skills/vcm-formulario (instalada em cada projeto pelo vcm iniciar)

_Ferramentas: Jinja2._

**Quando usar**

- toda resposta que relata trabalho
- início e fim de etapa
- ao chamar executores
- humano pergunta onde estamos

**Quando evitar**

- resposta curta sem trabalho feito: só cabeçalho, objetivo e campo livre

**Cuidados**

- números vêm do vcm, nunca de cabeça
- campos fixos não mudam de nome nem de ordem
- desvios e decisões pendentes sempre em Precisa de você

### Rumo do desenvolvimento

`vcm-rumo` · vibe_code_metrics/.claude/skills/vcm-rumo (instalada em cada projeto pelo vcm iniciar)

_Ferramentas: Plotly, Jinja2._

**Quando usar**

- início e fim de toda rodada de trabalho
- humano pergunta como está o desenvolvimento
- mudança de objetivo
- tarefa saindo do plano

**Quando evitar**

- correção de uma linha sem etapa própria: registrar só no PR

**Cuidados**

- estimativa é para calibrar, não para cobrar
- mudar de objetivo é permitido; mudar sem registrar em historico não
- nunca esconder desvio (fora do plano, estouro, parada, entregável ausente)

## Da plataforma (disponíveis nas sessões do Claude)

| Skill | Para quê | Agente sugerido | Situação |
|---|---|---|---|
| `code-review` | Revisar o diff, ou um PR, para bugs de correção, com níveis de esforço. | — | candidato |
| `dataviz` | Orientar o desenho de gráficos e dashboards (cores, escalas, acessibilidade), para qualquer biblioteca, inclusive Plotly. | — | candidato |
| `deep-research` | Pesquisar um tema em várias fontes, com subagentes, e entregar relatório com citações. | — | candidato |
| `docx` | Criar e editar documentos Word (.docx). | — | candidato |
| `pdf` | Ler, extrair texto e tabelas, juntar, dividir, preencher formulários e fazer OCR de PDFs. | — | candidato |
| `pptx` | Criar e editar apresentações PowerPoint (.pptx). | — | candidato |
| `run` | Subir e dirigir a aplicação do projeto para ver a mudança funcionando, além dos testes. | — | candidato |
| `session-start-hook` | Criar hooks de início de sessão versionados no repositório, para sessões na nuvem. | — | candidato |
| `simplify` | Revisar o código alterado para reuso, simplificação e eficiência, e aplicar as correções. | — | candidato |
| `skill-creator` | Criar, ajustar e avaliar skills novas. | — | candidato |
| `xlsx` | Abrir, editar, criar e limpar planilhas .xlsx e .csv, com fórmulas e gráficos. | — | candidato |

### Revisão de código

`code-review` · sessão do Claude Code (skill code-review)

**Quando usar**

- revisar o diff antes de abrir PR
- procurar bugs de correção em uma mudança

**Quando evitar**

- só limpeza de código (reuso, simplificação): usar simplify

**Cuidados**

- o nível máximo custa mais e só se pede por instrução explícita (CLAUDE.md ou pedido do humano)
- achados são hipóteses: confirmar antes de corrigir
- a revisão não substitui os testes do projeto (uv run pytest)

### Visualização de dados

`dataviz` · sessão do Claude Code (skill dataviz)

_Ferramentas: Plotly, Matplotlib._

**Quando usar**

- gráfico de etapa, curva ou indicador do projeto
- gráfico Plotly ou matplotlib de relatório
- paleta de cores para camadas ou disciplinas

**Quando evitar**

- cálculo do gráfico: o número vem do Python, nunca de conta feita no navegador

**Cuidados**

- regra do mantenedor: Python calcula, HTML/JS só apresenta
- cores do projeto (civil, hidromecânica, elétrica, geral) seguem a convenção existente
- checar contraste no modo escuro

### Pesquisa aprofundada

`deep-research` · sessão do Claude Code (skill deep-research)

**Quando usar**

- comparar alternativas técnicas ou normas
- revisar literatura sobre um método de medição

**Quando evitar**

- dado que já está no repositório ou na documentação do projeto: ler direto

**Cuidados**

- conferir cada citação antes de usar em documento técnico
- a pesquisa não substitui a norma vigente: citar a edição

### Documentos Word

`docx` · sessão do Claude Code (skill docx)

**Quando usar**

- memorial, relatório ou carta que o cliente pede em Word
- editar um .docx existente

**Quando evitar**

- relatório interativo do projeto: o visualizador é HTML gerado pelo Python

**Cuidados**

- números do documento devem vir da saída do Python, não ser digitados à mão
- conferir a versão final antes de enviar ao cliente

### PDF

`pdf` · sessão do Claude Code (skill pdf)

_Ferramentas: PyMuPDF, pdfplumber, pytesseract._

**Quando usar**

- conferir rapidamente uma prancha ou documento em PDF
- extrair texto ou tabela de um PDF avulso
- juntar ou dividir PDFs

**Quando evitar**

- extração repetível de pranchas no pipeline: usar código do projeto (pymupdf) para ficar determinístico

**Cuidados**

- leitura avulsa não é fonte de resultado de engenharia: conferir o valor contra a prancha
- OCR de texto SHX pode trocar dígitos

### Apresentações

`pptx` · sessão do Claude Code (skill pptx)

**Quando usar**

- apresentação de obra para reunião com o cliente
- resumo visual de etapas ou escopo para decisão

**Quando evitar**

- dado que precisa ser recalculado: o número sai do Python, a apresentação só mostra

**Cuidados**

- conferir cada número contra a saída do Python antes de apresentar
- gráficos colados como imagem não podem ser conferidos depois: guardar a fonte

### Rodar a aplicação

`run` · sessão do Claude Code (skill run)

**Quando usar**

- pedido para rodar, iniciar ou fotografar a aplicação
- confirmar que a mudança funciona no uso real

**Quando evitar**

- mudança que só toca testes ou documentação

**Cuidados**

- se o projeto já tiver skill própria de execução, ela tem prioridade
- registrar o que foi visto na execução, não só que subiu sem erro

### Hook de início de sessão

`session-start-hook` · sessão do Claude Code (skill session-start-hook)

**Quando usar**

- pedido explícito de um SessionStart hook commitado no repositório

**Quando evitar**

- configurar ambiente ou repositório para sessões na nuvem: usar as ferramentas de ambiente

**Cuidados**

- hook é executado pelo harness: preferências em memória não cumprem esse papel
- hook que instala dependências pode atrasar o início da sessão

### Simplificar código

`simplify` · sessão do Claude Code (skill simplify)

**Quando usar**

- limpar código recém-alterado antes do PR
- reduzir duplicação ou complexidade

**Quando evitar**

- procurar bugs: usar code-review (esta skill não caça bugs)

**Cuidados**

- aplica mudanças: rodar uv run pytest e uv run ruff check . depois
- não mexer em avaliadores e gabaritos trancados sem pedido explícito

### Criador de skills

`skill-creator` · sessão do Claude Code (skill skill-creator)

**Quando usar**

- criar uma skill nova para um fluxo repetido do projeto
- ajustar ou avaliar uma skill existente

**Quando evitar**

- mudança no código Python do projeto: não é uma skill

**Cuidados**

- testar a skill com um caso real antes de dar por pronta
- skill nova do projeto fica em .claude/skills/ do repositório que a usa

### Planilhas

`xlsx` · sessão do Claude Code (skill xlsx)

_Ferramentas: pandas, Polars._

**Quando usar**

- abrir ou editar planilha de orçamento ou de quantitativos
- criar planilha com fórmulas ou gráfico para o cliente

**Quando evitar**

- cálculo de engenharia que precisa ser reprodutível: calcular em Python (pandas ou Polars), não em fórmula de planilha

**Cuidados**

- fórmula gravada na planilha não substitui o cálculo do projeto
- planilha de cliente pode ter abas ocultas: conferir antes de concluir

## De plugins instalados

| Skill | Para quê | Agente sugerido | Situação |
|---|---|---|---|
| `architecture` | Criar ou avaliar um registro de decisão de arquitetura (ADR), com trade-offs e consequências. | — | candidato |
| `debug` | Conduzir depuração estruturada: reproduzir, isolar, diagnosticar e corrigir. | — | candidato |
| `documentation` | Escrever e manter documentação técnica: README, runbook, guia de uso e referência. | — | candidato |
| `tech-debt` | Levantar, categorizar e priorizar dívida técnica no repositório. | — | candidato |
| `testing-strategy` | Planejar a estratégia e o plano de testes de um componente ou de uma etapa. | — | candidato |

### Arquitetura (ADR)

`architecture` · sessão do Claude Code (skill engineering:architecture)

**Quando usar**

- escolher entre tecnologias ou bibliotecas com trade-offs
- documentar uma decisão de desenho que outros vão precisar entender

**Quando evitar**

- mudança pequena sem decisão de desenho envolvida

**Cuidados**

- registrar alternativas descartadas e o motivo
- registrar a data e o contexto da decisão
- decisão que afeta cálculo de engenharia precisa de tolerância declarada

### Depuração

`debug` · sessão do Claude Code (skill engineering:debug)

**Quando usar**

- erro com mensagem ou stack trace
- comportamento diferente do esperado sem causa óbvia

**Quando evitar**

- erro de digitação evidente, corrigível direto

**Cuidados**

- reproduzir antes de corrigir
- corrigir a causa, não o sintoma
- acrescentar teste que falhava antes da correção

### Documentação técnica

`documentation` · sessão do Claude Code (skill engineering:documentation)

**Quando usar**

- escrever ou atualizar README ou runbook
- documentar um fluxo de uso do repositório

**Quando evitar**

- docs/index.html: é gerado por 'uv run vcm docs' e nunca se edita à mão

**Cuidados**

- ao editar docs/*.md, rodar 'uv run vcm docs' e commitar docs/index.html junto
- o CI roda 'vcm docs --check'
- documentação de processo não substitui o plano em docs/plano.md

### Dívida técnica

`tech-debt` · sessão do Claude Code (skill engineering:tech-debt)

**Quando usar**

- auditoria de dívida técnica ou de saúde do código
- decidir o que refatorar primeiro

**Quando evitar**

- corrigir um bug agora: usar debug

**Cuidados**

- priorizar com evidência (métricas do balanço do vcm), não só por impressão
- cada item priorizado vira tarefa pequena com arquivos permitidos

### Estratégia de testes

`testing-strategy` · sessão do Claude Code (skill engineering:testing-strategy)

_Ferramentas: Hypothesis, pytest-benchmark, mutmut._

**Quando usar**

- planejar testes de um módulo novo de cálculo
- definir o que testar e com que cobertura

**Quando evitar**

- escrever um teste pontual: fazer direto, sem plano

**Cuidados**

- avaliadores e gabaritos são trancados: não alterar sem pedido explícito do humano
- cobertura é medida pelo balanço do vcm; o limite não pode cair

## Externas (repositórios públicos)

| Skill | Para quê | Agente sugerido | Situação |
|---|---|---|---|
| `ext-doc-coauthoring` | Fluxo em três etapas (contexto, refinamento por seção, teste com leitor sem contexto) para escrever propostas, especificações e documentos de decisão. | — | candidato |
| `ext-docx` | Criar e editar documentos Word (.docx), incluindo alterações rastreadas e comentários. | — | candidato |
| `ext-frontend-design` | Orientação para decisões visuais intencionais (tipografia, layout, tokens) ao criar ou reformar interfaces. | — | candidato |
| `ext-geopandas` | Fluxo com checagens para dados vetoriais em GeoPandas 1.2.0 (CRS, validade de geometria, junções espaciais, exportação). | — | candidato |
| `ext-mcp-builder` | Guia para construir servidores MCP de qualidade (Python FastMCP ou TypeScript) e suas avaliações. | — | candidato |
| `ext-networkx` | Construir, analisar e desenhar grafos com NetworkX (caminhos mínimos, centralidade, comunidades, leitura e escrita). | — | candidato |
| `ext-pdf` | Ler/extrair texto e tabelas de PDF, juntar, dividir, girar, criar PDF, preencher formulários e fazer OCR. | — | candidato |
| `ext-skill-creator` | Criar, melhorar e avaliar skills (evals com e sem a skill, otimização da descrição, empacotamento). | — | candidato |
| `ext-webapp-testing` | Testar e depurar apps web locais com Playwright em Python (capturas de tela, logs do console, servidores auxiliares). | — | candidato |
| `ext-xlsx` | Criar, editar e converter planilhas com openpyxl/pandas, recalculando fórmulas com LibreOffice e relatando erros. | — | candidato |

### Coautoria de documentos (Anthropic)

`ext-doc-coauthoring` · https://github.com/anthropics/skills/tree/main/skills/doc-coauthoring

**Quando usar**

- Redigir especificação, proposta técnica ou nota de decisão com revisão estruturada.

**Quando evitar**

- Textos curtos ou documentos que o método gera automaticamente.

**Cuidados**

- Só SKILL.md (sem scripts nem dependências).
- A pasta não tem LICENSE.txt nem campo license; licença do repositório raiz não conferida, por isso licenca null.
- Em inglês; sobrepõe-se a skills embutidas de documentos.

### Documentos Word (Anthropic)

`ext-docx` · https://github.com/anthropics/skills/tree/main/skills/docx

_Ferramentas: Jinja2._

**Quando usar**

- Memorial ou relatório que o cliente exige em .docx, com revisão rastreada.
- Editar modelo .docx existente.

**Quando evitar**

- Relatórios HTML do método (já são gerados por Python/Jinja2).
- Redistribuir a skill (licença proprietária).

**Cuidados**

- Licença proprietária (LICENSE.txt, 2025 Anthropic) sem cópia fora dos serviços nem derivados.
- Pasta tem scripts/ (OOXML); ler antes de instalar.
- Sobrepõe-se à skill embutida docx.
- Dependências exatas não verificadas (o SKILL.md não foi lido).

### Design de interface (Anthropic)

`ext-frontend-design` · https://github.com/anthropics/skills/tree/main/skills/frontend-design

_Ferramentas: Plotly, Jinja2._

**Quando usar**

- Melhorar a aparência de relatórios HTML e do visualizador (apresentação, sem cálculo em JS).

**Quando evitar**

- Alterar regra de cálculo; HTML/JS só apresentam valores do Python.

**Cuidados**

- Apache-2.0 (LICENSE.txt conferido).
- Só SKILL.md e LICENSE.txt, sem scripts.
- Sobrepõe-se às skills embutidas artifact-design e dataviz.

Licença: Apache-2.0 (verificada em 2026-11-02)

### GeoPandas (K-Dense, comunitária)

`ext-geopandas` · https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/geopandas

_Ferramentas: GeoPandas, Shapely, pyproj._

**Quando usar**

- {'Trabalho com shapes e UTM': 'planejar reprojeção, auditar geometrias e junções espaciais.'}

**Quando evitar**

- Tarefas sem dado vetorial; cálculos que já têm função validada no projeto.

**Cuidados**

- Skill de terceiros; ler SKILL.md e os scripts/ antes de instalar (o README do repositório recomenda escanear skills de terceiros).
- Licença MIT declarada no frontmatter da skill e no repositório (LICENSE.md); cada skill do repositório pode ter licença própria.
- Instalar a skill não instala dependências; pede ambiente Python 3.12 com uv.
- {'Atividade recente': 'repositório com 763 commits, versão 2.72.0 e 55,8 mil estrelas; data do último commit não confirmada.'}

Licença: MIT (verificada em 2026-11-02)

### Construtor de servidor MCP (Anthropic)

`ext-mcp-builder` · https://github.com/anthropics/skills/tree/main/skills/mcp-builder

_Ferramentas: Pydantic._

**Quando usar**

- Expor funções determinísticas do projeto (cálculos, consulta a cadastros) como ferramentas MCP.

**Quando evitar**

- Sem necessidade de integração externa; um CLI Python (vcm) costuma bastar.

**Cuidados**

- Apache-2.0 (LICENSE.txt conferido).
- Traz scripts/ e reference/; ler antes de instalar.
- Foco recomendado em TypeScript; exige Node ou o SDK Python.

Licença: Apache-2.0 (verificada em 2026-11-02)

### NetworkX (K-Dense, comunitária)

`ext-networkx` · https://github.com/K-Dense-AI/scientific-agent-skills/tree/main/skills/networkx

_Ferramentas: NetworkX._

**Quando usar**

- Redes de tubulação, conectividade de trechos ou dependências entre tarefas.

**Quando evitar**

- Grafos muito grandes (considerar rustworkx ou igraph).

**Cuidados**

- Skill de terceiros; ler SKILL.md e referências antes de instalar.
- O campo license da skill diz BSD de 3 cláusulas (provavelmente a do NetworkX); o repositório é MIT.
- Pasta tem SKILL.md e references/, sem scripts.
- Data do último commit não confirmada.

Licença: BSD-3-Clause (verificada em 2026-11-02)

### PDF (Anthropic)

`ext-pdf` · https://github.com/anthropics/skills/tree/main/skills/pdf

_Ferramentas: pdfplumber, PyMuPDF, pytesseract._

**Quando usar**

- Extração de tabelas e texto de memoriais e listas em PDF para pandas/planilha.
- Mesclar, dividir ou girar PDFs de projeto; PDF escaneado que precisa de OCR.

**Quando evitar**

- Pranchas vetoriais em camadas CAD ou georreferenciamento; usar as skills internas do projeto (ler-prancha, georef-pranchas).
- Redistribuir ou adaptar a skill (licença proprietária).

**Cuidados**

- Licença proprietária (LICENSE.txt, 2025 Anthropic) que proíbe extrair, copiar fora dos serviços e criar derivados; uso conforme o contrato com a Anthropic.
- Traz scripts/, forms.md e reference.md; ler antes de instalar.
- Depende de pypdf, pdfplumber, reportlab, pytesseract, pdf2image e ferramentas de sistema (poppler, tesseract).
- Sobrepõe-se à skill embutida pdf (por isso o prefixo ext-).

### Criador de skills (Anthropic)

`ext-skill-creator` · https://github.com/anthropics/skills/tree/main/skills/skill-creator

**Quando usar**

- Transformar um procedimento recorrente do mantenedor em skill do projeto com avaliações.
- Medir se a descrição aciona a skill (alinha com a medição antes x depois do método).

**Quando evitar**

- Skill trivial de poucas linhas; escrever à mão seguindo as boas práticas oficiais basta.

**Cuidados**

- Apache-2.0 (LICENSE.txt conferido).
- Scripts Python (run_eval, run_loop, package_skill, eval-viewer); ler antes de instalar.
- Otimização de descrição usa a CLI claude -p (só Claude Code) e subagentes em paralelo, o que consome tokens.
- Sobrepõe-se ao skill-creator embutido.

Licença: Apache-2.0 (verificada em 2026-11-02)

### Teste de aplicação web (Anthropic)

`ext-webapp-testing` · https://github.com/anthropics/skills/tree/main/skills/webapp-testing

**Quando usar**

- Conferir o visualizador HTML (medição, camadas) no navegador headless e capturar o console.
- Complementar scripts/testar_visualizador.py com cenários de interface.

**Quando evitar**

- {'Verificar cálculo': 'este fica em Python com pytest, não em teste de interface.'}

**Cuidados**

- Apache-2.0 (LICENSE.txt conferido).
- Traz scripts/with_server.py e examples/; ler antes de instalar.
- Requer Playwright e Chromium instalados (o SKILL.md não dá passos de instalação).

Licença: Apache-2.0 (verificada em 2026-11-02)

### Planilhas Excel (Anthropic)

`ext-xlsx` · https://github.com/anthropics/skills/tree/main/skills/xlsx

_Ferramentas: pandas._

**Quando usar**

- Entregar planilha com fórmulas vivas (quantitativos, orçamentos) e conferir que não há
- Editar planilha existente preservando formatação.

**Quando evitar**

- {'Cálculo de engenharia do método': 'o resultado final é calculado em Python (regra do mantenedor); a planilha apenas apresenta.'}
- Quando o entregável principal é HTML, banco de dados ou Google Sheets (a própria skill exclui esses casos).

**Cuidados**

- Licença proprietária declarada no frontmatter (LICENSE.txt); não redistribuir.
- Traz scripts/ (recalc.py usa LibreOffice via soffice); ler antes de instalar.
- Exige openpyxl, pandas, markitdown e LibreOffice instalados.
- Sobrepõe-se à skill embutida xlsx.
