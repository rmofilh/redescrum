"""Reconstrói, para cada Sprint, o escopo comprometido, o escopo adicionado/removido e a conclusão dos itens.

Saídas em data/interim/:
- itens_sprint.csv   : uma linha por (Sprint, issue) que esteve na Sprint entre o início e o fim;
- sprints_resumo.csv : uma linha por Sprint, com contagens, cobertura de story points e frações concluídas.
"""
import numpy as np
import pandas as pd

from src.data import carregar
from src.data.reconstrucao import LinhaDoTempo, tabela_pertinencia

# Itens que entram até 1h após Start_Date contam como comprometidos (pico de entradas
# entre 15 min e 1 h após o início, efeito do ato de iniciar a Sprint no Jira).
TOLERANCIA_INICIO = pd.Timedelta(hours=1)


def reconstruir(pert=None, linha=None, sprints=None):
    sprints = carregar.sprints() if sprints is None else sprints
    if pert is None:
        pert, _ = tabela_pertinencia()
    linha = LinhaDoTempo() if linha is None else linha

    s = sprints.dropna(subset=["start_date", "end_date"]).set_index("sprint_id")
    p = pert.dropna(subset=["sprint_id"]).copy()
    p["sprint_id"] = p.sprint_id.astype(int)
    p = p[p.sprint_id.isin(s.index)]
    p["inicio"] = p.sprint_id.map(s.start_date)
    p["fim"] = p.sprint_id.map(s.end_date)
    corte = p.inicio + TOLERANCIA_INICIO
    t_out = p.t_out.fillna(pd.Timestamp.max)

    comprometido = (p.t_in <= corte) & (t_out > corte)
    adicionado = (p.t_in > corte) & (p.t_in <= p.fim)
    p = p[comprometido | adicionado].copy()
    p["papel"] = np.where(comprometido[p.index], "comprometido", "adicionado")
    # uma issue pode ter mais de um intervalo na mesma Sprint (saiu e voltou): fica o primeiro relevante
    p = p.sort_values("t_in").drop_duplicates(["sprint_id", "issue_id"])

    p["removido_em"] = p.t_out.where(p.t_out <= p.fim)
    # já concluído no início (status vigente) -> fora do compromisso; reabertos contam normalmente
    ref_status = p.inicio.where(p.papel == "comprometido", p.t_in)
    p["concluido_antes_inicio"] = [linha.concluido_em(i, t) for i, t in zip(p.issue_id, ref_status)]
    p["concluido_em"] = [linha.primeira_conclusao_apos(i, t) for i, t in zip(p.issue_id, ref_status)]
    # story points vigentes no início (comprometidos) ou na entrada (adicionados)
    ref = p.inicio.where(p.papel == "comprometido", p.t_in)
    p["sp"] = [linha.sp_em(i, t) for i, t in zip(p.issue_id, ref)]
    p["sp_final"] = [linha.sp_em(i, pd.Timestamp.max) for i in p.issue_id]
    return p, s


def resumo(itens, s):
    c = itens[(itens.papel == "comprometido") & ~itens.concluido_antes_inicio].copy()
    c["feito_ate_fim"] = c.concluido_em <= c.fim
    c["sp0"] = c.sp.fillna(0)
    g = c.groupby("sprint_id")
    r = pd.DataFrame({
        "n_comprometidos": g.size(),
        "n_com_sp": g.sp.apply(lambda x: x.notna().sum()),
        "sp_comprometidos": g.sp0.sum(),
        "n_feitos": g.feito_ate_fim.sum(),
        "sp_feitos": c[c.feito_ate_fim].groupby("sprint_id").sp0.sum(),
        "n_removidos": g.removido_em.apply(lambda x: x.notna().sum()),
    }).fillna({"sp_feitos": 0})
    r["cobertura_sp"] = r.n_com_sp / r.n_comprometidos
    r["frac_itens"] = r.n_feitos / r.n_comprometidos
    r["frac_sp"] = np.where(r.sp_comprometidos > 0, r.sp_feitos / r.sp_comprometidos.replace(0, np.nan), np.nan)

    a = itens[itens.papel == "adicionado"].groupby("sprint_id")
    r["n_adicionados"] = a.size()
    r["sp_adicionados"] = a.sp.sum()
    r["n_concluidos_antes_inicio"] = itens[itens.concluido_antes_inicio & (itens.papel == "comprometido")].groupby("sprint_id").size()
    r = r.fillna({"n_adicionados": 0, "sp_adicionados": 0, "n_concluidos_antes_inicio": 0})

    cols = ["sprint_nome", "projeto", "project_id", "state", "start_date", "end_date", "complete_date", "duracao_dias"]
    out = s[cols].join(r, how="left")
    out["n_comprometidos"] = out.n_comprometidos.fillna(0).astype(int)
    return out.reset_index()


if __name__ == "__main__":
    itens, s = reconstruir()
    carregar.INTERIM.mkdir(parents=True, exist_ok=True)
    itens.to_csv(carregar.INTERIM / "itens_sprint.csv", index=False)
    r = resumo(itens, s)
    r.to_csv(carregar.INTERIM / "sprints_resumo.csv", index=False)
    print(f"itens_sprint: {len(itens)} linhas; sprints_resumo: {len(r)} Sprints")
