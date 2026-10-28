"""Curva média de pct_pontos_concluidos ao longo da Sprint, por classe (cenário principal: SP, L = 0,8).

Verifica se as Sprints que cumprem concentram entregas no fim (curva abaixo da diagonal do burndown ideal).
Mesma definição da base de modelagem (construir_base.variaveis_k): fração dos SP comprometidos, congelados no
início, concluída até t = início + fração_do_tempo × duração.
Saídas: reports/resultados/curva_media_concluido.csv e reports/figures/curva_media_concluido.png.
"""
import numpy as np
import pandas as pd

from src import viz
from src.data import carregar

FRACOES = np.round(np.arange(0, 1.0001, 0.05), 2)
L = 0.8


def curvas(itens, base):
    sprints = base[base.usa_sp].drop_duplicates("sprint_id")
    por_sprint = dict(tuple(itens[itens.sprint_id.isin(sprints.sprint_id)].groupby("sprint_id")))
    linhas = []
    for _, s in sprints.iterrows():
        it = por_sprint[s.sprint_id]
        comp = it[(it.papel == "comprometido") & ~it.concluido_antes_inicio]
        sp = comp.sp.fillna(0)
        cumpriu = int(s.frac_sp_final >= L - 1e-9)
        for f in FRACOES:
            t = s.start_date + f * (s.end_date - s.start_date)
            linhas.append({"sprint_id": s.sprint_id, "cumpriu": cumpriu, "pct_tempo": f,
                           "pct_concluido": sp[comp.concluido_em <= t].sum() / sp.sum()})
    return pd.DataFrame(linhas)


def resumir(c):
    return (c.groupby(["cumpriu", "pct_tempo"]).pct_concluido
            .agg(media="mean", mediana="median", q25=lambda x: x.quantile(0.25), q75=lambda x: x.quantile(0.75),
                 n_sprints="size").reset_index())


def figura(r, caminho):
    fig, ax = viz.plt.subplots(figsize=(6.4, 4.2))
    ax.plot([0, 1], [0, 1], ls="--", lw=1.2, color=viz.NEUTRO, label="burndown ideal (B1)")
    for i, (cls, rot) in enumerate([(1, "cumpriu (≥ 80%)"), (0, "não cumpriu")]):
        g = r[r.cumpriu == cls]
        ax.fill_between(g.pct_tempo, g.q25, g.q75, color=viz.SERIES[i], alpha=0.15, lw=0)
        ax.plot(g.pct_tempo, g.media, color=viz.SERIES[i], label=f"{rot}: média (faixa = quartis)")
        m = g[g.pct_tempo == 0.5].media.iloc[0]
        ax.plot([0.5], [m], "o", ms=8, color=viz.SERIES[i], mec=viz.SUPERFICIE, mew=2)
        ax.annotate(f"{m:.0%}", (0.5, m), xytext=(8, -4 if cls else 6), textcoords="offset points",
                    color=viz.TINTA, fontsize=9)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    ax.set_xlabel("fração do tempo da Sprint (pct_tempo)"); ax.set_ylabel("fração dos SP comprometidos concluída")
    ax.set_title("Curva média de conclusão — SP, L = 0,8 (1.166 Sprints)", loc="left")
    ax.legend(loc="upper left", fontsize=8)
    viz.salvar(fig, caminho)


def main():
    itens = pd.read_csv(carregar.INTERIM / "itens_sprint.csv", parse_dates=["concluido_em"])
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date", "end_date"])
    r = resumir(curvas(itens, base))
    r.to_csv(carregar.ROOT / "reports" / "resultados" / "curva_media_concluido.csv", index=False)
    figura(r, carregar.FIG / "curva_media_concluido.png")
    return r


if __name__ == "__main__":
    r = main()
    print(r[r.pct_tempo.isin([0.3, 0.5, 0.7, 1.0])].round(3).to_string(index=False))
