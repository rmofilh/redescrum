"""Etapa 2 — prova de conceito: ~20 Sprints de 3 projetos, burndown diário e rótulo para L em {0,8; 0,9; 1,0}."""
import numpy as np
import pandas as pd

from src import viz
from src.data import carregar

PROJETOS_AMOSTRA = ["MESOS", "MULE", "TIMOB"]
N_POR_PROJETO = {"MESOS": 7, "MULE": 7, "TIMOB": 6}
LIMIARES = [0.8, 0.9, 1.0]
SEMENTE = 42
CITADAS = {"MULE_4351", "MESOS_425", "TIMOB_4697"}  # burndowns citados no relatório; só esses viram figura


def burndown(itens_sprint, inicio, fim, unidade="sp"):
    """Série diária: restante do escopo comprometido e restante total (comprometido + adicionado)."""
    dias = pd.date_range(inicio, fim, freq="D")
    if dias[-1] < fim:
        dias = dias.append(pd.DatetimeIndex([fim]))
    it = itens_sprint[~itens_sprint.concluido_antes_inicio].copy()
    it["peso"] = it.sp.fillna(0) if unidade == "sp" else 1.0
    linhas = []
    for t in dias:
        presente = (it.papel == "comprometido") | (it.t_in <= t)
        ativo = presente & ~(it.removido_em <= t)
        aberto = ativo & ~(it.concluido_em <= t)
        linhas.append({
            "t": t,
            "restante_comprometido": it.peso[aberto & (it.papel == "comprometido")].sum(),
            "restante_total": it.peso[aberto].sum(),
        })
    return pd.DataFrame(linhas)


def escolher(resumo):
    elegiveis = resumo[resumo.projeto.isin(PROJETOS_AMOSTRA) & (resumo.state == "CLOSED")
                       & resumo.duracao_dias.between(5, 31) & (resumo.n_comprometidos >= 5)
                       & (resumo.cobertura_sp >= 0.7)]
    return (elegiveis.groupby("projeto", group_keys=False)
            .apply(lambda g: g.sample(N_POR_PROJETO[g.name], random_state=SEMENTE)))


def plotar(sprint, bd, caminho):
    fig, ax = viz.plt.subplots(figsize=(6.4, 3.6))
    dia = (bd.t - sprint.start_date).dt.total_seconds() / 86400
    total0 = bd.restante_comprometido.iloc[0]
    ax.plot([0, sprint.duracao_dias], [total0, 0], color=viz.NEUTRO, lw=1.2, ls="--", label="ideal")
    ax.plot(dia, bd.restante_comprometido, color=viz.SERIES[0], drawstyle="steps-post",
            label="restante do comprometido")
    ax.plot(dia, bd.restante_total, color=viz.SERIES[1], drawstyle="steps-post",
            label="restante incl. adicionados")
    for k in (0.3, 0.5, 0.7):
        ax.axvline(k * sprint.duracao_dias, color="#d6d5cf", lw=0.8)
    ax.set_xlabel("dias desde o início")
    ax.set_ylabel("story points restantes")
    ax.set_ylim(bottom=0)
    ax.set_title(f"{sprint.projeto} — {sprint.sprint_nome}  (concluído: {sprint.frac_sp:.0%} dos SP comprometidos)",
                 loc="left")
    ax.legend(loc="lower left", fontsize=8)
    viz.salvar(fig, caminho)


def main():
    itens = pd.read_csv(carregar.INTERIM / "itens_sprint.csv",
                        parse_dates=["t_in", "t_out", "inicio", "fim", "removido_em", "concluido_em"])
    resumo = pd.read_csv(carregar.INTERIM / "sprints_resumo.csv", parse_dates=["start_date", "end_date"])
    am = escolher(resumo)
    for L in LIMIARES:
        am[f"cumpriu_L{int(L * 100)}"] = (am.frac_sp >= L - 1e-9).astype(int)
    destino = carregar.FIG / "burndown_amostra"
    destino.mkdir(parents=True, exist_ok=True)
    checagens = []
    for _, s in am.iterrows():
        it = itens[itens.sprint_id == s.sprint_id]
        bd = burndown(it, s.start_date, s.end_date)
        if f"{s.projeto}_{s.sprint_id}" in CITADAS:
            plotar(s, bd, destino / f"{s.projeto}_{s.sprint_id}.png")
        # coerência: burndown nunca sobe no escopo comprometido; restante final bate com o rótulo
        checagens.append({
            "sprint_id": s.sprint_id,
            "monotono": bool((bd.restante_comprometido.diff().fillna(0) <= 1e-9).all()),
            "restante_final_confere": bool(np.isclose(
                bd.restante_comprometido.iloc[-1] + s.sp_feitos
                + it[(it.papel == "comprometido") & ~it.concluido_antes_inicio & (it.removido_em <= s.end_date)
                     & ~(it.concluido_em <= s.end_date)].sp.fillna(0).sum(),
                s.sp_comprometidos)),
        })
    am = am.merge(pd.DataFrame(checagens), on="sprint_id")
    am.to_csv(carregar.INTERIM / "amostra_poc.csv", index=False)
    return am


if __name__ == "__main__":
    am = main()
    cols = ["projeto", "sprint_id", "sprint_nome", "duracao_dias", "n_comprometidos", "cobertura_sp",
            "sp_comprometidos", "n_adicionados", "n_removidos", "n_concluidos_antes_inicio", "frac_sp",
            "cumpriu_L80", "cumpriu_L90", "cumpriu_L100", "monotono", "restante_final_confere"]
    print(am[cols].round(2).to_string())
