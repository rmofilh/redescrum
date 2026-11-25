"""Pergunta 3, passo 4: teste incremental de cada variável nova (triagem).

Cenário principal (SP, L = 0,8), separadamente em cada k:
  M0: logit(y) ~ pct_pontos_concluidos
  M1: logit(y) ~ pct_pontos_concluidos + variável
  - teste da razão de verossimilhança (LR) entre M0 e M1, 1 g.l. (supõe Sprints independentes);
  - versão agrupada: teste de Wald do coeficiente da variável em M1 com erros agrupados por projeto
    (statsmodels, cov_type="cluster"), porque Sprints do mesmo projeto não são independentes.
Os dois modelos usam as mesmas Sprints (casos completos da variável; só historico_cumprimento tem ausentes).
Variáveis entram na escala em que foram definidas (sem transformação).

Critério declarado antes de rodar: a variável passa se p < 0,05 na versão agrupada em pelo menos dois
dos três valores de k.
Saída: reports/artigo/q3_triagem.csv.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm
from scipy.stats import chi2

from src.artigo.variaveis_q3 import VARIAVEIS, carregar_variaveis
from src.data import carregar

L = 0.8
ALFA = 0.05
MIN_K_APROVADOS = 2
SAIDA = carregar.ROOT / "reports" / "artigo"


def base_principal():
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv")
    base = base[base.usa_sp]
    v = carregar_variaveis()
    v = v[v.unidade == "sp"].drop(columns="unidade")
    d = base.merge(v, on=["sprint_id", "k"], how="left", validate="one_to_one")
    return d.assign(y=(d.frac_sp_final >= L - 1e-9).astype(int))


def testar(d, var):
    g = d.dropna(subset=["pct_pontos_concluidos", var])
    X0 = sm.add_constant(g[["pct_pontos_concluidos"]])
    X1 = sm.add_constant(g[["pct_pontos_concluidos", var]])
    m0 = sm.Logit(g.y, X0).fit(disp=0)
    m1 = sm.Logit(g.y, X1).fit(disp=0)
    mc = sm.Logit(g.y, X1).fit(disp=0, cov_type="cluster", cov_kwds={"groups": g.projeto.astype("category").cat.codes})
    lr = 2 * (m1.llf - m0.llf)
    return {
        "n_sprints": len(g), "n_projetos": g.projeto.nunique(), "positivos": int(g.y.sum()),
        "media_variavel": g[var].mean(), "frac_nao_zero": (g[var] != 0).mean(),
        "coef": m1.params[var], "ep_ingenuo": m1.bse[var], "ep_agrupado": mc.bse[var],
        "lr_estatistica": lr, "p_lr": chi2.sf(lr, 1), "p_wald_agrupado": mc.pvalues[var],
        "auc_m0": _auc(g.y, m0.predict(X0)), "auc_m1": _auc(g.y, m1.predict(X1)),
    }


def _auc(y, s):
    from src.artigo.metricas import auc
    return auc(np.asarray(y), np.asarray(s))


def main():
    d = base_principal()
    linhas = []
    for var in VARIAVEIS:
        if d[var].notna().sum() == 0:
            print(f"{var}: sem valores (não construída), fora da triagem")
            continue
        for k, g in d.groupby("k"):
            linhas.append({"variavel": var, "k": k, **testar(g, var)})
    t = pd.DataFrame(linhas)
    t["significativo_agrupado"] = t.p_wald_agrupado < ALFA
    n_sig = t.groupby("variavel").significativo_agrupado.sum()
    t["passa"] = t.variavel.map(n_sig >= MIN_K_APROVADOS)
    SAIDA.mkdir(parents=True, exist_ok=True)
    t.to_csv(SAIDA / "q3_triagem.csv", index=False)
    cols = ["variavel", "k", "n_sprints", "coef", "p_lr", "p_wald_agrupado", "auc_m0", "auc_m1", "passa"]
    print(t[cols].to_string(index=False, float_format=lambda x: f"{x:.4g}"))
    return t


if __name__ == "__main__":
    main()
