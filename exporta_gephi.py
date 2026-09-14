import json
import networkx as nx

# Carregar rede
with open("rede_wikipedia.json", "r", encoding="utf-8") as f:
    dados = json.load(f)

G = nx.node_link_graph(dados, directed=True)

# Para visualização geral, usamos a versão não direcionada
H = G.to_undirected()

# =========================
# Métricas
# =========================

grau = dict(H.degree())
pagerank = nx.pagerank(G)

# Adicionar atributos aos nós
for no in H.nodes():
    H.nodes[no]["grau"] = grau[no]
    H.nodes[no]["pagerank"] = pagerank[no]

# =========================
# Exportar
# =========================

nx.write_gexf(H, "rede_wikipedia_gephi.gexf")

print("Arquivo criado: rede_wikipedia_gephi.gexf")