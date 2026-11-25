"""Gera as tabelas em Markdown usadas em reports/artigo/resumo_resultados.md (números direto dos CSVs)."""
import pandas as pd

from src.data import carregar

SAIDA = carregar.ROOT / "reports" / "artigo"
NOMES = {"burndown_ideal": "Burndown ideal", "burndown_calibrado": "Burndown calibrado",
         "monte_carlo": "Monte Carlo", "reg_logistica": "Regressão logística", "mlp": "MLP",
         "gradient_boosting": "Gradient Boosting", "mlp_curva": "MLP + curva"}
ORDEM = list(NOMES)


def f(x, n=3, sinal=False):
    if pd.isna(x):
        return "—"
    return f"{x:+.{n}f}" if sinal else f"{x:.{n}f}"


def tabela_metricas(m, cen, div, k):
    s = m[(m.cenario == cen) & (m.divisao == div) & (m.k == k)].set_index("modelo")
    linhas = ["| Modelo | ROC-AUC [IC 95%] | PR-AUC [IC 95%] | Brier | BSS [IC 95%] | Acur. bal. | F1 |",
              "|---|---|---|---|---|---|---|"]
    for mod in ORDEM:
        if mod not in s.index:
            continue
        r = s.loc[mod]
        linhas.append(
            f"| {NOMES[mod]} | {f(r.auc)} [{f(r.auc_ic_inf)}; {f(r.auc_ic_sup)}] "
            f"| {f(r.pr_auc)} [{f(r.pr_auc_ic_inf)}; {f(r.pr_auc_ic_sup)}] | {f(r.brier, 4)} "
            f"| {f(r.bss, sinal=True)} [{f(r.bss_ic_inf, sinal=True)}; {f(r.bss_ic_sup, sinal=True)}] "
            f"| {f(r.acuracia_balanceada)} | {f(r.f1)} |")
    r0 = s.iloc[0]
    cab = f"n = {int(r0.n_sprints)} Sprints, {int(r0.n_projetos)} projetos, {int(r0.positivos)} positivas (prevalência {r0.prevalencia:.3f}, que é a PR-AUC de um modelo ao acaso)."
    return cab + "\n\n" + "\n".join(linhas)


def tabela_diferencas(d, cen, div, metrica):
    s = d[(d.cenario == cen) & (d.divisao == div) & (d.metrica == metrica)]
    linhas = ["| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |", "|---|---|---|---|"]
    for mod in ORDEM:
        g = s[s.modelo == mod].set_index("k")
        if g.empty:
            continue
        cel = []
        for k in (0.3, 0.5, 0.7):
            r = g.loc[k]
            marca = ""
            if r.ic_inf > 0 or r.ic_sup < 0:
                melhor = (r.diferenca < 0) if metrica == "brier" else (r.diferenca > 0)
                marca = " ▲" if melhor else " ▼"
            cel.append(f"{f(r.diferenca, sinal=True)} [{f(r.ic_inf, sinal=True)}; {f(r.ic_sup, sinal=True)}]{marca}")
        linhas.append(f"| {NOMES[mod]} | " + " | ".join(cel) + " |")
    return "\n".join(linhas)


def main():
    m = pd.read_csv(SAIDA / "metricas.csv")
    d = pd.read_csv(SAIDA / "diferencas.csv")
    me = pd.read_csv(SAIDA / "metricas_grade_estendida.csv")
    de = pd.read_csv(SAIDA / "diferencas_grade_estendida.csv")
    blocos = {}
    for div in ("equipe_nova", "equipe_com_historico"):
        for k in (0.3, 0.5, 0.7):
            blocos[f"MET_{div}_{k}"] = tabela_metricas(m, "principal", div, k)
        for met in ("auc", "pr_auc", "brier"):
            blocos[f"DIF_{div}_{met}"] = tabela_diferencas(d, "principal", div, met)
            blocos[f"DIFE_{div}_{met}"] = tabela_diferencas(de, "principal", div, met)
    for cen in ("L70", "L60", "itens", "sem_DM"):
        for met in ("auc", "pr_auc"):
            blocos[f"DIF_{cen}_{met}"] = tabela_diferencas(d, cen, "equipe_nova", met)
    pp = pd.read_csv(SAIDA / "por_projeto.csv")
    t = pp.pivot(index="projeto", columns="modelo", values="auc")
    info = pp.groupby("projeto")[["n_sprints", "positivos"]].first()
    linhas = ["| Projeto | Sprints | Positivas | " + " | ".join(NOMES[c] for c in ORDEM if c in t.columns) + " |",
              "|---|---|---|" + "---|" * len([c for c in ORDEM if c in t.columns])]
    for pr, r in t.iterrows():
        linhas.append(f"| {pr} | {info.loc[pr, 'n_sprints']} | {info.loc[pr, 'positivos']} | "
                      + " | ".join(f(r[c]) for c in ORDEM if c in t.columns) + " |")
    blocos["POR_PROJETO"] = "\n".join(linhas)
    return blocos


if __name__ == "__main__":
    for k, v in main().items():
        print(f"<<{k}>>\n{v}\n")
