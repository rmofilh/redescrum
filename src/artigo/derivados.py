"""Insumos derivados para o artigo, calculados a partir de data/interim/itens_sprint.csv.

1. Entregas diárias de cada Sprint (itens comprometidos concluídos por dia de calendário).
2. Monte Carlo: probabilidade de a Sprint atingir L do compromisso, sorteando entregas diárias
   das 3 Sprints anteriores do mesmo projeto (encerradas antes do início da Sprint avaliada).
3. Curva do burndown amostrada em 10 pontos de tempo até k (entrada do MLP sobre a curva).

Nada aqui usa informação posterior a t_k da Sprint avaliada: o Monte Carlo só usa Sprints já
encerradas antes do início e o que a própria Sprint concluiu até t_k.
Saídas: data/processed/monte_carlo.csv e data/processed/curvas.csv.
"""
import numpy as np
import pandas as pd

from src.data import carregar

KS = [0.3, 0.5, 0.7]
LS = [0.6, 0.7, 0.8]
N_SIM = 5000
JANELA = 3            # Sprints anteriores usadas como histórico
N_PONTOS_CURVA = 10   # pontos da curva entre 0 e t_k
SEMENTE = 42


def carregar_itens():
    it = pd.read_csv(carregar.INTERIM / "itens_sprint.csv",
                     parse_dates=["t_in", "t_out", "inicio", "fim", "removido_em", "concluido_em"])
    c = it[(it.papel == "comprometido") & ~it.concluido_antes_inicio].copy()
    c["peso_sp"] = c.sp.fillna(0)
    c["peso_itens"] = 1.0
    return c


def entregas_diarias(c, resumo):
    """{(sprint_id, unidade): vetor com o entregue em cada dia de calendário da Sprint}."""
    out = {}
    dur = resumo.set_index("sprint_id").duracao_dias
    for sid, g in c.groupby("sprint_id"):
        n_dias = int(np.ceil(dur.get(sid, np.nan))) if pd.notna(dur.get(sid, np.nan)) else 0
        if n_dias <= 0:
            continue
        feito = g[g.concluido_em <= g.fim]
        dia = ((feito.concluido_em - feito.inicio).dt.total_seconds() // 86400).clip(0, n_dias - 1).astype(int)
        for u in ("sp", "itens"):
            out[(sid, u)] = np.bincount(dia, weights=feito[f"peso_{u}"], minlength=n_dias).astype(float)
    return out


def historico_anterior(resumo):
    """{sprint_id: [ids das até 3 Sprints anteriores do mesmo projeto, encerradas antes do início]}."""
    r = resumo.dropna(subset=["start_date", "end_date"]).sort_values("end_date")
    out = {}
    for _, g in r.groupby("projeto"):
        fins, ids = g.end_date.values, g.sprint_id.values
        for sid, ini in zip(g.sprint_id, g.start_date.values):
            k = np.searchsorted(fins, ini, side="right")
            out[sid] = list(ids[max(0, k - JANELA):k])
    return out


def monte_carlo(base, c, diarias, hist, rng):
    linhas = []
    comp = {u: c.groupby("sprint_id")[f"peso_{u}"].sum() for u in ("sp", "itens")}
    for _, s in base.iterrows():
        dur = s.duracao_dias
        for u in ("sp", "itens"):
            if u == "sp" and not s.usa_sp:
                continue
            C = comp[u].get(s.sprint_id, 0.0)
            if C <= 0:
                continue
            pct = s.pct_pontos_concluidos if u == "sp" else s.pct_itens_concluidos
            feito_k = pct * C
            restante = max(1, int(round((1 - s.k) * dur)))
            pool = [diarias[(p, u)] for p in hist.get(s.sprint_id, []) if (p, u) in diarias]
            if len(pool) >= 1:
                fonte = "historico_3" if len(pool) == JANELA else f"historico_{len(pool)}"
                amostra = np.concatenate(pool)
            else:
                # sem nenhuma Sprint anterior: usa o ritmo diário da própria Sprint até t_k
                fonte = "propria_sprint"
                d = diarias.get((s.sprint_id, u))
                dias_k = max(1, int(np.floor(s.k * dur)))
                amostra = d[:dias_k] if d is not None else np.zeros(1)
            sims = rng.choice(amostra, size=(N_SIM, restante), replace=True).sum(axis=1)
            linha = {"sprint_id": s.sprint_id, "k": s.k, "unidade": u, "fonte": fonte,
                     "n_sprints_historico": len(pool), "dias_restantes": restante}
            for L in LS:
                linha[f"p_mc_L{int(L * 100)}"] = float(np.mean(feito_k + sims >= L * C - 1e-9))
            linhas.append(linha)
    return pd.DataFrame(linhas)


def curvas(base, c):
    """Fração concluída do compromisso em t_j = início + (j/10)·k·duração, j = 1..10."""
    linhas = []
    por = dict(tuple(c.groupby("sprint_id")))
    for _, s in base.iterrows():
        g = por.get(s.sprint_id)
        if g is None:
            continue
        inicio = pd.Timestamp(s.start_date)
        dur = pd.Timedelta(days=s.duracao_dias)
        conc = g.concluido_em.values
        for u in ("sp", "itens"):
            peso = g[f"peso_{u}"].values
            C = peso.sum()
            if C <= 0:
                continue
            linha = {"sprint_id": s.sprint_id, "k": s.k, "unidade": u}
            for j in range(1, N_PONTOS_CURVA + 1):
                t = np.datetime64(inicio + dur * (s.k * j / N_PONTOS_CURVA))
                feito = (~pd.isna(conc)) & (conc <= t)
                linha[f"c{j:02d}"] = peso[feito].sum() / C
            linhas.append(linha)
    return pd.DataFrame(linhas)


def main():
    rng = np.random.default_rng(SEMENTE)
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date", "end_date"])
    resumo = pd.read_csv(carregar.INTERIM / "sprints_resumo.csv", parse_dates=["start_date", "end_date"])
    resumo = resumo[resumo.n_comprometidos.notna()]
    c = carregar_itens()
    diarias = entregas_diarias(c, resumo)
    hist = historico_anterior(resumo)
    mc = monte_carlo(base, c, diarias, hist, rng)
    mc.to_csv(carregar.PROCESSED / "monte_carlo.csv", index=False)
    cv = curvas(base, c)
    cv.to_csv(carregar.PROCESSED / "curvas.csv", index=False)
    print("monte_carlo:", len(mc), "linhas;", mc[mc.k == 0.5].groupby("unidade").fonte.value_counts().to_dict())
    print("curvas:", len(cv), "linhas")


if __name__ == "__main__":
    main()
