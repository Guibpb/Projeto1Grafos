# Análise de Redes: Rede de Hiperlinks da Wikipédia

Este repositório contém os códigos, dados e resultados utilizados no projeto de caracterização e modelagem de uma rede complexa real.

O projeto modela uma rede de hiperlinks da Wikipédia relacionada à **Ciência da Computação** e investiga suas propriedades estruturais, suas principais medidas de centralidade e a capacidade de modelos clássicos de redes em reproduzir essas características.

## Sobre o Projeto

O objetivo é investigar quais propriedades estruturais caracterizam a rede estudada e verificar em que medida essas propriedades podem ser reproduzidas pelos modelos clássicos de **Erdős–Rényi**, **Watts–Strogatz** e **Barabási–Albert**.

### Definição da Rede

- **Nós:** representam artigos da Wikipédia.
- **Arestas:** representam hiperlinks entre artigos.
- **Direção:** a rede original é direcionada. Uma aresta `A → B` indica que o artigo A possui um hiperlink para o artigo B.
- **Peso:** a rede é não ponderada; cada hiperlink é representado por uma aresta.

A coleta foi realizada a partir do artigo **"Ciência da computação"**, utilizando uma busca em largura (BFS) com profundidade máxima igual a 2.

Foi definido um limite de 500 nós. A coleta resultou em uma rede com **397 nós** e **9.246 arestas direcionadas**.

## Estrutura do Repositório

```text
.
├── coleta.py
├── analise.py
├── modelos.py
├── rede_wikipedia.json
├── resultados/
│   ├── metricas.txt
│   ├── centralidades.csv
│   ├── comparacao_top10_centralidades.csv
│   ├── distribuicao_grau_total.png
│   ├── distribuicao_in_out_degree.png
│   ├── modelos_detalhado.csv
│   ├── comparacao_modelos.csv
│   ├── comparacao_modelos_desvio.csv
│   ├── comparacao_erros_modelos.csv
│   ├── comparacao_modelos.txt
│   ├── distribuicao_grau_modelos.png
│   ├── ccdf_grau_modelos.png
│   ├── comparacao_clustering.png
│   └── comparacao_path_length.png
└── README.md