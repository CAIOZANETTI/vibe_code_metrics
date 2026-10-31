# T000 — Autodesenvolvimento do Vibe Code Metrics

## Problema
Não sabemos quanto custa, em tokens, tempo humano e qualidade, desenvolver um repositório de
engenharia com agentes de IA, nem se a qualidade do código se mantém ao longo das iterações.

## Hipótese (falsificável)
Desenvolver o `vcm` com o próprio método (PDCA com retrospectiva medida a cada PR) produz:

1. decisões rastreáveis em 100% dos PRs, cada uma com cartão de balanço;
2. nenhuma regressão em restrição eliminatória mesclada (testes, determinismo, segurança);
3. complexidade média e duplicação **sem tendência de alta** ao longo das fases, ao contrário da
   degradação persistente relatada em estudos de adoção de agentes;
4. custo por item do plano mensurável e decrescente após a Fase 2.

A hipótese é **rejeitada** se o item 2 ou o item 3 falharem em duas fases consecutivas.

## Alternativas
- Desenvolvimento sem retrospectiva (linha de base: Fase 0, reconstruída a partir do histórico).
- Variações de roteamento de modelos (ver T003).

## Condições de validade
- Um único mantenedor: baixo poder estatístico. Os resultados são descritivos, não causais.
- O custo em plano de assinatura é **equivalente de API**.
