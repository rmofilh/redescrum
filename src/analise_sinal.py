"""Etapa 4 — análise de sinal: baselines B0/B1 x regressão logística x MLP pequeno, por k.

Avaliação principal: GroupKFold por projeto (5 dobras; todas as linhas de uma Sprint e de um projeto
ficam na mesma dobra). Secundária: divisão temporal dentro de cada projeto (70% mais antigas -> treino).
Métricas calculadas sobre as predições fora da dobra, separadas por k.
Saídas: reports/resultados_sinal.csv, reports/figures/metrica_vs_k_*.png, data/processed/balanceamento.csv.
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from src import viz
from src.data import carregar

warnings.filterwarnings("ignore", category=ConvergenceWarning)
SEMENTE = 42
KS = [0.3, 0.5, 0.7]
REPORTS = carregar.ROOT / "reports"

# (nome, unidade, L), em ordem de importância (decisões D1 e D2 em reports/decisoes.md):
# principal SP com L=0,8; robustez itens com L=0,8; sensibilidade L=0,6 nas duas unidades
CENARIOS = [("SP, L=0,8", "sp", 80), ("itens, L=0,8", "itens", 80), ("SP, L=0,6", "sp", 60), ("itens, L=0,6", "itens", 60)]


def variaveis(unidade):
    if unidade == "sp":
        return ["pct_tempo", "pct_pontos_concluidos", "pontos_adicionados_rel", "itens_em_andamento_rel",
                "compromisso_vs_velocidade", "duracao_dias"]
    return ["pct_tempo", "pct_itens_concluidos", "itens_adicionados_rel", "itens_em_andamento_rel",
            "compromisso_vs_velocidade_itens", "duracao_dias"]


def preparar(base, unidade, L):
    d = base[base.usa_sp] if unidade == "sp" else base
    frac = "frac_sp_final" if unidade == "sp" else "frac_itens_final"
    d = d.assign(y=(d[frac] >= L / 100 - 1e-9).astype(int))
    return d.reset_index(drop=True)


def _log_ratios(X):
    # razões têm cauda longa (ex.: compromisso/velocidade até 240): log1p estabiliza antes de padronizar
    return np.log1p(np.clip(X, 0, None))


def modelos():
    pre = [SimpleImputer(strategy="median", add_indicator=True), FunctionTransformer(_log_ratios), StandardScaler()]
    return {
        "Regressão logística": lambda: make_pipeline(*pre, LogisticRegression(class_weight="balanced", max_iter=2000)),
        "MLP (1 camada, 8 neurônios)": lambda: make_pipeline(
            *pre, MLPClassifier(hidden_layer_sizes=(8,), alpha=1e-2, max_iter=2000, random_state=SEMENTE)),
    }


def _sobreamostrar(X, y, rng):
    """MLPClassifier não aceita class_weight: replica positivos do treino até equilibrar."""
    pos = np.flatnonzero(y == 1)
    if len(pos) == 0:
        return X, y
    extra = rng.choice(pos, size=max((y == 0).sum() - len(pos), 0), replace=True)
    idx = np.concatenate([np.arange(len(y)), extra])
    return X[idx], y[idx]


def predizer_fora_da_dobra(d, cols, divisoes):
    X, y = d[cols].to_numpy(float), d.y.to_numpy()
    prob = {nome: np.full(len(d), np.nan) for nome in modelos()}
    rng = np.random.default_rng(SEMENTE)
    for tr, te in divisoes:
        for nome, fabrica in modelos().items():
            m = fabrica()
            Xt, yt = (X[tr], y[tr]) if "logística" in nome else _sobreamostrar(X[tr], y[tr], rng)
            m.fit(Xt, yt)
            prob[nome][te] = m.predict_proba(X[te])[:, 1]
    return prob


def metricas(y, pred, score):
    m = {"acuracia": accuracy_score(y, pred), "acuracia_balanceada": balanced_accuracy_score(y, pred),
         "f1": f1_score(y, pred, zero_division=0)}
    m["auc"] = roc_auc_score(y, score) if len(np.unique(y)) > 1 and np.std(score) > 0 else np.nan
    return m


def avaliar(d, unidade, divisoes, avaliados):
    cols = variaveis(unidade)
    pct = cols[1]
    prob = predizer_fora_da_dobra(d, cols, divisoes)
    linhas = []
    for k in KS:
        sel = avaliados & (d.k == k).to_numpy()
        y = d.y.to_numpy()[sel]
        maj = int(d.y[~sel | True].mean() >= 0.5)  # classe majoritária (0 em todos os cenários)
        linhas.append({"modelo": "B0 — classe majoritária", "k": k, **metricas(y, np.full(len(y), maj), np.zeros(len(y)))})
        folga = (d[pct] - d.pct_tempo).to_numpy()[sel]
        linhas.append({"modelo": "B1 — burndown ideal", "k": k, **metricas(y, (folga >= 0).astype(int), folga)})
        for nome, p in prob.items():
            linhas.append({"modelo": nome, "k": k, **metricas(y, (p[sel] >= 0.5).astype(int), p[sel])})
    return pd.DataFrame(linhas)


def divisao_por_projeto(d, n=5):
    gkf = GroupKFold(n_splits=n)
    return list(gkf.split(d, d.y, groups=d.projeto)), np.ones(len(d), bool)


def divisao_temporal(d, frac_treino=0.7):
    """Dentro de cada projeto: as 70% Sprints mais antigas treinam, as 30% mais recentes testam."""
    ordem = d.drop_duplicates("sprint_id").sort_values("start_date")
    rank = ordem.groupby("projeto").cumcount() / ordem.groupby("projeto").sprint_id.transform("size")
    teste_ids = set(ordem.sprint_id[rank >= frac_treino])
    te = d.sprint_id.isin(teste_ids).to_numpy()
    return [(np.flatnonzero(~te), np.flatnonzero(te))], te


def grafico(res, cenario, divisao, caminho):
    r = res[(res.cenario == cenario) & (res.divisao == divisao)]
    fig, eixos = viz.plt.subplots(1, 2, figsize=(9, 3.4), sharex=True)
    for ax, met, titulo in [(eixos[0], "auc", "AUC"), (eixos[1], "acuracia_balanceada", "Acurácia balanceada")]:
        for i, (nome, g) in enumerate(r.groupby("modelo", sort=False)):
            if nome.startswith("B0") and met == "auc":
                continue
            ls = "--" if nome.startswith("B") else "-"
            ax.plot(g.k, g[met], ls=ls, marker="o", ms=5, color=viz.SERIES[i], label=nome)
        ax.axhline(0.5, color=viz.NEUTRO, lw=0.8)
        ax.set_title(titulo, loc="left")
        ax.set_xticks(KS)
        ax.set_xlabel("k (fração do tempo da Sprint)")
        ax.set_ylim(0.4, 1.0)
    alcas, rotulos = eixos[1].get_legend_handles_labels()
    fig.legend(alcas, rotulos, loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.06))
    fig.suptitle(f"Métrica × k — {cenario} — {divisao}", x=0.01, ha="left", fontsize=11)
    viz.salvar(fig, caminho)


def ablacao(base):
    """AUC (GroupKFold, regressão logística) retirando grupos de variáveis — quanto cada uma agrega ao burndown."""
    linhas = []
    for nome, unidade, L in CENARIOS:
        d = preparar(base, unidade, L)
        todas = variaveis(unidade)
        conjuntos = {"só burndown (pct_tempo + % concluído)": todas[:2], "todas": todas,
                     "todas − compromisso_vs_velocidade": [c for c in todas if "velocidade" not in c],
                     "todas − itens_em_andamento_rel": [c for c in todas if "andamento" not in c],
                     "todas − adicionados_rel": [c for c in todas if "adicionados" not in c]}
        divisoes, _ = divisao_por_projeto(d)
        for rotulo, cols in conjuntos.items():
            p = predizer_fora_da_dobra(d, cols, divisoes)["Regressão logística"]
            for k in KS:
                sel = (d.k == k).to_numpy()
                linhas.append({"cenario": nome, "variaveis": rotulo, "k": k, "auc": roc_auc_score(d.y[sel], p[sel])})
    return pd.DataFrame(linhas)


def main():
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date"])
    res, bal = [], []
    for nome, unidade, L in CENARIOS:
        d = preparar(base, unidade, L)
        s = d[d.k == 0.5]
        bal.append(s.groupby("projeto").agg(n_sprints=("y", "size"), pct_cumpriu=("y", "mean"))
                   .assign(cenario=nome).reset_index())
        for div_nome, (divisoes, aval) in [("GroupKFold por projeto", divisao_por_projeto(d)),
                                           ("temporal por projeto", divisao_temporal(d))]:
            r = avaliar(d, unidade, divisoes, aval)
            res.append(r.assign(cenario=nome, divisao=div_nome, n_sprints=d.sprint_id.nunique(),
                                pct_positivos=s.y.mean()))
    res = pd.concat(res, ignore_index=True)
    res.to_csv(REPORTS / "resultados_sinal.csv", index=False)
    ablacao(base).to_csv(REPORTS / "ablacao_variaveis.csv", index=False)
    pd.concat(bal).to_csv(carregar.PROCESSED / "balanceamento.csv", index=False)
    for nome, _, _ in CENARIOS:
        for div in res.divisao.unique():
            slug = nome.replace(", ", "_").replace("=", "").replace(",", "").replace(" ", "")
            grafico(res, nome, div, carregar.FIG / f"metrica_vs_k_{slug}_{'group' if 'Group' in div else 'temporal'}.png")
    return res


if __name__ == "__main__":
    r = main()
    pd.set_option("display.width", 200)
    print(r.round(3).to_string(index=False))
