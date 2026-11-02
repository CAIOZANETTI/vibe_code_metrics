---
name: vcm-formulario
description: Formulário padrão de interação. Toda resposta do agente ao humano durante o vibe coding num projeto com o Vibe Code Metrics segue o mesmo formulário (objetivo, o que estou fazendo, onde estamos, agentes, precisa de você, campo livre). Use em toda resposta que relate trabalho, ao iniciar ou terminar uma etapa, ao chamar executores e quando o humano perguntar "onde estamos".
---

# Formulário padrão de interação

O humano acompanha vários desenvolvimentos ao mesmo tempo. Para saber onde cada um está sem ler a
conversa inteira, **toda resposta que relata trabalho começa por este formulário**, sempre com os
mesmos campos e na mesma ordem.

## Como preencher

1. Rode `vcm rumo --formulario`. O Python preenche o que vem de dados: objetivo, progresso, etapas
   em andamento, próxima etapa, tempo, gasto, agentes e desvios. Não invente esses números.
2. Complete os campos marcados com `…`:
   - **O que estou fazendo:** uma ou duas frases, no presente, sobre a ação desta resposta.
   - **Campo livre:** resultado, explicação, pergunta, lista, tabela; o que a resposta precisar.
3. Em **Agentes**, acrescente o papel de cada agente que vai chamar nesta resposta (gerente,
   executor-sonnet, executor-haiku) se ainda não estiver na tabela.
4. Em **Precisa de você**, além dos desvios, liste as decisões que só o humano pode tomar
   (troca de métricas, mudança de objetivo, correção sugerida a aprovar). Se não houver, "nada".

Sem `rumo.yaml` (pergunta avulsa, projeto sem rumo), use o mesmo formulário com "sem rumo
definido" em Onde estamos e proponha um rumo se o trabalho for durar mais de uma rodada.

## Modelo

```markdown
### Interação · <projeto>

**Objetivo:** <do rumo.yaml>

**O que estou fazendo:** <frase curta>

**Onde estamos:** `█████░░░░░ 50%` · em andamento: E2 … · próxima: E3 · 0,40 dias · IA 1,2 h · US$ 3,17

**Agentes**

| Agente | Etapa | Situação |
|---|---|---|
| sonnet | E2 … | trabalhando |

**Precisa de você**

- nada no momento

**Campo livre:** <o resto da resposta>
```

## Regras

- Os campos fixos não mudam de nome nem de ordem: o humano lê de relance.
- Números vêm do `vcm`, nunca de estimativa de cabeça. Horário de fim só depois que aconteceu.
- Resposta curta a uma pergunta direta, sem trabalho feito, pode ir só no Campo livre, mas com o
  cabeçalho e o objetivo.
- Não esconda desvio nem decisão pendente: eles vão sempre em **Precisa de você**.
