import json
import math
import os

import matplotlib.pyplot as plt
import networkx as nx
import pandas as pd

ARQUIVO_REDE = "rede_wikipedia.json"
PASTA_RESULTADOS = "resultados"
N_REPETICOES = 10
SEED = 42
WS_P = 0.10


def carregar_rede():
    with open(ARQUIVO_REDE, "r", encoding="utf-8") as f:
        dados = json.load(f)
    return nx.node_link_graph(dados, directed=True)


def preparar_rede(G):
    # Os modelos clássicos usados aqui são não direcionados.
    return nx.Graph(G) if G.is_directed() else G.copy()


def maior_componente(G):
    if not G:
        return G.copy()
    c = max(nx.connected_components(G), key=len)
    return G.subgraph(c).copy()


def metricas(G):
    G = preparar_rede(G)
    n, m = G.number_of_nodes(), G.number_of_edges()
    if n == 0:
        return {"nos":0,"arestas":0,"grau_medio":0.0,"densidade":0.0,
                "clustering":0.0,"average_path_length":0.0,"diametro":0,
                "componentes":0,"maior_componente":0}
    H = maior_componente(G)
    return {
        "nos": n,
        "arestas": m,
        "grau_medio": 2*m/n,
        "densidade": nx.density(G) if n > 1 else 0.0,
        "clustering": nx.average_clustering(G),
        "average_path_length": nx.average_shortest_path_length(H) if H.number_of_nodes() > 1 else 0.0,
        "diametro": nx.diameter(H) if H.number_of_nodes() > 1 else 0,
        "componentes": nx.number_connected_components(G),
        "maior_componente": H.number_of_nodes(),
    }


def parametros(n, m):
    grau = 2*m/n
    k = max(2, int(round(grau)))
    if k % 2: k -= 1
    k = min(k, n-1)
    if k % 2: k -= 1
    m_ba = max(1, min(n-1, int(round(grau/2))))
    # BA: m_initial + m*(n-m_initial), with m_initial=m in NetworkX.
    arestas_ba = m_ba*(n - m_ba) + m_ba*(m_ba-1)//2
    return {"grau_real":grau, "k_ws":k, "arestas_ws":n*k//2, "p_ws":WS_P,
            "m_ba":m_ba, "arestas_ba":arestas_ba}


def gerar_modelos(n, m, pars, rep):
    return (
        nx.gnm_random_graph(n, m, seed=SEED + rep),
        nx.watts_strogatz_graph(n, pars["k_ws"], pars["p_ws"], seed=SEED+1000+rep),
        nx.barabasi_albert_graph(n, pars["m_ba"], seed=SEED+2000+rep),
    )


def grau_frequencia(G):
    G = preparar_rede(G)
    graus = [d for _, d in G.degree()]
    if not graus:
        return [], []
    cont = {}
    for d in graus: cont[d] = cont.get(d, 0) + 1
    xs = sorted(cont)
    return xs, [cont[x]/len(graus) for x in xs]


def salvar_graficos(grafos, medias):
    caminhos=[]
    plt.figure(figsize=(10,6))
    for nome,G in grafos.items():
        x,y=grau_frequencia(G)
        if x: plt.plot(x,y,marker="o",markersize=3,linewidth=1,label=nome)
    plt.xlabel("Grau"); plt.ylabel("Frequência relativa")
    plt.title("Distribuição de grau: rede real vs. modelos")
    plt.legend(); plt.grid(alpha=.25); plt.tight_layout()
    p=os.path.join(PASTA_RESULTADOS,"distribuicao_grau_modelos.png"); plt.savefig(p,dpi=300); plt.close(); caminhos.append(p)

    plt.figure(figsize=(10,6))
    for nome,G in grafos.items():
        graus=sorted([d for _,d in preparar_rede(G).degree()], reverse=True)
        if not graus: continue
        xs=sorted(set(graus)); n=len(graus)
        ys=[sum(d>=k for d in graus)/n for k in xs]
        xy=[(k,y) for k,y in zip(xs,ys) if k>0 and y>0]
        if xy: plt.loglog([a for a,_ in xy],[b for _,b in xy],marker="o",markersize=3,linewidth=1,label=nome)
    plt.xlabel("Grau"); plt.ylabel("P(K ≥ k)")
    plt.title("CCDF da distribuição de grau")
    plt.legend(); plt.grid(alpha=.25); plt.tight_layout()
    p=os.path.join(PASTA_RESULTADOS,"ccdf_grau_modelos.png"); plt.savefig(p,dpi=300); plt.close(); caminhos.append(p)

    for col, ylabel, fn in [("clustering","Clustering médio","comparacao_clustering.png"),("average_path_length","Average path length","comparacao_path_length.png")]:
        plt.figure(figsize=(9,6)); medias.set_index("modelo")[col].plot(kind="bar",rot=0)
        plt.xlabel(""); plt.ylabel(ylabel); plt.title(ylabel+": rede real vs. modelos")
        plt.grid(axis="y",alpha=.25); plt.tight_layout()
        p=os.path.join(PASTA_RESULTADOS,fn); plt.savefig(p,dpi=300); plt.close(); caminhos.append(p)
    return caminhos


def salvar_tabelas(df, real, pars):
    metricas_cols=["nos","arestas","grau_medio","densidade","clustering","average_path_length","diametro","componentes","maior_componente"]
    df.to_csv(os.path.join(PASTA_RESULTADOS,"modelos_detalhado.csv"),index=False,encoding="utf-8-sig")
    aleat=df[df.modelo!="Rede real"]
    medias=aleat.groupby("modelo")[metricas_cols].mean().reset_index()
    linha=pd.Series(real)[metricas_cols].to_frame().T; linha.insert(0,"modelo","Rede real")
    medias_final=pd.concat([linha,medias],ignore_index=True)
    medias_final.to_csv(os.path.join(PASTA_RESULTADOS,"comparacao_modelos.csv"),index=False,encoding="utf-8-sig")
    desv=aleat.groupby("modelo")[metricas_cols].std().reset_index()
    desv.to_csv(os.path.join(PASTA_RESULTADOS,"comparacao_modelos_desvio.csv"),index=False,encoding="utf-8-sig")

    erros=[]
    for _,row in medias.iterrows():
        r={"modelo":row.modelo}
        for c in ["grau_medio","clustering","average_path_length","diametro"]:
            r["erro_absoluto_"+c]=abs(row[c]-real[c])
            r["erro_relativo_"+c]=abs(row[c]-real[c])/abs(real[c]) if real[c] else math.nan
        erros.append(r)
    pd.DataFrame(erros).to_csv(os.path.join(PASTA_RESULTADOS,"comparacao_erros_modelos.csv"),index=False,encoding="utf-8-sig")

    # Texto com uma comparação direta.
    with open(os.path.join(PASTA_RESULTADOS,"comparacao_modelos.txt"),"w",encoding="utf-8") as f:
        f.write("COMPARAÇÃO DA REDE DA WIKIPÉDIA COM MODELOS CLÁSSICOS\n")
        f.write("="*70+"\n\n")
        f.write("A rede real foi convertida de direcionada para não direcionada para a comparação.\n\n")
        f.write(f"Rede real: n={int(real['nos'])}, m={int(real['arestas'])}, grau médio={real['grau_medio']:.6f}\n")
        f.write(f"ER: G(n,m), n={int(real['nos'])}, m={int(real['arestas'])}\n")
        f.write(f"WS: n={int(real['nos'])}, k={pars['k_ws']}, p={pars['p_ws']}, arestas={pars['arestas_ws']}\n")
        f.write(f"BA: n={int(real['nos'])}, m={pars['m_ba']}, arestas={pars['arestas_ba']}\n\n")
        f.write("MODELO MAIS PRÓXIMO DA REDE REAL\n")
        for c,nome in [("clustering","Clustering"),("average_path_length","Average path length"),("grau_medio","Grau médio"),("diametro","Diâmetro")]:
            dif=aleat.groupby("modelo")[c].mean().sub(real[c]).abs(); f.write(f"{nome}: {dif.idxmin()}\n")
    return medias_final


def main():
    os.makedirs(PASTA_RESULTADOS,exist_ok=True)
    G=carregar_rede(); real=preparar_rede(G); n,m=real.number_of_nodes(),real.number_of_edges()
    real_met=metricas(real)
    pars=parametros(n,m)
    print("="*60); print("COMPARAÇÃO COM MODELOS CLÁSSICOS"); print("="*60)
    print(f"Rede carregada: {G.number_of_nodes()} nós, {G.number_of_edges()} arestas")
    print(f"Rede real para comparação: {n} nós, {m} arestas")
    print(f"Grau médio: {real_met['grau_medio']:.6f}")
    print(f"WS: k={pars['k_ws']}, p={pars['p_ws']}, arestas={pars['arestas_ws']}")
    print(f"BA: m={pars['m_ba']}, arestas={pars['arestas_ba']}")

    resultados=[dict(real_met,modelo="Rede real",repeticao=0)]
    modelos_amostra=None
    for rep in range(1,N_REPETICOES+1):
        ER,WS,BA=gerar_modelos(n,m,pars,rep)
        atuais={"Erdős–Rényi":ER,"Watts–Strogatz":WS,"Barabási–Albert":BA}
        if rep==1: modelos_amostra=atuais
        for nome,H in atuais.items():
            r=metricas(H); r["modelo"]=nome; r["repeticao"]=rep; resultados.append(r)
        print(f"Repetição {rep}/{N_REPETICOES} concluída")

    df=pd.DataFrame(resultados)
    medias=salvar_tabelas(df,real_met,pars)
    graficos=salvar_graficos({"Rede real":real,**modelos_amostra},medias)
    print("\nCOMPARAÇÃO FINAL")
    print(medias[["modelo","nos","arestas","grau_medio","densidade","clustering","average_path_length","diametro"]].to_string(index=False))
    print("\nARQUIVOS GERADOS")
    for nome in ["modelos_detalhado.csv","comparacao_modelos.csv","comparacao_modelos_desvio.csv","comparacao_erros_modelos.csv","comparacao_modelos.txt",* [os.path.basename(x) for x in graficos]]:
        print(os.path.join(PASTA_RESULTADOS,nome))

if __name__=="__main__":
    main()