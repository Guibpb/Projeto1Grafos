import requests
import networkx as nx
import json
import time
from collections import deque


# ============================================================
# CONFIGURAÇÕES
# ============================================================

PAGINA_INICIAL = "Ciência da Computação"

MAX_NOS = 500

# 0 = somente página inicial
# 1 = página inicial + links dela
# 2 = + links das páginas da primeira camada
PROFUNDIDADE_MAXIMA = 2

API_URL = "https://pt.wikipedia.org/w/api.php"

HEADERS = {
    "User-Agent": (
        "ProjetoGrafosUSP/1.0 "
        "(estudo academico; contato: guilherme.bpb@usp.br) "
        "Python-requests"
    )
}


# ============================================================
# SESSÃO
# ============================================================

session = requests.Session()
session.headers.update(HEADERS)


# ============================================================
# BUSCA LINKS DE UMA PÁGINA
# ============================================================

def obter_links(titulo):

    links = []

    params = {
        "action": "query",
        "format": "json",
        "titles": titulo,
        "prop": "links",
        "plnamespace": 0,
        "pllimit": "max",
    }

    while True:

        try:

            resposta = session.get(
                API_URL,
                params=params,
                timeout=30
            )

            resposta.raise_for_status()

            dados = resposta.json()

        except Exception as e:

            print(f"ERRO ao buscar '{titulo}': {e}")
            return links

        paginas = dados.get("query", {}).get("pages", {})

        for pagina in paginas.values():

            for link in pagina.get("links", []):

                titulo_link = link.get("title")

                if titulo_link:
                    links.append(titulo_link)

        # ----------------------------------------------------
        # PAGINAÇÃO DA API
        # ----------------------------------------------------

        if "continue" not in dados:
            break

        params.update(dados["continue"])

    return links


# ============================================================
# COLETA DOS NÓS
# ============================================================

def descobrir_nos():

    profundidades = {
        PAGINA_INICIAL: 0
    }

    fila = deque([
        PAGINA_INICIAL
    ])

    ordem = []

    print()
    print("=" * 60)
    print("FASE 1 - DESCOBRINDO OS NÓS")
    print("=" * 60)

    while fila:

        pagina = fila.popleft()

        profundidade = profundidades[pagina]

        ordem.append(pagina)

        print(
            f"[{len(ordem):4d}] "
            f"{pagina} "
            f"(profundidade {profundidade})"
        )

        # Não precisamos descobrir novos nós a partir dessa
        # camada.
        if profundidade >= PROFUNDIDADE_MAXIMA:
            continue

        links = obter_links(pagina)

        print(
            f"      {len(links)} links encontrados"
        )

        for destino in links:

            # Já conhecemos esse nó
            if destino in profundidades:
                continue

            # Não ultrapassar limite de nós
            if len(profundidades) >= MAX_NOS:
                break

            profundidades[destino] = profundidade + 1

            fila.append(destino)

        time.sleep(0.2)

        # Quando atingimos MAX_NOS, ainda precisamos terminar
        # apenas a fase de descoberta.
        if len(profundidades) >= MAX_NOS:
            break

    return profundidades


# ============================================================
# COLETA DAS ARESTAS
# ============================================================

def construir_rede(nos):

    G = nx.DiGraph()

    # Adiciona todos os nós primeiro
    for titulo, profundidade in nos.items():

        G.add_node(
            titulo,
            profundidade=profundidade
        )

    print()
    print("=" * 60)
    print("FASE 2 - DESCOBRINDO AS ARESTAS")
    print("=" * 60)

    total = len(nos)

    for contador, origem in enumerate(nos, start=1):

        print(
            f"[{contador:4d}/{total}] "
            f"{origem}"
        )

        links = obter_links(origem)

        arestas_adicionadas = 0

        for destino in links:

            # Só criamos a aresta se o destino fizer parte
            # da nossa amostra de nós.
            if destino in nos:

                G.add_edge(
                    origem,
                    destino
                )

                arestas_adicionadas += 1

        print(
            f"      Links encontrados: {len(links)} | "
            f"Arestas na rede: {arestas_adicionadas}"
        )

        time.sleep(0.2)

    return G


# ============================================================
# SALVAR
# ============================================================

def salvar_rede(G):

    dados = nx.node_link_data(G)

    with open(
        "rede_wikipedia.json",
        "w",
        encoding="utf-8"
    ) as arquivo:

        json.dump(
            dados,
            arquivo,
            ensure_ascii=False,
            indent=2
        )


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("COLETA DA REDE DA WIKIPÉDIA")
    print("=" * 60)

    print(f"Página inicial: {PAGINA_INICIAL}")
    print(f"Máximo de nós: {MAX_NOS}")
    print(f"Profundidade máxima: {PROFUNDIDADE_MAXIMA}")

    # --------------------------------------------------------
    # FASE 1
    # --------------------------------------------------------

    nos = descobrir_nos()

    print()
    print(
        f"Nós descobertos: {len(nos)}"
    )

    # --------------------------------------------------------
    # FASE 2
    # --------------------------------------------------------

    G = construir_rede(nos)

    # --------------------------------------------------------
    # RESULTADOS
    # --------------------------------------------------------

    print()
    print("=" * 60)
    print("RESULTADO FINAL")
    print("=" * 60)

    print(
        f"Número de nós: {G.number_of_nodes()}"
    )

    print(
        f"Número de arestas: {G.number_of_edges()}"
    )

    print(
        f"Densidade: {nx.density(G):.6f}"
    )

    componentes = nx.number_connected_components(
        G.to_undirected()
    )

    print(
        f"Componentes conexos: {componentes}"
    )

    componentes_fortes = (
        nx.number_strongly_connected_components(G)
    )

    print(
        f"Componentes fortemente conexos: "
        f"{componentes_fortes}"
    )

    salvar_rede(G)

    print()
    print("Rede salva em: rede_wikipedia.json")