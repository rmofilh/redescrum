"""Figuras do artigo (PNG, 300 dpi) a partir de reports/artigo/*.csv.

fig_diferencas.png  diferença de AUC e PR-AUC de cada modelo para o burndown calibrado, com IC 95%,
                    nos cenários "equipe nova" e "equipe com histórico" (cenário principal: SP, L = 0,8).
fig_calibracao.png  diagrama de confiabilidade em k = 0,5 (equipe nova).
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.data import carregar

SAIDA = carregar.ROOT / "reports" / "artigo"
FIG = SAIDA / "figuras"
TINTA, TINTA_2, GRADE = "#0b0b0b", "#52514e", "#e4e3df"
# paleta categórica de referência (3 primeiros slots: válidos para todos os pares, inclusive daltonismo)
CORES_K = {0.3: "#2a78d6", 0.5: "#eb6834", 0.7: "#1baf7a"}
MARCAS_K = {0.3: "o", 0.5: "s", 0.7: "D"}
NOMES = {
    "burndown_ideal": "Burndown ideal", "monte_carlo": "Monte Carlo", "reg_logistica": "Logistic regression",
    "mlp": "MLP", "gradient_boosting": "Gradient boosting", "mlp_curva": "MLP + curve",
}
ORDEM = ["burndown_ideal", "monte_carlo", "reg_logistica", "mlp", "gradient_boosting", "mlp_curva"]
DIVISOES = {"equipe_nova": "Unseen projects (new team)", "equipe_com_historico": "Temporal cuts (team with history)"}
METRICAS = {"auc": "Δ ROC-AUC", "pr_auc": "Δ PR-AUC"}

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8.5, "axes.edgecolor": TINTA_2,
                     "axes.labelcolor": TINTA, "xtick.color": TINTA_2, "ytick.color": TINTA_2,
                     "axes.spines.top": False, "axes.spines.right": False})


def fig_diferencas():
    d = pd.read_csv(SAIDA / "diferencas.csv")
    d = d[d.cenario == "principal"]
    fig, eixos = plt.subplots(2, 2, figsize=(7.2, 5.6), sharey=True)
    for i, (div, titulo) in enumerate(DIVISOES.items()):
        for j, (met, rotulo) in enumerate(METRICAS.items()):
            ax = eixos[i, j]
            ax.axvline(0, color=TINTA_2, lw=1)
            for n, mod in enumerate(ORDEM):
                for o, k in enumerate((0.3, 0.5, 0.7)):
                    r = d[(d.divisao == div) & (d.modelo == mod) & (d.metrica == met) & (d.k == k)]
                    if r.empty:
                        continue
                    r = r.iloc[0]
                    y = n + (o - 1) * 0.22
                    ax.plot([r.ic_inf, r.ic_sup], [y, y], color=CORES_K[k], lw=1.6, solid_capstyle="round")
                    ax.plot(r.diferenca, y, MARCAS_K[k], color=CORES_K[k], ms=5,
                            markeredgecolor="white", markeredgewidth=0.8,
                            label=f"k = {k}" if (n == 0 and i == 0 and j == 0) else None)
            ax.set_yticks(range(len(ORDEM)))
            ax.set_yticklabels([NOMES[m] for m in ORDEM])
            ax.invert_yaxis()
            ax.grid(axis="x", color=GRADE, lw=0.6)
            ax.set_axisbelow(True)
            ax.set_xlabel(f"{rotulo} vs. calibrated burndown")
            ax.set_title(titulo if j == 0 else "", loc="left", fontsize=9, color=TINTA)
    alcas, rotulos = eixos[0, 0].get_legend_handles_labels()
    fig.legend(alcas, rotulos, loc="upper center", ncol=3, fontsize=8, frameon=False,
               bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(FIG / "fig_diferencas.png", dpi=300)
    plt.close(fig)


def fig_calibracao(k=0.5):
    c = pd.read_csv(SAIDA / "calibracao.csv")
    c = c[c.k == k]
    mods = [("burndown_calibrado", "Calibrated burndown", "#2a78d6", "o"),
            ("monte_carlo", "Monte Carlo", "#eb6834", "s"),
            ("reg_logistica", "Logistic regression", "#1baf7a", "D"),
            ("mlp", "MLP", "#eda100", "^")]
    fig, ax = plt.subplots(figsize=(3.6, 3.4))
    ax.plot([0, 1], [0, 1], color=TINTA_2, lw=1, ls="--", label="Perfect calibration")
    for mod, nome, cor, marca in mods:
        g = c[c.modelo == mod].sort_values("prob_media")
        ax.plot(g.prob_media, g.frequencia_observada, color=cor, lw=1.5, marker=marca, ms=4.5,
                markeredgecolor="white", markeredgewidth=0.7, label=nome)
    ax.set_xlim(0, 0.8); ax.set_ylim(0, 0.8)
    ax.set_xlabel("Mean predicted probability (decile)")
    ax.set_ylabel("Observed frequency of meeting the commitment")
    ax.grid(color=GRADE, lw=0.6); ax.set_axisbelow(True)
    ax.legend(fontsize=7, frameon=False, loc="upper left")
    fig.tight_layout()
    fig.savefig(FIG / "fig_calibracao.png", dpi=300)
    plt.close(fig)


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    fig_diferencas()
    fig_calibracao()


if __name__ == "__main__":
    main()
