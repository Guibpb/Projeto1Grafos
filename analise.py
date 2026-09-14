import json
from pathlib import Path

import networkx as nx
import pandas as pd
import matplotlib.pyplot as plt


# ============================================================
# CONFIGURAÇÕES
# ============================================================

ARQUIVO_REDE = "rede_wikipedia.json"
PASTA_RESULTADOS = Path("resultados")
TOP_N = 10


# ============================================================
# CARREGAR REDE
# ============================================================

def carregar_rede(arquivo):
    """Carrega a rede direcionada salva pelo coleta.py."""
    with open(arquivo, "r", encoding="utf-8") as f:
        dados = json.load(f)

    # O formato node_link_data usado na coleta pode apresentar
    # a lista de arestas como "edges" ou "links", dependendo
    # da versão do NetworkX.
    if "edges" in dados:
        G = nx.node_link_graph(dados, directed=True, edges="edges")
    elif "links" in dados:
        G = nx.node_link_graph(dados, directed=True, edges="links")
    else:
        raise ValueError("Formato do arquivo JSON não reconhecido.")

    return nx.DiGraph(G)


# ============================================================
# FUNÇÕES AUXILIARES
# ============================================================

def media_dict(dicionario):
    if not dicionario:
        return 0.0
    return sum(dicionario.values()) / len(dicionario)


def top_10(dicionario):
    return sorted(
        dicionario.items(),
        key=lambda x: x[1],
        reverse=True
    )[:TOP_N]


def salvar_ranking(dicionario, nome_metrica):
    """Salva ranking de uma métrica em CSV."""
    dados = sorted(
        dicionario.items(),
        key=lambda x: x[1],
        reverse=True
    )

    df = pd.DataFrame(
        dados,
        columns=["pagina", nome_metrica]
    )

    return df


# ============================================================
# CARACTERIZAÇÃO ESTRUTURAL
# ============================================================

def analisar_estrutura(G):
    n = G.number_of_nodes()
    m = G.number_of_edges()

    if n > 0:
        densidade = nx.density(G)
    else:
        densidade = 0.0

    # -------------------------
    # Graus
    # -------------------------
    graus_in = dict(G.in_degree())
    graus_out = dict(G.out_degree())
    graus_total = dict(G.degree())

    grau_medio_total = media_dict(graus_total)
    grau_medio_in = media_dict(graus_in)
    grau_medio_out = media_dict(graus_out)

    # -------------------------
    # Clustering
    # -------------------------
    # NetworkX calcula clustering para grafos direcionados.
    clustering_medio = nx.average_clustering(G)

    # -------------------------
    # Componentes conexos
    # -------------------------
    # Para "componente conexo", tratamos o grafo como não direcionado.
    UG = G.to_undirected()
    componentes = list(nx.connected_components(UG))
    numero_componentes = len(componentes)

    maior_componente = max(componentes, key=len) if componentes else set()
    maior_componente_tamanho = len(maior_componente)

    # -------------------------
    # Caminho médio e diâmetro
    # -------------------------
    # Esses valores não podem ser calculados diretamente no grafo
    # inteiro se ele não for conexo. Usamos a maior componente conexa,
    # ignorando temporariamente a direção das arestas.
    if maior_componente_tamanho >= 2:
        G_maior = UG.subgraph(maior_componente).copy()
        average_path_length = nx.average_shortest_path_length(G_maior)
        diameter = nx.diameter(G_maior)
    else:
        average_path_length = 0.0
        diameter = 0

    # -------------------------
    # Componentes fortemente conexos
    # -------------------------
    componentes_fortes = list(nx.strongly_connected_components(G))
    numero_componentes_fortes = len(componentes_fortes)
    maior_componente_forte = max(
        (len(c) for c in componentes_fortes),
        default=0
    )

    metricas = {
        "numero_nos": n,
        "numero_arestas": m,
        "grau_medio_total": grau_medio_total,
        "grau_medio_entrada": grau_medio_in,
        "grau_medio_saida": grau_medio_out,
        "densidade": densidade,
        "clustering_coefficient_medio": clustering_medio,
        "average_path_length_maior_componente": average_path_length,
        "diametro_maior_componente": diameter,
        "componentes_conexos": numero_componentes,
        "maior_componente_conexa_nos": maior_componente_tamanho,
        "componentes_fortemente_conexos": numero_componentes_fortes,
        "maior_componente_fortemente_conexa_nos": maior_componente_forte,
    }

    return metricas, graus_in, graus_out, graus_total, UG


# ============================================================
# CENTRALIDADES
# ============================================================

def analisar_centralidades(G, UG):
    print()
    print("Calculando centralidades...")

    # Degree centrality no grafo direcionado considera o grau total.
    degree = nx.degree_centrality(G)

    # Em grafo direcionado, o closeness padrão do NetworkX representa
    # a distância a partir dos nós que conseguem alcançar cada nó.
    closeness = nx.closeness_centrality(G)

    betweenness = nx.betweenness_centrality(
        G,
        normalized=True
    )

    # Eigenvector centrality: usamos o grafo direcionado.
    # max_iter alto evita falha desnecessária em convergência.
    try:
        eigenvector = nx.eigenvector_centrality(
            G,
            max_iter=2000,
            tol=1e-10
        )
    except nx.PowerIterationFailedConvergence:
        print("Aviso: eigenvector centrality não convergiu no grafo direcionado.")
        print("Calculando eigenvector centrality na versão não direcionada.")
        eigenvector = nx.eigenvector_centrality(
            UG,
            max_iter=2000,
            tol=1e-10
        )

    # PageRank é especialmente apropriado para uma rede de hiperlinks.
    pagerank = nx.pagerank(G, alpha=0.85)

    return {
        "degree_centrality": degree,
        "closeness": closeness,
        "betweenness": betweenness,
        "eigenvector_centrality": eigenvector,
        "pagerank": pagerank,
    }


# ============================================================
# DISTRIBUIÇÃO DE GRAUS
# ============================================================

def gerar_grafico_graus(graus_in, graus_out, graus_total):
    frequencia_total = {}
    for grau in graus_total.values():
        frequencia_total[grau] = frequencia_total.get(grau, 0) + 1

    frequencia_in = {}
    for grau in graus_in.values():
        frequencia_in[grau] = frequencia_in.get(grau, 0) + 1

    frequencia_out = {}
    for grau in graus_out.values():
        frequencia_out[grau] = frequencia_out.get(grau, 0) + 1

    # -------------------------
    # Frequência do grau total
    # -------------------------
    plt.figure(figsize=(9, 6))
    plt.bar(
        list(frequencia_total.keys()),
        list(frequencia_total.values()),
        width=0.8
    )
    plt.xlabel("Grau total")
    plt.ylabel("Número de páginas")
    plt.title("Distribuição do grau total")
    plt.tight_layout()
    plt.savefig(
        PASTA_RESULTADOS / "distribuicao_grau_total.png",
        dpi=200
    )
    plt.close()

    # -------------------------
    # In-degree x Out-degree
    # -------------------------
    plt.figure(figsize=(9, 6))
    plt.hist(
        list(graus_in.values()),
        bins=20,
        alpha=0.7,
        label="In-degree"
    )
    plt.hist(
        list(graus_out.values()),
        bins=20,
        alpha=0.7,
        label="Out-degree"
    )
    plt.xlabel("Grau")
    plt.ylabel("Número de páginas")
    plt.title("Distribuição de in-degree e out-degree")
    plt.legend()
    plt.tight_layout()
    plt.savefig(
        PASTA_RESULTADOS / "distribuicao_in_out_degree.png",
        dpi=200
    )
    plt.close()


# ============================================================
# GERA TABELA DE CENTRALIDADES
# ============================================================

def gerar_tabela_centralidades(G, centralidades):
    paginas = list(G.nodes())

    df = pd.DataFrame({
        "pagina": paginas,
        "degree_centrality": [centralidades["degree_centrality"][p] for p in paginas],
        "closeness": [centralidades["closeness"][p] for p in paginas],
        "betweenness": [centralidades["betweenness"][p] for p in paginas],
        "eigenvector_centrality": [centralidades["eigenvector_centrality"][p] for p in paginas],
        "pagerank": [centralidades["pagerank"][p] for p in paginas],
        "in_degree": [G.in_degree(p) for p in paginas],
        "out_degree": [G.out_degree(p) for p in paginas],
        "degree_total": [G.degree(p) for p in paginas],
    })

    df.to_csv(
        PASTA_RESULTADOS / "centralidades.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return df


# ============================================================
# IMPRIMIR TOP 10
# ============================================================

def imprimir_top_centralidades(centralidades):

    nomes = {
        "degree_centrality": "Degree Centrality",
        "closeness": "Closeness",
        "betweenness": "Betweenness",
        "eigenvector_centrality": "Eigenvector Centrality",
        "pagerank": "PageRank",
    }

    for chave, nome in nomes.items():

        print()
        print("=" * 60)
        print(f"TOP {TOP_N} - {nome}")
        print("=" * 60)

        ranking = top_10(centralidades[chave])

        for i, (pagina, valor) in enumerate(ranking, start=1):
            print(
                f"{i:2d}. {pagina} -> {valor:.6f}"
            )


# ============================================================
# COMPARAÇÃO ENTRE CENTRALIDADES
# ============================================================

def calcular_concordancia(df):
    """
    Mede quantas páginas aparecem simultaneamente nos Top 10
    das diferentes centralidades.
    """

    colunas = [
        "degree_centrality",
        "closeness",
        "betweenness",
        "eigenvector_centrality",
        "pagerank",
    ]

    tops = {}

    for coluna in colunas:
        tops[coluna] = set(
            df.nlargest(TOP_N, coluna)["pagina"]
        )

    linhas = []

    for i, c1 in enumerate(colunas):
        for c2 in colunas[i + 1:]:
            intersecao = tops[c1] & tops[c2]

            linhas.append({
                "centralidade_1": c1,
                "centralidade_2": c2,
                "quantidade_em_comum_top_10": len(intersecao),
            })

    resultado = pd.DataFrame(linhas)

    resultado.to_csv(
        PASTA_RESULTADOS / "comparacao_top10_centralidades.csv",
        index=False,
        encoding="utf-8-sig"
    )

    return resultado


# ============================================================
# RELATÓRIO TXT
# ============================================================

def salvar_relatorio(metricas):

    with open(
        PASTA_RESULTADOS / "metricas.txt",
        "w",
        encoding="utf-8"
    ) as f:

        f.write("ANÁLISE DA REDE DA WIKIPÉDIA\n")
        f.write("=" * 60 + "\n\n")

        for nome, valor in metricas.items():

            if isinstance(valor, float):
                f.write(f"{nome}: {valor:.6f}\n")
            else:
                f.write(f"{nome}: {valor}\n")


# ============================================================
# PROGRAMA PRINCIPAL
# ============================================================

def main():

    arquivo = Path(ARQUIVO_REDE)

    if not arquivo.exists():
        print(f"ERRO: arquivo '{ARQUIVO_REDE}' não encontrado.")
        print("Coloque o analise.py na mesma pasta do rede_wikipedia.json.")
        return

    PASTA_RESULTADOS.mkdir(exist_ok=True)

    print("=" * 60)
    print("ANÁLISE DA REDE DA WIKIPÉDIA")
    print("=" * 60)

    # --------------------------------------------------------
    # Carregamento
    # --------------------------------------------------------

    G = carregar_rede(ARQUIVO_REDE)

    print(
        f"Rede carregada: {G.number_of_nodes()} nós, "
        f"{G.number_of_edges()} arestas"
    )

    # --------------------------------------------------------
    # Estrutura
    # --------------------------------------------------------

    metricas, graus_in, graus_out, graus_total, UG = analisar_estrutura(G)

    print()
    print("=" * 60)
    print("CARACTERIZAÇÃO ESTRUTURAL")
    print("=" * 60)

    nomes = {
        "numero_nos": "Número de nós",
        "numero_arestas": "Número de arestas",
        "grau_medio_total": "Grau médio total",
        "grau_medio_entrada": "In-degree médio",
        "grau_medio_saida": "Out-degree médio",
        "densidade": "Densidade",
        "clustering_coefficient_medio": "Clustering coefficient médio",
        "average_path_length_maior_componente": "Average path length (maior componente)",
        "diametro_maior_componente": "Diâmetro (maior componente)",
        "componentes_conexos": "Componentes conexos",
        "maior_componente_conexa_nos": "Nós na maior componente conexa",
        "componentes_fortemente_conexos": "Componentes fortemente conexos",
        "maior_componente_fortemente_conexa_nos": "Nós na maior componente fortemente conexa",
    }

    for chave, nome in nomes.items():

        valor = metricas[chave]

        if isinstance(valor, float):
            print(f"{nome}: {valor:.6f}")
        else:
            print(f"{nome}: {valor}")

    # --------------------------------------------------------
    # Centralidades
    # --------------------------------------------------------

    centralidades = analisar_centralidades(G, UG)

    imprimir_top_centralidades(centralidades)

    # --------------------------------------------------------
    # CSV de centralidades
    # --------------------------------------------------------

    df = gerar_tabela_centralidades(
        G,
        centralidades
    )

    # --------------------------------------------------------
    # Concordância dos Top 10
    # --------------------------------------------------------

    calcular_concordancia(df)

    # --------------------------------------------------------
    # Distribuição de graus
    # --------------------------------------------------------

    gerar_grafico_graus(
        graus_in,
        graus_out,
        graus_total
    )

    # --------------------------------------------------------
    # Relatório
    # --------------------------------------------------------

    salvar_relatorio(metricas)

    # --------------------------------------------------------
    # Resumo final
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("ARQUIVOS GERADOS")
    print("=" * 60)

    print("resultados/metricas.txt")
    print("resultados/centralidades.csv")
    print("resultados/comparacao_top10_centralidades.csv")
    print("resultados/distribuicao_grau_total.png")
    print("resultados/distribuicao_in_out_degree.png")

    print()
    print("Análise concluída.")


if __name__ == "__main__":
    main()