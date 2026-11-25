"""Avaliação do artigo: regras simples contra modelos aprendidos na previsão do cumprimento da Sprint.

Modelos (ordem crescente de complexidade):
  burndown_ideal       folga = %concluído − %tempo; "cumpre" se folga >= 0. Sem treino, sem probabilidade.
  burndown_calibrado   regressão logística sobre a folga (2 parâmetros): mesma ordenação, probabilidade calibrada.
  monte_carlo          probabilidade simulada a partir das entregas diárias das Sprints anteriores. Sem treino.
  reg_logistica        regressão logística sobre as variáveis tabulares (fronteira linear).
  mlp                  perceptron de múltiplas camadas sobre as variáveis tabulares (fronteira não linear).
  gradient_boosting    árvores de decisão em sequência (HistGradientBoosting) sobre as variáveis tabulares.
  mlp_curva            MLP sobre as variáveis tabulares + 9 pontos anteriores da curva do burndown até t_k.

Protocolo:
  - Nenhum rebalanceamento de classes: as probabilidades ficam na escala real (necessário para o Brier).
  - Parâmetros escolhidos só no treino, por validação cruzada interna agrupada por projeto (log-loss).
  - Corte de decisão = proporção de positivos no treino (regra de Bayes para a acurácia balanceada
    quando o modelo é calibrado); burndown_ideal usa folga >= 0.
  - Cenário "equipe nova": StratifiedGroupKFold (5 dobras) por projeto.
  - Cenário "equipe com histórico": 5 cortes no tempo; treino = Sprints encerradas antes do corte,
    teste = Sprints iniciadas entre o corte e o seguinte.
Saída: reports/artigo/predicoes.csv (uma linha por Sprint × k × modelo × cenário × divisão).
"""
import warnings

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import GridSearchCV, StratifiedGroupKFold
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler

from src.data import carregar

warnings.filterwarnings("ignore", category=ConvergenceWarning)
SEMENTE = 42
KS = [0.3, 0.5, 0.7]
SAIDA = carregar.ROOT / "reports" / "artigo"

# variáveis tabulares (as mesmas do trabalho original), por unidade
TABULAR = {
    "sp": ["pct_tempo", "pct_pontos_concluidos", "pontos_adicionados_rel", "itens_em_andamento_rel",
           "compromisso_vs_velocidade", "duracao_dias"],
    "itens": ["pct_tempo", "pct_itens_concluidos", "itens_adicionados_rel", "itens_em_andamento_rel",
              "compromisso_vs_velocidade_itens", "duracao_dias"],
}
RAZOES = {"pontos_adicionados_rel", "itens_adicionados_rel", "itens_em_andamento_rel",
          "compromisso_vs_velocidade", "compromisso_vs_velocidade_itens",
          # pergunta 3 (razões por item comprometido; só entram se aprovadas na triagem)
          "comentarios_recentes_rel", "trocas_responsavel_rel", "dependencias_abertas_rel"}
CURVA = [f"c{j:02d}" for j in range(1, 10)]

# cenários: (unidade, L, projeto excluído)
CENARIOS = {
    "principal": ("sp", 80, None),
    "L70": ("sp", 70, None),
    "L60": ("sp", 60, None),
    "itens": ("itens", 80, None),
    "sem_DM": ("sp", 80, "DM"),
}

MODELOS = ["burndown_ideal", "burndown_calibrado", "monte_carlo", "reg_logistica", "mlp",
           "gradient_boosting", "mlp_curva"]

# grades declaradas antes de rodar
GRADES = {
    "reg_logistica": {"m__C": [0.01, 0.1, 1.0, 10.0]},
    "mlp": {"m__hidden_layer_sizes": [(5,), (10,), (15,)], "m__alpha": [1e-3, 1e-2, 1e-1]},
    "mlp_curva": {"m__hidden_layer_sizes": [(5,), (10,), (15,)], "m__alpha": [1e-3, 1e-2, 1e-1]},
    "gradient_boosting": {"m__learning_rate": [0.05, 0.1], "m__max_depth": [2, 3],
                          "m__max_iter": [100, 300]},
}


# Análise suplementar (decidida depois da 1ª rodada, por isso reportada à parte): na grade declarada,
# MLP, Gradient Boosting e regressão logística escolheram a configuração mais regularizada disponível.
# A grade estendida acrescenta configurações ainda mais simples para testar se o empate com o burndown
# se deve ao limite da grade.
GRADES_ESTENDIDAS = {
    "reg_logistica": {"m__C": [0.0001, 0.001, 0.01, 0.1, 1.0]},
    "mlp": {"m__hidden_layer_sizes": [(2,), (5,), (10,)], "m__alpha": [0.1, 1.0, 10.0]},
    "mlp_curva": {"m__hidden_layer_sizes": [(2,), (5,), (10,)], "m__alpha": [0.1, 1.0, 10.0]},
    "gradient_boosting": {"m__learning_rate": [0.01, 0.05], "m__max_depth": [1, 2],
                          "m__max_iter": [50, 100], "m__l2_regularization": [0.0, 1.0]},
}


def _log1p(X):
    return np.log1p(np.clip(X, 0, None))


def preprocessador(cols):
    razoes = [c for c in cols if c in RAZOES]
    outras = [c for c in cols if c not in RAZOES]
    return ColumnTransformer([
        ("razoes", make_pipeline(SimpleImputer(strategy="median", add_indicator=True),
                                 FunctionTransformer(_log1p), StandardScaler()), razoes),
        ("outras", make_pipeline(SimpleImputer(strategy="median", add_indicator=True), StandardScaler()), outras),
    ])


def pipeline(nome, cols):
    from sklearn.pipeline import Pipeline
    if nome == "reg_logistica":
        m = LogisticRegression(max_iter=5000)
    elif nome in ("mlp", "mlp_curva"):
        m = MLPClassifier(max_iter=2000, random_state=SEMENTE)
    elif nome == "gradient_boosting":
        m = HistGradientBoostingClassifier(random_state=SEMENTE)
    return Pipeline([("pre", preprocessador(cols)), ("m", m)])


# Pergunta 3: novo conjunto = TABULAR + variáveis aprovadas no teste incremental
# (reports/artigo/q3_triagem.csv, gerado por src/artigo/triagem_q3.py). TABULAR não muda.
def variaveis_aprovadas():
    t = pd.read_csv(SAIDA / "q3_triagem.csv")
    return list(t[t.passa].variavel.drop_duplicates())


def tabular_q3():
    aprovadas = variaveis_aprovadas()
    return {u: cols + aprovadas for u, cols in TABULAR.items()}


def preparar(base, mc, curvas, cenario, conjunto="base"):
    unidade, L, excluir = CENARIOS[cenario]
    d = base[base.usa_sp] if unidade == "sp" else base
    frac = "frac_sp_final" if unidade == "sp" else "frac_itens_final"
    pct = "pct_pontos_concluidos" if unidade == "sp" else "pct_itens_concluidos"
    d = d.assign(y=(d[frac] >= L / 100 - 1e-9).astype(int), folga=d[pct] - d.pct_tempo)
    m = mc[mc.unidade == unidade][["sprint_id", "k", f"p_mc_L{L}"]].rename(columns={f"p_mc_L{L}": "p_mc"})
    c = curvas[curvas.unidade == unidade][["sprint_id", "k"] + CURVA]
    d = d.merge(m, on=["sprint_id", "k"], how="left").merge(c, on=["sprint_id", "k"], how="left")
    cols = TABULAR[unidade]
    if conjunto == "q3":
        from src.artigo.variaveis_q3 import carregar_variaveis
        cols = tabular_q3()[unidade]
        v = carregar_variaveis()
        v = v[v.unidade == unidade][["sprint_id", "k"] + [c for c in cols if c not in TABULAR[unidade]]]
        d = d.merge(v, on=["sprint_id", "k"], how="left", validate="one_to_one")
    if excluir:
        d = d[d.projeto != excluir]
    return d.reset_index(drop=True), cols


# ---------- divisões ----------

def divisao_equipe_nova(d):
    """StratifiedGroupKFold por projeto; estratifica pelo rótulo da Sprint (as 3 linhas k ficam juntas)."""
    s = d.drop_duplicates("sprint_id")
    cv = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=SEMENTE)
    for i, (tr, te) in enumerate(cv.split(s, s.y, s.projeto)):
        ids_te = set(s.sprint_id.iloc[te])
        mask = d.sprint_id.isin(ids_te).to_numpy()
        yield i, np.flatnonzero(~mask), np.flatnonzero(mask)


def cortes_tempo(d, n=5):
    s = d.drop_duplicates("sprint_id")
    return list(s.start_date.quantile(np.linspace(0.5, 0.9, n)))


def divisao_equipe_com_historico(d, n=5):
    cortes = cortes_tempo(d, n) + [pd.Timestamp.max]
    for i in range(n):
        tr = (d.end_date < cortes[i]).to_numpy()
        te = ((d.start_date >= cortes[i]) & (d.start_date < cortes[i + 1])).to_numpy()
        yield i, np.flatnonzero(tr), np.flatnonzero(te)


# ---------- ajuste e predição ----------

def ajustar_prever(nome, d, tr, te, cols, grades=None):
    grades = GRADES if grades is None else grades
    """Devolve (escore no teste, probabilidade no teste ou NaN, corte, parâmetros escolhidos)."""
    dtr, dte = d.iloc[tr], d.iloc[te]
    prev = dtr.y.mean()
    if nome == "burndown_ideal":
        return dte.folga.to_numpy(), np.full(len(te), np.nan), 0.0, ""
    if nome == "monte_carlo":
        return dte.p_mc.to_numpy(), dte.p_mc.to_numpy(), prev, ""
    if nome == "burndown_calibrado":
        m = LogisticRegression(C=1e6, max_iter=5000).fit(dtr[["folga"]], dtr.y)
        p = m.predict_proba(dte[["folga"]])[:, 1]
        return p, p, prev, f"w={m.coef_[0][0]:.3f}; b={m.intercept_[0]:.3f}"
    feats = cols + CURVA if nome == "mlp_curva" else cols
    interno = StratifiedGroupKFold(n_splits=3, shuffle=True, random_state=SEMENTE)
    # divisão interna por Sprint/projeto: usa o rótulo da Sprint e agrupa por projeto
    busca = GridSearchCV(pipeline(nome, feats), grades[nome], scoring="neg_log_loss",
                         cv=interno, n_jobs=-1, refit=True)
    busca.fit(dtr[feats], dtr.y, groups=dtr.projeto)
    p = busca.predict_proba(dte[feats])[:, 1]
    return p, p, prev, str(busca.best_params_)


def rodar(base, mc, curvas, cenario, divisao, grades=None, modelos=None, conjunto="base"):
    modelos = MODELOS if modelos is None else modelos
    d, cols = preparar(base, mc, curvas, cenario, conjunto)
    gerador = divisao_equipe_nova(d) if divisao == "equipe_nova" else divisao_equipe_com_historico(d)
    linhas, params = [], []
    for dobra, tr, te in gerador:
        for nome in modelos:
            esc, prob, corte, par = ajustar_prever(nome, d, tr, te, cols, grades)
            dte = d.iloc[te]
            linhas.append(pd.DataFrame({
                "cenario": cenario, "divisao": divisao, "dobra": dobra, "modelo": nome,
                "sprint_id": dte.sprint_id.values, "projeto": dte.projeto.values, "k": dte.k.values,
                "y": dte.y.values, "escore": esc, "prob": prob, "corte": corte,
                "pred": (esc >= corte).astype(int),
            }))
            params.append({"cenario": cenario, "divisao": divisao, "dobra": dobra, "modelo": nome,
                           "n_treino_sprints": d.iloc[tr].sprint_id.nunique(),
                           "n_teste_sprints": dte.sprint_id.nunique(),
                           "positivos_teste": int(dte[dte.k == 0.5].y.sum()), "parametros": par})
        print(f"  {cenario}/{divisao} dobra {dobra}: treino {d.iloc[tr].sprint_id.nunique()} Sprints, "
              f"teste {d.iloc[te].sprint_id.nunique()}", flush=True)
    return pd.concat(linhas, ignore_index=True), pd.DataFrame(params)


def main():
    SAIDA.mkdir(parents=True, exist_ok=True)
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date", "end_date"])
    mc = pd.read_csv(carregar.PROCESSED / "monte_carlo.csv")
    curvas = pd.read_csv(carregar.PROCESSED / "curvas.csv")
    execucoes = [("principal", "equipe_nova"), ("principal", "equipe_com_historico"),
                 ("L70", "equipe_nova"), ("L60", "equipe_nova"), ("itens", "equipe_nova"),
                 ("sem_DM", "equipe_nova")]
    preds, params = [], []
    for cen, div in execucoes:
        p, q = rodar(base, mc, curvas, cen, div)
        preds.append(p); params.append(q)
    pd.concat(preds).to_csv(SAIDA / "predicoes.csv", index=False)
    pd.concat(params).to_csv(SAIDA / "parametros_por_dobra.csv", index=False)


def main_grade_estendida():
    """Suplementar: cenário principal, regras de referência + modelos aprendidos com a grade estendida."""
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date", "end_date"])
    mc = pd.read_csv(carregar.PROCESSED / "monte_carlo.csv")
    curvas = pd.read_csv(carregar.PROCESSED / "curvas.csv")
    mods = ["burndown_ideal", "burndown_calibrado", "reg_logistica", "mlp", "gradient_boosting", "mlp_curva"]
    preds, params = [], []
    for div in ("equipe_nova", "equipe_com_historico"):
        p, q = rodar(base, mc, curvas, "principal", div, GRADES_ESTENDIDAS, mods)
        preds.append(p); params.append(q)
    pd.concat(preds).to_csv(SAIDA / "predicoes_grade_estendida.csv", index=False)
    pd.concat(params).to_csv(SAIDA / "parametros_por_dobra_grade_estendida.csv", index=False)


def main_q3():
    """Pergunta 3: cenário principal, nas duas divisões. Mesmas grades, sementes e cortes da rodada
    principal. Os modelos aprendidos rodam com o conjunto atual (nomes originais) e com o conjunto
    ampliado pelas variáveis aprovadas (sufixo _q3), para que a comparação com e sem as variáveis novas
    use as mesmas Sprints e a mesma reamostragem."""
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date", "end_date"])
    mc = pd.read_csv(carregar.PROCESSED / "monte_carlo.csv")
    curvas = pd.read_csv(carregar.PROCESSED / "curvas.csv")
    aprendidos = ["reg_logistica", "mlp", "gradient_boosting", "mlp_curva"]
    print("variáveis aprovadas:", variaveis_aprovadas())
    preds, params = [], []
    for div in ("equipe_nova", "equipe_com_historico"):
        p, q = rodar(base, mc, curvas, "principal", div, modelos=["burndown_ideal", "burndown_calibrado"] + aprendidos)
        p3, q3 = rodar(base, mc, curvas, "principal", div, modelos=aprendidos, conjunto="q3")
        p3["modelo"] += "_q3"; q3["modelo"] += "_q3"
        preds += [p, p3]; params += [q, q3]
    pd.concat(preds).to_csv(SAIDA / "predicoes_q3.csv", index=False)
    pd.concat(params).to_csv(SAIDA / "parametros_por_dobra_q3.csv", index=False)


if __name__ == "__main__":
    import sys
    if "--grade-estendida" in sys.argv:
        main_grade_estendida()
    elif "--q3" in sys.argv:
        main_q3()
    else:
        main()
