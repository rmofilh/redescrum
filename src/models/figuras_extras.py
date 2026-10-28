"""Figura das matrizes de confusão em k = 0,5 (cenário principal), lida de reports/resultados/exp4_avaliacao.csv.

Saída: reports/figures/redes/exp4_matrizes_confusao_k05.png.
"""
import numpy as np
import pandas as pd

from src import viz
from src.data import carregar

RESULTADOS = carregar.ROOT / "reports" / "resultados"
MODELOS = [("B1 — burndown ideal", "B1 — burndown ideal"), ("Adaline", "Adaline")]
ROTULOS = [["VN", "FP"], ["FN", "VP"]]
LEGENDAS = [["Sprint em risco,\ncom alerta", "Sprint em risco,\nSEM alerta"], ["cumpriu, mas\ncom alerta falso", "cumpriu,\nreconhecida"]]
ACERTO, ERRO = "#dbe8f8", "#efeeea"


def figura_matrizes(aval, caminho, cenario="SP, L = 0,8", k=0.5):
    a = aval[(aval.cenario == cenario) & (aval.k == k)].set_index("modelo")
    fig, eixos = viz.plt.subplots(1, len(MODELOS), figsize=(10, 4.4))
    for ax, (nome, titulo) in zip(eixos, MODELOS):
        r = a.loc[nome]
        m = np.array([[r.VN, r.FP], [r.FN, r.VP]], dtype=int)
        for i in range(2):
            for j in range(2):
                ax.add_patch(viz.plt.Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=ACERTO if i == j else ERRO,
                                               edgecolor=viz.SUPERFICIE, lw=3))
                ax.text(j, i - 0.15, f"{ROTULOS[i][j]} = {m[i, j]}", ha="center", va="center", fontsize=14,
                        fontweight="bold", color=viz.TINTA)
                ax.text(j, i + 0.2, LEGENDAS[i][j], ha="center", va="center", fontsize=9, color=viz.TINTA_2)
        # o erro mais grave para o Scrum Master: Sprint em risco sem alerta (FP, com positivo = cumpriu)
        ax.add_patch(viz.plt.Rectangle((0.53, -0.47), 0.94, 0.94, fill=False, edgecolor=viz.SERIES[1], lw=2.5))
        ax.set_xlim(-0.5, 1.5); ax.set_ylim(1.5, -0.5); ax.set_aspect("equal")
        ax.set_xticks([0, 1], ["prevê: não cumpre\n(alerta)", "prevê: cumpre\n(sem alerta)"])
        ax.set_yticks([0, 1], ["real:\nnão cumpriu", "real:\ncumpriu"])
        ax.tick_params(length=0)
        ax.grid(False)
        for lado in ax.spines.values():
            lado.set_visible(False)
        ax.set_title(f"{titulo}\nacurácia balanceada {r.acuracia_balanceada:.2f} · AUC {r.auc:.2f}".replace(".", ","),
                     loc="left", fontsize=10)
    n = int(m.sum())
    fig.suptitle(f"Matrizes de confusão em k = {str(k).replace('.', ',')} — {cenario} — {n:_} Sprints".replace("_", "."),
                 x=0.01, ha="left", fontsize=11)
    fig.text(0.01, -0.02, "Contorno laranja: o erro mais grave para o Scrum Master (Sprint em risco que passa sem alerta).",
             fontsize=8.5, color=viz.TINTA_2)
    viz.salvar(fig, caminho)


def main():
    aval = pd.read_csv(RESULTADOS / "exp4_avaliacao.csv")
    figura_matrizes(aval, carregar.FIG / "redes" / "exp4_matrizes_confusao_k05.png")


if __name__ == "__main__":
    main()
