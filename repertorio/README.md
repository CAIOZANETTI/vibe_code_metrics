# Repertório

O repertório é o catálogo de alternativas técnicas que o método considera para cada tipo de tarefa. Cada alternativa tem um arquivo YAML em `repertorio/<papel>/<id>.yaml`, com descrição, quando considerar, quando evitar, cuidados e relações com outras alternativas.

Papéis:

- `calculo`: cálculo numérico e álgebra linear.
- `tabular`: tabelas, filtros, junções e agrupamentos.
- `armazenamento`: persistência de dados.
- `grafos`: estruturas e algoritmos de grafos.
- `intercambio`: formatos de troca entre sistemas.
- `apresentacao`: geração de figuras e relatórios.

Status:

- `em_uso`: adotada no projeto atual.
- `em_teste`: em avaliação em uma tese ou experimento.
- `candidato`: considerada, ainda sem teste.
- `rejeitado`: testada e descartada, com evidência registrada.

Só se comparam alternativas do mesmo papel. Por isso, `compete_com` liga apenas alternativas de um mesmo papel; `coopera_com` pode cruzar papéis.

O campo `evidencias` nasce vazio. As teses o preenchem com referências aos seus resultados, por exemplo T005 para a escolha entre pandas e Polars. Este repertório não traz números de desempenho.

`modelos.yaml` é o catálogo de modelos de IA. Preços só entram com fonte oficial, data de verificação e valor preenchido a partir da página do fornecedor.
