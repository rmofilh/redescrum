"""Experimentos com Perceptron, Adaline e PMC, no formato do livro (Silva, Spatti & Flauzino).

1. Perceptron e Adaline com 2 entradas (pct_tempo, pct_pontos_concluidos): 5 treinamentos com sementes
   diferentes; pesos finais, nº de épocas, convergência; curvas de erro por época.
2. Figura: Sprints coloridas por classe, diagonal do burndown ideal (B1) e retas aprendidas.
3. PMC com todas as variáveis: topologia (5, 10, 15) por validação cruzada; 5 treinamentos; loss_curve_.
4. Avaliação fora da dobra (GroupKFold por projeto) de B0, B1, Perceptron, Adaline e PMC em k = 0,3/0,5/0,7.

Cenários (decisões D1–D3 em reports/decisoes.md): principal SP com L = 0,8; robustez itens com L = 0,8;
sensibilidade SP com L = 0,8 sem o projeto DM.
Saídas: reports/resultados/*.csv e reports/figures/redes/*.png.
"""
import numpy as np
import pandas as pd
from sklearn.metrics import balanced_accuracy_score, confusion_matrix, roc_auc_score

from src import analise_sinal as A
from src import viz
from src.data import carregar
from src.models.redes import AdalineRede, PMCRede, PerceptronRede, escolher_topologia

SEMENTES = [1, 2, 3, 4, 5]
SEMENTE_AVALIACAO = 42
KS = [0.3, 0.5, 0.7]
SAIDA = carregar.ROOT / "reports" / "resultados"
FIG = carregar.FIG / "redes"
ENTRADAS_2 = ["pct_tempo", "pct_pontos_concluidos"]

CENARIOS = {
    "principal": ("SP, L = 0,8", "sp", 80, None),
    "robustez": ("itens, L = 0,8", "itens", 80, None),
    "sem_DM": ("SP, L = 0,8, sem DM", "sp", 80, "DM"),
}


def base_cenario(base, chave):
    _, unidade, L, excluir = CENARIOS[chave]
    d = A.preparar(base, unidade, L)
    if excluir:
        d = d[d.projeto != excluir].reset_index(drop=True)
    return d, A.variaveis(unidade)


# ---------- Experimentos 1 e 2: Perceptron e Adaline com 2 entradas ----------

def limiar_em(w, pct_tempo):
    """Valor de pct_pontos_concluidos sobre a reta w0 + w1·pct_tempo + w2·pct_concluido = 0."""
    return -(w[0] + w[1] * pct_tempo) / w[2]


def experimento_1(d):
    X, y = d[ENTRADAS_2].to_numpy(float), d.y.to_numpy()
    linhas, curvas = [], {"Perceptron": [], "Adaline": []}
    for classe in (PerceptronRede, AdalineRede):
        for s in SEMENTES:
            r = classe(semente=s, padronizar=False).treinar(X, y)
            curvas[r.nome].append(r.historico_)
            linhas.append({
                "rede": r.nome, "semente": s, "w0_limiar": r.w_[0], "w1_pct_tempo": r.w_[1],
                "w2_pct_concluido": r.w_[2], "epocas": r.n_epocas_, "convergiu": r.convergiu_,
                "erro_final": r.historico_[-1],
                "fronteira_em_k05": limiar_em(r.w_, 0.5),
                "acuracia_balanceada_treino": balanced_accuracy_score(y, r.prever(X)),
            })
    return pd.DataFrame(linhas), curvas


def figura_curvas_lineares(curvas, caminho):
    fig, (a1, a2) = viz.plt.subplots(1, 2, figsize=(9, 3.4))
    for i, h in enumerate(curvas["Perceptron"]):
        a1.plot(range(1, len(h) + 1), h, lw=1, color=viz.SERIES[i], label=f"semente {SEMENTES[i]}")
    a1.set_title("Perceptron — amostras classificadas errado", loc="left")
    a1.set_xlabel("época"); a1.set_ylabel("nº de erros")
    for i, h in enumerate(curvas["Adaline"]):
        a2.plot(range(1, len(h) + 1), h, lw=1.5, color=viz.SERIES[i], label=f"semente {SEMENTES[i]}")
    a2.set_title("Adaline — EQM por época", loc="left")
    a2.set_xlabel("época"); a2.set_ylabel("EQM (ponderado pelas classes)")
    a2.set_yscale("log")
    alcas, rot = a2.get_legend_handles_labels()
    fig.legend(alcas, rot, loc="lower center", ncol=5, fontsize=8, bbox_to_anchor=(0.5, -0.06))
    viz.salvar(fig, caminho)


def figura_fronteiras(d, tab, caminho):
    rng = np.random.default_rng(0)
    x = d.pct_tempo.to_numpy() + rng.uniform(-0.035, 0.035, len(d))
    yv = d.pct_pontos_concluidos.to_numpy()
    fig, ax = viz.plt.subplots(figsize=(7.2, 5))
    neg = d.y.to_numpy() == 0
    ax.scatter(x[neg], yv[neg], s=7, color="#b9b8b2", alpha=0.6, lw=0, label="não cumpriu")
    ax.scatter(x[~neg], yv[~neg], s=12, color=viz.SERIES[1], alpha=0.9, lw=0, label="cumpriu (L = 0,8)")
    xs = np.linspace(0.2, 0.8, 50)
    ax.plot(xs, xs, color=viz.TINTA_2, ls="--", lw=1.5, label="B1: burndown ideal (concluído = tempo)")
    for rede, cor in (("Perceptron", viz.SERIES[0]), ("Adaline", viz.SERIES[2])):
        t = tab[tab.rede == rede]
        for j, (_, r) in enumerate(t.iterrows()):
            w = [r.w0_limiar, r.w1_pct_tempo, r.w2_pct_concluido]
            ax.plot(xs, limiar_em(w, xs), color=cor, lw=2 if j == 0 else 1, alpha=1 if j == 0 else 0.5,
                    label=f"{rede} (5 sementes)" if j == 0 else None)
    ax.set_xlim(0.2, 0.8); ax.set_ylim(-0.02, 1.02)
    ax.set_xticks(KS)
    ax.set_xlabel("pct_tempo (k, com deslocamento horizontal aleatório só para visualização)")
    ax.set_ylabel("pct_pontos_concluidos")
    ax.set_title("Fronteiras de decisão com 2 entradas — SP, L = 0,8 (k = 0,3/0,5/0,7)", loc="left")
    ax.legend(loc="upper left", fontsize=8)
    viz.salvar(fig, caminho)


# ---------- Experimento 3: PMC com todas as variáveis ----------

def experimento_3(d, cols):
    X, y = d[cols].to_numpy(float), d.y.to_numpy()
    melhor, cv = escolher_topologia(X, y, d.projeto, n_dobras=5, semente=SEMENTE_AVALIACAO)
    linhas, curvas = [], []
    for s in SEMENTES:
        r = PMCRede(n_ocultos=melhor, semente=s).treinar(X, y)
        curvas.append(r.historico_)
        linhas.append({"semente": s, "n_ocultos": melhor, "erro_final_entropia_cruzada": r.erro_final_,
                       "epocas": r.n_epocas_, "convergiu": r.convergiu_,
                       "acuracia_balanceada_treino": balanced_accuracy_score(y, r.prever(X)),
                       "auc_treino": roc_auc_score(y, r.escore(X))})
    return melhor, pd.DataFrame(cv), pd.DataFrame(linhas), curvas


def figura_loss_pmc(curvas, n, caminho):
    fig, ax = viz.plt.subplots(figsize=(6.4, 3.6))
    for i, h in enumerate(curvas):
        ax.plot(range(1, len(h) + 1), h, lw=1.5, color=viz.SERIES[i], label=f"semente {SEMENTES[i]}")
    ax.set_xlabel("época"); ax.set_ylabel("perda (entropia cruzada)")
    ax.set_title(f"PMC — loss_curve_ (1 camada oculta, {n} neurônios, 5 sementes)", loc="left")
    ax.legend(fontsize=8)
    viz.salvar(fig, caminho)


# ---------- Experimento 4: avaliação fora da dobra ----------

def avaliar_cenario(d, cols):
    X, y = d[cols].to_numpy(float), d.y.to_numpy()
    divisoes, _ = A.divisao_por_projeto(d)  # as mesmas dobras da análise de sinal
    escores = {n: np.full(len(d), np.nan) for n in ("Perceptron", "Adaline", "PMC")}
    preds = {n: np.full(len(d), -1) for n in escores}
    topologias = []
    for i, (tr, te) in enumerate(divisoes):
        n, cv = escolher_topologia(X[tr], y[tr], d.projeto.to_numpy()[tr], n_dobras=3, semente=SEMENTE_AVALIACAO)
        topologias.append({"dobra": i + 1, "n_ocultos": n, **{f"auc_cv_{c['n_ocultos']}": c["auc_fora_da_dobra"] for c in cv}})
        for rede in (PerceptronRede(semente=SEMENTE_AVALIACAO), AdalineRede(semente=SEMENTE_AVALIACAO),
                     PMCRede(n_ocultos=n, semente=SEMENTE_AVALIACAO)):
            rede.treinar(X[tr], y[tr])
            escores[rede.nome][te] = rede.escore(X[te])
            preds[rede.nome][te] = rede.prever(X[te])

    linhas = []
    pct = cols[1]
    for k in KS:
        sel = (d.k == k).to_numpy()
        yk = y[sel]
        folga = (d[pct] - d.pct_tempo).to_numpy()[sel]
        candidatos = {"B0 — classe majoritária": (np.zeros(len(yk), int), np.zeros(len(yk))),
                      "B1 — burndown ideal": ((folga >= 0).astype(int), folga)}
        candidatos |= {n: (preds[n][sel], escores[n][sel]) for n in escores}
        for nome, (p, s) in candidatos.items():
            tn, fp, fn, tp = confusion_matrix(yk, p, labels=[0, 1]).ravel()
            linhas.append({"modelo": nome, "k": k, **A.metricas(yk, p, s), "VN": tn, "FP": fp, "FN": fn, "VP": tp})
    return pd.DataFrame(linhas), pd.DataFrame(topologias)


def figura_metrica_k(res, titulo, caminho):
    fig, eixos = viz.plt.subplots(1, 3, figsize=(11, 3.4), sharex=True)
    for ax, met, rot in zip(eixos, ["auc", "acuracia_balanceada", "f1"], ["AUC", "Acurácia balanceada", "F1"]):
        for i, (nome, g) in enumerate(res.groupby("modelo", sort=False)):
            if nome.startswith("B0") and met == "auc":
                continue
            ax.plot(g.k, g[met], ls="--" if nome.startswith("B") else "-", marker="o", ms=5,
                    color=viz.SERIES[i], label=nome)
        ax.set_title(rot, loc="left"); ax.set_xticks(KS); ax.set_xlabel("k")
        ax.set_ylim(0, 1)
    alcas, rotulos = eixos[1].get_legend_handles_labels()
    fig.legend(alcas, rotulos, loc="lower center", ncol=5, fontsize=8, bbox_to_anchor=(0.5, -0.07))
    fig.suptitle(f"Métrica × k — {titulo} — GroupKFold por projeto", x=0.01, ha="left", fontsize=11)
    viz.salvar(fig, caminho)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    FIG.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date"])
    d, cols = base_cenario(base, "principal")

    tab1, curvas = experimento_1(d)
    tab1.to_csv(SAIDA / "exp1_perceptron_adaline_2entradas.csv", index=False)
    figura_curvas_lineares(curvas, FIG / "exp1_curvas_treinamento.png")
    figura_fronteiras(d, tab1, FIG / "exp2_fronteiras_2entradas.png")
    print("exp1/2 ok")

    n, cv, tab3, curvas3 = experimento_3(d, cols)
    cv.to_csv(SAIDA / "exp3_pmc_topologias_cv.csv", index=False)
    tab3.to_csv(SAIDA / "exp3_pmc_treinamentos.csv", index=False)
    figura_loss_pmc(curvas3, n, FIG / "exp3_pmc_loss_curve.png")
    print(f"exp3 ok (topologia {n})")

    todos, topos = [], []
    for chave, (titulo, *_rest) in CENARIOS.items():
        dc, cc = base_cenario(base, chave)
        res, top = avaliar_cenario(dc, cc)
        res = res.assign(cenario=titulo, n_sprints=dc.sprint_id.nunique(), n_projetos=dc.projeto.nunique(),
                         pct_positivos=dc[dc.k == 0.5].y.mean())
        todos.append(res); topos.append(top.assign(cenario=titulo))
        figura_metrica_k(res, titulo, FIG / f"exp4_metrica_vs_k_{chave}.png")
        print(f"exp4 {chave} ok")
    pd.concat(todos).to_csv(SAIDA / "exp4_avaliacao.csv", index=False)
    pd.concat(topos).to_csv(SAIDA / "exp4_topologias_por_dobra.csv", index=False)


if __name__ == "__main__":
    main()
