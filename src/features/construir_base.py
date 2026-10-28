"""Etapa 3 — base de modelagem: uma linha por Sprint x k, com variáveis calculadas só com eventos <= t_k.

t_k = Start_Date + k * (End_Date - Start_Date), k em {0,3; 0,5; 0,7}.
Unidade: story points (SP vigentes no início/na entrada do item) quando a cobertura de SP do escopo
comprometido é >= 70%; a contagem de itens é calculada sempre, como unidade alternativa.
Saída: data/processed/base_modelagem.csv (+ base_filtros.csv com o funil de filtros).
"""
import numpy as np
import pandas as pd

from src.data import carregar
from src.data.reconstrucao import STATUS_A_FAZER, STATUS_CONCLUIDO, LinhaDoTempo

KS = [0.3, 0.5, 0.7]
LIMIARES = [0.8, 0.9, 1.0]
DUR_MIN, DUR_MAX = 5, 31          # dias
MIN_COMPROMETIDOS = 5             # itens
MIN_COBERTURA_SP = 0.70
JANELA_VELOCIDADE = 3             # Sprints anteriores do mesmo projeto


def velocidade_anterior(resumo, entregue):
    """Média do entregue (SP ou itens) nas 3 Sprints anteriores do mesmo projeto já encerradas no início."""
    r = resumo.assign(entregue=entregue).sort_values("end_date")
    out = {}
    for _, g in r.groupby("projeto"):
        fins, valores = g.end_date.values, g.entregue.values
        for sid, ini in zip(g.sprint_id, g.start_date.values):
            k = np.searchsorted(fins, ini, side="right")  # só Sprints com End_Date <= início atual
            out[sid] = valores[k - JANELA_VELOCIDADE:k].mean() if k >= JANELA_VELOCIDADE else np.nan
    return pd.Series(out)


def entregue_total(itens, unidade):
    """Entregue até o fim (comprometidos + adicionados) por Sprint — usado só como histórico de velocidade."""
    v = itens[~itens.concluido_antes_inicio & (itens.concluido_em <= itens.fim)]
    peso = v.sp.fillna(0) if unidade == "sp" else pd.Series(1.0, index=v.index)
    return peso.groupby(v.sprint_id).sum()


def variaveis_k(it, inicio, fim, k, linha):
    t = inicio + k * (fim - inicio)
    it = it[~it.concluido_antes_inicio]
    comp = it[it.papel == "comprometido"]
    adic = it[(it.papel == "adicionado") & (it.t_in <= t)]
    feito = comp.concluido_em <= t
    removido = comp.removido_em <= t
    sp_comp = comp.sp.fillna(0).sum()
    ativos = pd.concat([comp[~removido], adic[~(adic.removido_em <= t)]])
    ativos = ativos[~(ativos.concluido_em <= t)]
    status = [linha.status_em(i, t) for i in ativos.issue_id]
    andamento = sum(s not in STATUS_A_FAZER and s not in STATUS_CONCLUIDO for s in status)
    n = len(comp)
    return {
        "pct_pontos_concluidos": comp.sp.fillna(0)[feito].sum() / sp_comp if sp_comp > 0 else np.nan,
        "pct_itens_concluidos": feito.sum() / n,
        "pontos_adicionados_rel": adic.sp.fillna(0).sum() / sp_comp if sp_comp > 0 else np.nan,
        "itens_adicionados_rel": len(adic) / n,
        "pontos_removidos_rel": comp.sp.fillna(0)[removido].sum() / sp_comp if sp_comp > 0 else np.nan,
        "itens_removidos_rel": removido.sum() / n,
        "itens_em_andamento_rel": andamento / n,
    }


def construir():
    itens = pd.read_csv(carregar.INTERIM / "itens_sprint.csv",
                        parse_dates=["t_in", "t_out", "inicio", "fim", "removido_em", "concluido_em"])
    resumo = pd.read_csv(carregar.INTERIM / "sprints_resumo.csv",
                         parse_dates=["start_date", "end_date", "complete_date"])
    resumo = resumo[resumo.n_comprometidos.notna()]

    # velocidade com todas as Sprints com datas (inclusive as que serão filtradas)
    vel_sp = velocidade_anterior(resumo, resumo.sprint_id.map(entregue_total(itens, "sp")).fillna(0).values)
    vel_it = velocidade_anterior(resumo, resumo.sprint_id.map(entregue_total(itens, "itens")).fillna(0).values)

    funil = [("Sprints na tabela Sprint", len(carregar.sprints()))]
    f = resumo
    funil.append(("com Start_Date e End_Date válidos", len(f)))
    f = f[f.state == "CLOSED"]; funil.append(("State = CLOSED", len(f)))
    f = f[f.duracao_dias.between(DUR_MIN, DUR_MAX)]; funil.append((f"duração {DUR_MIN}-{DUR_MAX} dias", len(f)))
    f = f[f.n_comprometidos >= MIN_COMPROMETIDOS]; funil.append((f">= {MIN_COMPROMETIDOS} itens comprometidos", len(f)))
    base_itens = f
    f = f[f.cobertura_sp >= MIN_COBERTURA_SP]; funil.append((f"cobertura de SP >= {MIN_COBERTURA_SP:.0%}", len(f)))
    f = f[f.sp_comprometidos > 0]; funil.append(("SP comprometidos > 0", len(f)))
    ids_sp = set(f.sprint_id)

    linha = LinhaDoTempo()
    por_sprint = dict(tuple(itens[itens.sprint_id.isin(base_itens.sprint_id)].groupby("sprint_id")))
    linhas = []
    for _, s in base_itens.iterrows():
        it = por_sprint[s.sprint_id]
        base = {
            "sprint_id": s.sprint_id, "projeto": s.projeto, "sprint_nome": s.sprint_nome,
            "start_date": s.start_date, "end_date": s.end_date, "duracao_dias": s.duracao_dias,
            "n_comprometidos": s.n_comprometidos, "sp_comprometidos": s.sp_comprometidos,
            "cobertura_sp": s.cobertura_sp, "usa_sp": s.sprint_id in ids_sp,
            "compromisso_vs_velocidade": s.sp_comprometidos / vel_sp.get(s.sprint_id, np.nan)
            if vel_sp.get(s.sprint_id, 0) > 0 else np.nan,
            "compromisso_vs_velocidade_itens": s.n_comprometidos / vel_it.get(s.sprint_id, np.nan)
            if vel_it.get(s.sprint_id, 0) > 0 else np.nan,
            "frac_sp_final": s.frac_sp, "frac_itens_final": s.frac_itens,
        }
        for L in LIMIARES:
            base[f"cumpriu_sp_L{int(L * 100)}"] = int(s.frac_sp >= L - 1e-9) if pd.notna(s.frac_sp) else np.nan
            base[f"cumpriu_itens_L{int(L * 100)}"] = int(s.frac_itens >= L - 1e-9)
        for k in KS:
            linhas.append({**base, "k": k, "pct_tempo": k, **variaveis_k(it, s.start_date, s.end_date, k, linha)})

    df = pd.DataFrame(linhas)
    return df, pd.DataFrame(funil, columns=["etapa", "n_sprints"])


if __name__ == "__main__":
    df, funil = construir()
    carregar.PROCESSED.mkdir(parents=True, exist_ok=True)
    df.to_csv(carregar.PROCESSED / "base_modelagem.csv", index=False)
    funil.to_csv(carregar.PROCESSED / "base_filtros.csv", index=False)
    print(funil.to_string(index=False))
    print(f"base_modelagem: {len(df)} linhas ({df.sprint_id.nunique()} Sprints; {df[df.usa_sp].sprint_id.nunique()} com SP)")
