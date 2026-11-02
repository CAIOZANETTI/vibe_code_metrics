---
name: vcm-rumo
description: Mantém o rumo do desenvolvimento (objetivo, etapas da WBS, estimado × real e desvios) em rumo.yaml e informa o humano a cada rodada, com comentário no PR. Use no início e no fim de toda rodada de trabalho num projeto com o Vibe Code Metrics, quando o humano pedir "como está o desenvolvimento", ao mudar o objetivo ou ao perceber que a tarefa saiu do plano.
---

# Rumo do desenvolvimento

O objetivo e as etapas ficam em `rumo.yaml`, na raiz do projeto. Ele é o contrato entre o humano e
os agentes: o que estamos fazendo, em que ordem, quanto deve custar e quando está pronto. O comando
`vcm rumo` compara o plano com o que aconteceu (tokens e tempo dos logs do Claude Code, arquivos
alterados no git) e aponta desvios.

## No início de cada rodada

1. Se não existir `rumo.yaml`, proponha um ao humano antes de programar: `vcm rumo --novo "objetivo"`
   e preencha as etapas (entregáveis como caminhos, `depende_de`, `agente`, `estimativa_min`,
   `estimativa_tokens`, critério de pronto). Etapas pequenas: de 15 a 60 minutos cada.
2. Rode `vcm rumo` e diga ao humano, em até 5 linhas: objetivo, progresso, etapa que vai começar,
   estimativa dela e desvios em aberto.
3. Marque a etapa: `vcm rumo --etapa E2 --status fazendo`.
4. Ao chamar um executor, comece a descrição do agente pelo id da etapa (`E2: …`). Assim o
   `vcm rumo` separa as chamadas de duas etapas do mesmo modelo em paralelo.

## Durante a rodada

- Trabalhe só nos entregáveis da etapa. Se precisar mexer em outro arquivo, pare e decida com o
  humano: (a) acrescentar o arquivo à etapa, (b) criar uma etapa nova ou (c) desistir da mudança.
- Se a etapa passar de 1,5× a estimativa de tokens ou de tempo, avise antes de continuar.

## No fim de cada rodada

1. Marque o status (`feito`, `bloqueado` ou `cancelado`) com `vcm rumo --etapa … --status …`.
2. Rode `vcm balanco <base> HEAD` (qualidade) e `vcm rumo` (rumo).
3. Publique o Markdown de `results/rumo.md` como comentário no PR da rodada e mostre ao humano o
   mesmo resumo.
4. Se o objetivo mudou, registre em `historico` (`data`, `mudanca`, `motivo`) — mudar de objetivo é
   permitido; mudar sem registrar não.

## Regras

- O humano decide o objetivo e aceita o critério de pronto; o agente propõe etapas e estimativas.
- Referência de calibração (rodada de 02/11/2026, razão real/estimado): etapa de executor Sonnet
  com testes, de 100 mil a 150 mil tokens e de 5 a 15 minutos; etapa do gerente (Opus), cerca de
  100 mil tokens. Ajuste com a razão das rodadas seguintes.
- Estimativas são para calibrar, não para cobrar: a razão real/estimado de cada etapa melhora as
  próximas estimativas.
- Não esconda desvio: "fora do plano", "estouro", "parada" e "entregável ausente" sempre aparecem no
  resumo ao humano.
