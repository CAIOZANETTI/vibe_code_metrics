# Como funcionam as Agent Skills (notas verificadas)

Verificado em 2026-11-02 nas fontes citadas. O que não foi confirmado está marcado [não verificado].

## O que é uma skill
- Pasta com um `SKILL.md`: frontmatter YAML entre `---` + instruções em markdown. Pode ter arquivos de apoio (`reference.md`, `examples.md`, `scripts/`). Fonte: https://code.claude.com/docs/en/skills (2026-11-02).
- Frontmatter na plataforma: `name` (até 64 caracteres; só minúsculas, números e hífen; sem as palavras reservadas `anthropic` e `claude`) e `description` (não vazia, até 1.024 caracteres) são exigidos. Fonte: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview (2026-11-02).
- No Claude Code todos os campos são opcionais (só `description` é recomendado); `name` padrão é o nome da pasta. Outros campos: `when_to_use`, `disable-model-invocation`, `user-invocable`, `allowed-tools`, `context: fork`, `model`, `paths`, `license`. Campos desconhecidos são ignorados sem erro. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- A descrição combinada (`description` + `when_to_use`) é truncada em 1.536 caracteres na listagem: colocar o caso de uso principal no começo. Fonte: idem.
- Carregamento progressivo: nível 1, só nome e descrição (cerca de 100 tokens por skill) ficam sempre no contexto; nível 2, o corpo do `SKILL.md` entra quando a descrição casa com o pedido; nível 3, arquivos de apoio são lidos só se necessários e scripts rodam via bash, entrando no contexto apenas a saída. Fonte: platform.claude.com/.../agent-skills/overview (2026-11-02).
- Depois de carregada, a skill permanece no contexto nos turnos seguintes; por isso, corpo curto (menos de 500 linhas). Também pode ser chamada direto com `/nome-da-skill`. Fonte: code.claude.com/docs/en/skills (2026-11-02).

## Onde ficam (Claude Code)
- Pessoal: `~/.claude/skills/<skill>/SKILL.md` (todos os projetos da máquina).
- Projeto: `.claude/skills/<skill>/SKILL.md` (versionado no repositório; vale para quem clonar).
- Também: corporativa (managed settings), aninhada em subpastas, `--add-dir` e plugins (`<plugin>/skills/...`, invocada como `/plugin:skill`).
- Precedência para o mesmo nome: corporativa > pessoal > projeto. Skill de plugin tem namespace e não colide. Skill do usuário substitui skill embutida de mesmo nome. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- Skills não sincronizam entre superfícies: claude.ai (zip em Configurações), API (`/v1/skills`) e Claude Code (sistema de arquivos) são separados. As skills prontas de documentos (pptx, xlsx, docx, pdf) não vêm no Claude Code. Fonte: platform.claude.com/.../agent-skills/overview (2026-11-02).
- Sessões em nuvem não carregam plugins instalados na sua máquina nem os habilitados no `.claude/settings.json`. Fonte: https://code.claude.com/docs/en/discover-plugins (2026-11-02). Se skills de `.claude/skills/` do repositório valem na nuvem: [não verificado].

## Instalar skills de terceiros
- Marketplace de plugins: `/plugin marketplace add anthropics/skills`, depois `/plugin install document-skills@anthropic-agent-skills` ou `example-skills@anthropic-agent-skills`. Fonte: https://github.com/anthropics/skills (2026-11-02).
- Forma geral: `/plugin install <plugin>@<marketplace>`; no shell, `claude plugin install ...` (escopo user por padrão; `--scope project` para o repositório). Fonte: code.claude.com/docs/en/discover-plugins (2026-11-02).
- Cópia de pasta: colocar a pasta da skill em `~/.claude/skills/` ou `.claude/skills/`. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- Seção específica sobre instalar skills soltas na página de skills: [não verificado] (os últimos ~18 mil caracteres da página não foram lidos).

## Segurança
- Oficial: usar skills só de fontes confiáveis (criadas por você ou da Anthropic); uma skill maliciosa pode mandar o Claude chamar ferramentas ou rodar código fora do propósito declarado, com risco de vazamento de dados. Auditar todos os arquivos (SKILL.md, scripts, recursos), procurar chamadas de rede inesperadas; tratar como instalar software. Fonte: platform.claude.com/.../agent-skills/overview (2026-11-02).
- `allowed-tools` pode pré-aprovar ferramentas e a confiança do workspace não barra isso: revisar o campo em skills versionadas antes de rodar. `` !`comando` `` no corpo executa shell antes de o Claude ver o texto; `disableSkillShellExecution` desliga. Fonte: code.claude.com/docs/en/skills (2026-11-02).
- Regra do projeto: ler `SKILL.md` e `scripts/` antes de instalar qualquer skill de terceiros.

## Boas práticas oficiais de escrita
Fonte: https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices (2026-11-02).
- Descrição em terceira pessoa, dizendo o que faz e quando usar, com termos-chave; evitar "ajuda com documentos".
- Ser conciso: só o que o Claude ainda não sabe; dar um padrão-padrão em vez de lista de opções.
- Graus de liberdade: instruções livres para tarefas flexíveis; script exato e sem parâmetros para operações frágeis.
- Preferir scripts prontos para o que é repetível (mais confiáveis, economizam tokens); deixar claro se é para executar ou só ler; tratar erros no script.
- Divulgação progressiva: arquivos de apoio a um nível de profundidade do `SKILL.md`; índice em arquivos com mais de 100 linhas; caminhos com barra normal.
- Fluxos com checklist e laço validar-corrigir; plano intermediário validado por script em operações em lote.
- Criar avaliações antes (mínimo de três cenários), comparar com e sem a skill e testar com Haiku, Sonnet e Opus.
- Listar dependências; na API não há rede nem instalação de pacotes, no claude.ai depende da configuração, no Claude Code há rede total.
