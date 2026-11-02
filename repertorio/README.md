# Repertório

O repertório é o catálogo de alternativas técnicas que o método considera para cada tipo de tarefa. Cada alternativa tem um arquivo YAML em `repertorio/<papel>/<id>.yaml`, com descrição, quando considerar, quando evitar, cuidados e relações com outras alternativas.

Papéis:

- `calculo`: cálculo numérico e álgebra linear.
- `tabular`: tabelas, filtros, junções e agrupamentos.
- `armazenamento`: persistência de dados.
- `validacao`: unidades físicas e validação de esquemas e tabelas.
- `geoespacial`: geometria, sistemas de coordenadas, vetores e rasters georreferenciados.
- `cad_3d`: CAD (DXF), BIM (IFC), nuvens de pontos e fotogrametria.
- `grafos`: estruturas e algoritmos de grafos.
- `intercambio`: formatos de troca entre sistemas.
- `documentos`: leitura de PDF (vetorial e tabelas) e OCR.
- `apresentacao`: geração de figuras e relatórios.
- `qualidade`: testes de propriedade, tempo e mutação.

Status:

- `em_uso`: adotada no projeto atual.
- `em_teste`: em avaliação em uma tese ou experimento.
- `candidato`: considerada, ainda sem teste.
- `rejeitado`: testada e descartada, com evidência registrada.

Só se comparam alternativas do mesmo papel. Por isso, `compete_com` liga apenas alternativas de um mesmo papel; `coopera_com` pode cruzar papéis.

O campo `evidencias` nasce vazio. As teses o preenchem com referências aos seus resultados, por exemplo T005 para a escolha entre pandas e Polars. Este repertório não traz números de desempenho.

Campos de verificação: `repositorio`, `licenca` (identificador SPDX), `ultima_versao`
("x.y.z (aaaa-mm)") e `verificado_em` (data em que licença e versão foram conferidas no PyPI ou
no repositório). Campo que não foi conferido fica `null` e é anotado em `cuidados`.

A página legível do repertório (`docs/repertorio.md`, também no HTML da documentação) é gerada
destes arquivos por `vcm docs`.

`modelos.yaml` é o catálogo de modelos de IA. Preços só entram com fonte oficial, data de verificação e valor preenchido a partir da página do fornecedor.
