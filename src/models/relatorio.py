"""Gera reports/resultados.md a partir de reports/resultados/*.csv (todos os números vêm dos CSVs)."""
import pandas as pd

from src.data import carregar
from src.models.experimentos import CENARIOS, SAIDA

REPORTS = carregar.ROOT / "reports"
FIG = "figures/redes"  # relativo a reports/


def br(v, casas=3):
    if isinstance(v, (bool,)) or pd.isna(v):
        return {True: "sim", False: "não"}.get(v, "–")
    if isinstance(v, (int,)) or (isinstance(v, float) and float(v).is_integer() and abs(v) >= 10):
        return f"{int(v):,}".replace(",", ".")
    return f"{v:.{casas}f}".replace(".", ",")


def tabela(df, casas=3):
    cab = "| " + " | ".join(df.columns) + " |"
    sep = "|" + "|".join("---" if df[c].dtype == object else "---:" for c in df.columns) + "|"
    linhas = ["| " + " | ".join(v if isinstance(v, str) else br(v, casas) for v in r) + " |"
              for r in df.itertuples(index=False)]
    return "\n".join([cab, sep, *linhas])


def main():
    e1 = pd.read_csv(SAIDA / "exp1_perceptron_adaline_2entradas.csv")
    cv3 = pd.read_csv(SAIDA / "exp3_pmc_topologias_cv.csv")
    e3 = pd.read_csv(SAIDA / "exp3_pmc_treinamentos.csv")
    e4 = pd.read_csv(SAIDA / "exp4_avaliacao.csv")
    top = pd.read_csv(SAIDA / "exp4_topologias_por_dobra.csv")

    titulo = {k: v[0] for k, v in CENARIOS.items()}
    principal = e4[e4.cenario == titulo["principal"]]
    m = lambda mod, k, met, df=principal: df[(df.modelo.str.startswith(mod)) & (df.k == k)][met].iloc[0]
    n_top = int(e3.n_ocultos.iloc[0])
    ad = e1[e1.rede == "Adaline"]
    pe = e1[e1.rede == "Perceptron"]

    out = [f"""# Resultados — Perceptron, Adaline e PMC

> Gerado por `src/models/relatorio.py` a partir de `reports/resultados/*.csv`. Para reproduzir: `scripts/experimentos.sh`.
> Decisões em vigor (`reports/decisoes.md`): **D1** rótulo `cumpriu = concluído / comprometido ≥ 0,8`; **D2** unidade principal story points, com itens só para robustez; **D3** redes do scikit-learn.

## Resumo

- **Cenário principal (SP, L = 0,8, GroupKFold por projeto, {br(int(principal.n_sprints.iloc[0]))} Sprints, {br(principal.pct_positivos.iloc[0] * 100, 1)}% "cumpriu"):** o **Adaline** é a melhor rede. Em k = 0,5, AUC {br(m('Adaline', .5, 'auc'))} contra {br(m('B1', .5, 'auc'))} do B1, e acurácia balanceada {br(m('Adaline', .5, 'acuracia_balanceada'))} contra {br(m('B1', .5, 'acuracia_balanceada'))}. Ele **empata com B1 em AUC** e o supera em acurácia balanceada.
- O **PMC** ({n_top} neurônios ocultos no treino completo) fica abaixo do Adaline e do B1 em AUC (k = 0,5: {br(m('PMC', .5, 'auc'))}). A não linearidade não ajuda com estas variáveis, e a rede sobreajusta (AUC no treino ≈ {br(e3.auc_treino.mean())}).
- O **Perceptron** não converge: as classes se sobrepõem, então os pesos da última época oscilam. É o pior modelo treinado (k = 0,5: AUC {br(m('Perceptron', .5, 'auc'))}) e, no cenário principal, piora com k.
- **A curva sobe com k** para B1, Adaline e PMC, nos três cenários.
- **B0** chega a {br(m('B0', .5, 'acuracia'))} de acurácia sem detectar nenhum positivo. Com L = 0,8 a acurácia simples engana; as métricas de decisão são a acurácia balanceada, o F1 e a AUC.

## Protocolo

| Item | Configuração |
|---|---|
| Base | `data/processed/base_modelagem.csv` (uma linha por Sprint × k; um modelo para os três k, avaliado em cada k) |
| Cenários | principal **{titulo['principal']}**; robustez **{titulo['robustez']}**; sensibilidade **{titulo['sem_DM']}** |
| Variáveis (SP) | pct_tempo, pct_pontos_concluidos, pontos_adicionados_rel, itens_em_andamento_rel, compromisso_vs_velocidade, duracao_dias. Imputação pela mediana + indicador, `log1p`, z-score, tudo ajustado só no treino |
| Divisão | `GroupKFold(5)` por projeto, as mesmas dobras da análise de sinal (`src/analise_sinal.divisao_por_projeto`). Métricas sobre as predições fora da dobra |
| Desequilíbrio | Perceptron e Adaline: pesos de amostra "balanced" (= `class_weight="balanced"`). PMC: sobreamostragem dos positivos só no treino |
| Perceptron | `sklearn.linear_model.Perceptron` (η = 1); pesos iniciais U(−0,5; 0,5); para em época sem erros ou após 100 épocas |
| Adaline | `SGDClassifier(loss="squared_error", penalty=None, learning_rate="constant", eta0=1e-3)`; para quando \\|ΔEQM\\| ≤ 10⁻⁶ ou após 500 épocas |
| PMC | `MLPClassifier`: 1 camada oculta logística, `solver="sgd"` (retropropagação), η = 0,01, *momentum* 0,9, α = 10⁻² (L2), até 2.000 épocas. Topologia ∈ {{5, 10, 15}} por GroupKFold(3) **dentro do treino de cada dobra** |
| Sementes | avaliação: 42; experimentos "formato livro": 1 a 5 |

### Equivalência do Adaline com o cap. 4 do livro

| Livro (regra Delta) | `SGDClassifier(loss="squared_error")` |
|---|---|
| saída linear u = Σ wᵢxᵢ − θ (θ = limiar) | `decision_function` = wᵀx + b (b = −θ) |
| EQM = 1/(2p) Σ (d − u)², com d ∈ {{−1, +1}} | perda ½ (y − wᵀx)², com y ∈ {{−1, +1}} para a classe positiva |
| ajuste amostra a amostra: w ← w + η (d − u) x | SGD sem penalização e com taxa constante: w ← w + η (y − wᵀx) x |
| parada: \\|EQM_atual − EQM_anterior\\| ≤ ε | laço de épocas próprio (`partial_fit`) com o mesmo critério (ε = 10⁻⁶) |
| operação: y = sinal(u) | `predict` = sinal(`decision_function`) |

Diferenças: (i) os pesos de classe multiplicam η amostra a amostra; (ii) a ordem das amostras é embaralhada a cada época (`shuffle=True`); (iii) os pesos iniciais são aleatórios pequenos, como no livro (o sklearn começaria em zero).

## Experimento 1 — Perceptron e Adaline com 2 entradas (pct_tempo, pct_pontos_concluidos)

Treino na base principal inteira (sem divisão: o objetivo aqui é observar o treinamento, como nas tabelas do livro). **Desvio em relação ao pedido:** com só k = 0,5, `pct_tempo` seria constante (0,5) e viraria um segundo limiar, sem reta no plano. Por isso o treino usa as três frações de tempo juntas, e a tabela informa onde cada fronteira corta **k = 0,5** (o B1 corta em 0,5). Entradas sem padronização (já estão em [0, 1]); "erro final" = nº de amostras erradas (Perceptron) ou EQM (Adaline).

"""]
    t1 = e1.rename(columns={"rede": "Rede", "semente": "Semente", "w0_limiar": "w₀ (bias)", "w1_pct_tempo": "w₁ (pct_tempo)",
                            "w2_pct_concluido": "w₂ (pct_concluído)", "epocas": "Épocas", "convergiu": "Convergiu",
                            "erro_final": "Erro final", "fronteira_em_k05": "Fronteira em k = 0,5",
                            "acuracia_balanceada_treino": "Acur. bal. (treino)"})
    t1["Semente"] = t1.Semente.astype(str)
    t1["Épocas"] = t1["Épocas"].astype(str)
    out.append(tabela(t1))
    out.append(f"""
- **Perceptron:** nenhuma das 5 sementes converge em 100 épocas (classes não linearmente separáveis). Os pesos da última época variam muito entre sementes, e em {int((pe['acuracia_balanceada_treino'] <= 0.5 + 1e-9).sum())} das 5 a reta final deixa todas as Sprints de um mesmo lado (acurácia balanceada 0,5). É o comportamento descrito no livro para problemas não separáveis.
- **Adaline:** as 5 sementes convergem em {int(ad.epocas.min())}–{int(ad.epocas.max())} épocas para praticamente a mesma reta (EQM final ≈ {br(ad.erro_final.mean(), 4)}). A fronteira corta k = 0,5 em pct_concluído ≈ {br(ad.fronteira_em_k05.mean(), 2)}: abaixo da diagonal do B1 (0,5), porque a ponderação de classes desloca a reta para capturar mais Sprints que cumprem.

![Curvas de treinamento]({FIG}/exp1_curvas_treinamento.png)

## Experimento 2 — Fronteiras no plano (pct_tempo × pct_pontos_concluidos)

![Fronteiras de decisão]({FIG}/exp2_fronteiras_2entradas.png)

Os pontos laranja (cumpriu) se concentram acima da diagonal do burndown ideal, mas há muitos pontos cinza (não cumpriu) na mesma região: as classes se sobrepõem. As 5 retas do Adaline praticamente coincidem. As do Perceptron se espalham, e algumas ficam fora da área do gráfico.

## Experimento 3 — PMC com todas as variáveis (cenário principal)

**Escolha da topologia** por GroupKFold(5) por projeto na base principal. Critério: AUC das predições fora da dobra agregadas. A média por dobra é instável porque uma dobra contém só o DM, com 0,8% de positivos.

""")
    out.append(tabela(cv3.rename(columns={"n_ocultos": "Neurônios ocultos", "auc_fora_da_dobra": "AUC fora da dobra",
                                          "auc_media_por_dobra": "AUC média por dobra", "auc_dp_por_dobra": "DP por dobra"})
                      .astype({"Neurônios ocultos": str})))
    out.append(f"""
**Topologia escolhida: {n_top} neurônios ocultos.** Cinco treinamentos na base principal inteira:

""")
    t3 = e3.drop(columns="n_ocultos").rename(columns={
        "semente": "Semente", "erro_final_entropia_cruzada": "Erro final (entropia cruzada)", "epocas": "Épocas",
        "convergiu": "Convergiu", "acuracia_balanceada_treino": "Acur. bal. (treino)", "auc_treino": "AUC (treino)"})
    t3["Semente"] = t3.Semente.astype(str)
    t3["Épocas"] = t3["Épocas"].astype(str)
    out.append(tabela(t3))
    out.append(f"""
"Convergiu" segue o critério do sklearn (melhora da perda < 10⁻⁵ por 20 épocas seguidas). {'Nenhum treinamento atingiu esse critério antes de 2.000 épocas: a perda continua caindo devagar, sinal de que a rede passa a decorar o treino.' if not e3.convergiu.any() else ''}

![Curva de perda do PMC]({FIG}/exp3_pmc_loss_curve.png)

## Experimento 4 — Avaliação por k (B0, B1, Perceptron, Adaline, PMC)

Predições fora da dobra (GroupKFold por projeto). Matriz de confusão: VN/FP/FN/VP, com positivo = "cumpriu".
""")
    for chave in ("principal", "robustez", "sem_DM"):
        r = e4[e4.cenario == titulo[chave]]
        out.append(f"\n### {titulo[chave]} — {br(int(r.n_sprints.iloc[0]))} Sprints, {int(r.n_projetos.iloc[0])} projetos, "
                   f"{br(r.pct_positivos.iloc[0] * 100, 1)}% \"cumpriu\"\n")
        t = r[["modelo", "k", "acuracia", "acuracia_balanceada", "f1", "auc", "VN", "FP", "FN", "VP"]].copy()
        t["k"] = t.k.map(lambda v: br(v, 1))
        for c in ("VN", "FP", "FN", "VP"):
            t[c] = t[c].astype(int).astype(str)
        t.columns = ["Modelo", "k", "Acurácia", "Acur. balanceada", "F1", "AUC", "VN", "FP", "FN", "VP"]
        out.append(tabela(t))
        tp = top[top.cenario == titulo[chave]]
        out.append(f"\nTopologia do PMC escolhida em cada dobra: {', '.join(str(int(v)) for v in tp.n_ocultos)} neurônios.\n")
        out.append(f"![Métrica × k — {titulo[chave]}]({FIG}/exp4_metrica_vs_k_{chave}.png)\n")

    rob = e4[e4.cenario == titulo["robustez"]]
    sem = e4[e4.cenario == titulo["sem_DM"]]
    out.append(f"""
### Leitura

- **Principal:** Adaline ≈ B1 em AUC (k = 0,3/0,5/0,7: {br(m('Adaline', .3, 'auc'), 2)}/{br(m('Adaline', .5, 'auc'), 2)}/{br(m('Adaline', .7, 'auc'), 2)} contra {br(m('B1', .3, 'auc'), 2)}/{br(m('B1', .5, 'auc'), 2)}/{br(m('B1', .7, 'auc'), 2)}) e superior em acurácia balanceada, porque detecta mais Sprints que cumprem (VP {int(m('Adaline', .5, 'VP'))} contra {int(m('B1', .5, 'VP'))} em k = 0,5) ao custo de mais falsos positivos (FP {int(m('Adaline', .5, 'FP'))} contra {int(m('B1', .5, 'FP'))}). O F1 fica empatado.
- **Robustez (itens):** mesma ordem: Adaline (AUC {br(m('Adaline', .5, 'auc', rob), 2)} em k = 0,5) ≥ B1 ({br(m('B1', .5, 'auc', rob), 2)}) > PMC ({br(m('PMC', .5, 'auc', rob), 2)}) > Perceptron ({br(m('Perceptron', .5, 'auc', rob), 2)}). Aqui o PMC fica mais perto do Adaline.
- **Sem o DM:** a proporção de positivos sobe para {br(sem.pct_positivos.iloc[0] * 100, 1)}%. B1 e Adaline continuam empatados em AUC (k = 0,5: {br(m('B1', .5, 'auc', sem), 2)} e {br(m('Adaline', .5, 'auc', sem), 2)}), e as conclusões não dependem do DM.
- **Para o alerta ao Scrum Master:** um modelo linear treinado (Adaline) já basta e não supera a régua do burndown ideal em capacidade de ordenar as Sprints (AUC). O ganho dele é calibrar o limiar para a classe rara. Para a rede não linear superar o B1, faltam variáveis com informação nova (ver Trabalhos futuros).

## Trabalhos futuros (não executados, por decisão do usuário)

- Variáveis extras: comentários recentes, mudanças de responsável (`Change_Type = PEOPLE`), itens `Flagged`, dependências via `Issue_Link`, velocidade de burndown recente, histórico de cumprimento da equipe.
- Sensibilidades: tolerância de 1 h no início da Sprint; `End_Date` contra `Complete_Date`; limiar de decisão escolhido no treino (em vez de 0 ou 0,5); outros L (0,6 já avaliado só na análise de sinal).
- Perceptron com "bolso" (*pocket*), que guarda os melhores pesos, para problemas não separáveis; Adaline e PMC em lote, com validação por época (*early stopping*).
- PMC: outras ativações e otimizadores (adam/ReLU), duas camadas ocultas, critério de parada pelo EQM como no livro.
- Divisão temporal dentro de cada projeto como confirmação (feita só na análise de sinal); intervalos de confiança por *bootstrap* de projetos.
- Implementar as três redes do zero (NumPy), conforme os algoritmos do livro, e comparar com as versões do scikit-learn.
""")
    (REPORTS / "resultados.md").write_text("\n".join(out))
    print("reports/resultados.md gerado")


if __name__ == "__main__":
    main()
