"""Métricas e intervalos de confiança por reamostragem de projetos (bootstrap agrupado).

Para cada cenário × divisão × k:
  - AUC-ROC, PR-AUC (precisão média), Brier, Brier skill score, acurácia balanceada e F1;
  - intervalo de 95% de cada métrica, sorteando projetos com reposição (B = 2000);
  - diferença de cada modelo para o burndown_calibrado (AUC, PR-AUC, Brier), com intervalo de 95%.
Entrada: reports/artigo/predicoes.csv. Saídas: reports/artigo/metricas.csv, diferencas.csv,
por_projeto.csv e calibracao.csv.
"""
import numpy as np
import pandas as pd
from scipy.stats import rankdata
from sklearn.metrics import balanced_accuracy_score, f1_score

from src.data import carregar

B = 2000
SEMENTE = 7
REF = "burndown_calibrado"
SAIDA = carregar.ROOT / "reports" / "artigo"


def auc(y, s):
    n1 = y.sum(); n0 = len(y) - n1
    if n1 == 0 or n0 == 0:
        return np.nan
    r = rankdata(s)
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def pr_auc(y, s):
    """Precisão média (mesma definição do scikit-learn)."""
    if y.sum() == 0:
        return np.nan
    o = np.argsort(-s, kind="mergesort")
    s, y = s[o], y[o]
    idx = np.r_[np.flatnonzero(np.diff(s)), len(y) - 1]
    tp = np.cumsum(y)[idx]
    fp = idx + 1 - tp
    prec = tp / (tp + fp)
    rec = tp / tp[-1]
    return np.sum(np.diff(np.r_[0, rec]) * prec)


def brier(y, p):
    return np.nan if np.isnan(p).all() else np.mean((p - y) ** 2)


def bss(y, p):
    pi = y.mean()
    ref = pi * (1 - pi)
    return np.nan if ref == 0 or np.isnan(p).all() else 1 - brier(y, p) / ref


def metricas_ponto(y, esc, prob, pred):
    return {
        "auc": auc(y, esc), "pr_auc": pr_auc(y, esc), "brier": brier(y, prob), "bss": bss(y, prob),
        "acuracia_balanceada": balanced_accuracy_score(y, pred), "f1": f1_score(y, pred, zero_division=0),
    }


def blocos(p):
    """Matrizes por modelo (linhas alinhadas por Sprint) e índice de linhas por projeto."""
    largo = {}
    for c in ("escore", "prob", "pred"):
        largo[c] = p.set_index(["sprint_id", "projeto", "y", "modelo"])[c].unstack("modelo")
    idx = largo["escore"].index.to_frame(index=False)
    grupos = {pr: np.flatnonzero(idx.projeto.to_numpy() == pr) for pr in idx.projeto.unique()}
    return largo, idx.y.to_numpy().astype(int), grupos


def avaliar_grupo(p, rng):
    largo, y, grupos = blocos(p)
    modelos = list(largo["escore"].columns)
    E = {m: largo["escore"][m].to_numpy(float) for m in modelos}
    P = {m: largo["prob"][m].to_numpy(float) for m in modelos}
    D = {m: largo["pred"][m].to_numpy(float).astype(int) for m in modelos}
    ponto = {m: metricas_ponto(y, E[m], P[m], D[m]) for m in modelos}

    projetos = list(grupos)
    amostras = {m: {"auc": [], "pr_auc": [], "brier": [], "bss": []} for m in modelos}
    for _ in range(B):
        sel = rng.choice(len(projetos), len(projetos), replace=True)
        ii = np.concatenate([grupos[projetos[j]] for j in sel])
        yb = y[ii]
        if yb.sum() == 0 or yb.sum() == len(yb):
            continue
        for m in modelos:
            a = amostras[m]
            a["auc"].append(auc(yb, E[m][ii]))
            a["pr_auc"].append(pr_auc(yb, E[m][ii]))
            a["brier"].append(brier(yb, P[m][ii]))
            a["bss"].append(bss(yb, P[m][ii]))

    linhas, difs = [], []
    for m in modelos:
        lin = {"modelo": m, "n_sprints": len(y), "n_projetos": len(projetos), "positivos": int(y.sum()),
               "prevalencia": y.mean(), **ponto[m]}
        for met in ("auc", "pr_auc", "brier", "bss"):
            v = np.array(amostras[m][met], float)
            lin[f"{met}_ic_inf"], lin[f"{met}_ic_sup"] = (np.nanpercentile(v, [2.5, 97.5])
                                                          if np.isfinite(v).any() else (np.nan, np.nan))
        linhas.append(lin)
        if m == REF:
            continue
        for met in ("auc", "pr_auc", "brier"):
            v = np.array(amostras[m][met], float) - np.array(amostras[REF][met], float)
            if not np.isfinite(v).any():
                continue
            difs.append({"modelo": m, "metrica": met, "diferenca": ponto[m][met] - ponto[REF][met],
                         "ic_inf": np.nanpercentile(v, 2.5), "ic_sup": np.nanpercentile(v, 97.5),
                         "frac_bootstrap_melhor_que_ref": np.nanmean(v < 0) if met == "brier" else np.nanmean(v > 0)})
    return pd.DataFrame(linhas), pd.DataFrame(difs)


def por_projeto(p, min_pos=10):
    s = p[(p.cenario == "principal") & (p.divisao == "equipe_nova") & (p.k == 0.5)]
    pos = s[s.modelo == REF].groupby("projeto").y.sum()
    linhas = []
    for pr in pos[pos >= min_pos].index:
        g = s[s.projeto == pr]
        for m, h in g.groupby("modelo"):
            linhas.append({"projeto": pr, "modelo": m, "n_sprints": len(h), "positivos": int(h.y.sum()),
                           "auc": auc(h.y.to_numpy(), h.escore.to_numpy()),
                           "pr_auc": pr_auc(h.y.to_numpy(), h.escore.to_numpy())})
    return pd.DataFrame(linhas)


def calibracao(p, n_bins=10):
    s = p[(p.cenario == "principal") & (p.divisao == "equipe_nova") & p.prob.notna()]
    linhas = []
    for (m, k), g in s.groupby(["modelo", "k"]):
        bins = pd.qcut(g.prob.rank(method="first"), n_bins, labels=False)
        for b, h in g.groupby(bins):
            linhas.append({"modelo": m, "k": k, "faixa": int(b), "prob_media": h.prob.mean(),
                           "frequencia_observada": h.y.mean(), "n": len(h)})
    return pd.DataFrame(linhas)


def main(sufixo=""):
    rng = np.random.default_rng(SEMENTE)
    p = pd.read_csv(SAIDA / f"predicoes{sufixo}.csv")
    mets, difs = [], []
    for (cen, div, k), g in p.groupby(["cenario", "divisao", "k"], sort=False):
        m, d = avaliar_grupo(g, rng)
        for t in (m, d):
            t.insert(0, "k", k); t.insert(0, "divisao", div); t.insert(0, "cenario", cen)
        mets.append(m); difs.append(d)
        print(f"{cen}/{div} k={k}: ok", flush=True)
    pd.concat(mets).to_csv(SAIDA / f"metricas{sufixo}.csv", index=False)
    pd.concat(difs).to_csv(SAIDA / f"diferencas{sufixo}.csv", index=False)
    if not sufixo:
        por_projeto(p).to_csv(SAIDA / "por_projeto.csv", index=False)
        calibracao(p).to_csv(SAIDA / "calibracao.csv", index=False)


if __name__ == "__main__":
    import sys
    main("_grade_estendida" if "--grade-estendida" in sys.argv else "_q3" if "--q3" in sys.argv else "")
