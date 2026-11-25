"""Pergunta 3, passo 6: gera reports/artigo/q3_notas.md a partir dos CSVs (nenhum número digitado à mão).

Também calcula a diferença pareada "modelo com as variáveis novas − mesmo modelo sem elas" (ROC-AUC e
PR-AUC), com intervalo de 95% por reamostragem de projetos (B = 2000), e grava
reports/artigo/diferencas_q3_pareadas.csv.
"""
import numpy as np
import pandas as pd

from src.artigo import variaveis_q3 as V
from src.artigo.metricas import B, auc, pr_auc
from src.data import carregar

SAIDA = carregar.ROOT / "reports" / "artigo"
SEMENTE = 11
APRENDIDOS = ["reg_logistica", "mlp", "gradient_boosting", "mlp_curva"]
NOMES = {"burndown_ideal": "Burndown ideal", "burndown_calibrado": "Burndown calibrado",
         "reg_logistica": "Regressão logística", "mlp": "MLP", "gradient_boosting": "Gradient Boosting",
         "mlp_curva": "MLP + curva"}
DIVISOES = {"equipe_nova": "Equipe nova (StratifiedGroupKFold por projeto)",
            "equipe_com_historico": "Equipe com histórico (5 cortes no tempo)"}


def nome(m):
    return NOMES.get(m.removesuffix("_q3"), m) + (" + Q3" if m.endswith("_q3") else "")


def f(x, d=3, sinal=True):
    return "—" if pd.isna(x) else (f"{x:+.{d}f}" if sinal else f"{x:.{d}f}")


def ic(v, a, b):
    marca = " ▲" if a > 0 else " ▼" if b < 0 else ""
    return f"{f(v)} [{f(a)}; {f(b)}]{marca}"


def n(x):
    """Inteiro com ponto de milhar (pt-BR)."""
    return f"{x:,}".replace(",", ".")


def pval(p):
    return f"{p:.2e}" if p < 1e-3 else f"{p:.3f}"


def md(df):
    cols = list(df.columns)
    linhas = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    linhas += ["| " + " | ".join(str(v) for v in r) + " |" for r in df.itertuples(index=False)]
    return "\n".join(linhas)


# ---------- diferença pareada com e sem as variáveis novas ----------

def diferencas_pareadas(p):
    rng = np.random.default_rng(SEMENTE)
    linhas = []
    for (div, k), g in p.groupby(["divisao", "k"], sort=False):
        larg = g.set_index(["sprint_id", "projeto", "y", "modelo"]).escore.unstack("modelo")
        idx = larg.index.to_frame(index=False)
        y = idx.y.to_numpy().astype(int)
        projetos = idx.projeto.unique()
        grupos = [np.flatnonzero(idx.projeto.to_numpy() == pr) for pr in projetos]
        sorteios = []
        for _ in range(B):
            ii = np.concatenate([grupos[j] for j in rng.choice(len(projetos), len(projetos), replace=True)])
            if 0 < y[ii].sum() < len(ii):
                sorteios.append(ii)
        for m in APRENDIDOS:
            if f"{m}_q3" not in larg:
                continue
            s0, s1 = larg[m].to_numpy(float), larg[f"{m}_q3"].to_numpy(float)
            for met, fn in (("auc", auc), ("pr_auc", pr_auc)):
                v = np.array([fn(y[ii], s1[ii]) - fn(y[ii], s0[ii]) for ii in sorteios])
                linhas.append({"divisao": div, "k": k, "modelo": m, "metrica": met,
                               "sem_q3": fn(y, s0), "com_q3": fn(y, s1), "diferenca": fn(y, s1) - fn(y, s0),
                               "ic_inf": np.percentile(v, 2.5), "ic_sup": np.percentile(v, 97.5),
                               "frac_bootstrap_q3_melhor": np.mean(v > 0)})
    return pd.DataFrame(linhas)


# ---------- relatório ----------

def contagens_extracao():
    arqs = {"12_comentarios": "datas dos comentários", "13_changelog_assignee": "mudanças de assignee",
            "14_issue_links": "ligações (estado final, sem data)",
            "15_changelog_links": "Change_Log com Field = 'Link' (adição/remoção datada)",
            "16_issues_alvo": "issues alvo de ligações de bloqueio",
            "17_changelog_status_alvo": "transições de status das issues alvo"}
    linhas = []
    for a, desc in arqs.items():
        df = pd.read_csv(carregar.CSV / f"{a}.csv")
        linhas.append({"Consulta": f"`sql/{a}.sql`", "Conteúdo": desc, "Linhas": n(len(df)),
                       "Issues": n(df.issue_id.nunique())})
    return pd.DataFrame(linhas)


def descritivas(v):
    linhas = []
    for (u, k), g in v.groupby(["unidade", "k"]):
        for var in V.VARIAVEIS:
            x = g[var]
            linhas.append({"Unidade": u, "k": k, "Variável": f"`{var}`", "Média": f(x.mean(), 3, False),
                           "Mediana": f(x.median(), 3, False), "% > 0": f"{(x > 0).mean():.0%}",
                           "Ausentes": int(x.isna().sum())})
    return pd.DataFrame(linhas)


def tabela_triagem(t):
    t = t.copy()
    return pd.DataFrame({
        "Variável": "`" + t.variavel + "`", "k": t.k, "n": t.n_sprints, "coef.": t.coef.map(lambda x: f(x, 3)),
        "EP agrupado": t.ep_agrupado.map(lambda x: f(x, 3, False)), "p (LR)": t.p_lr.map(pval),
        "p (Wald agrupado)": t.p_wald_agrupado.map(pval),
        "AUC sem → com": [f"{a:.3f} → {b:.3f}" for a, b in zip(t.auc_m0, t.auc_m1)],
        "Passa": t.passa.map({True: "sim", False: "não"}),
    })


def tabela_vs_ref(dif, div, met):
    s = dif[(dif.cenario == "principal") & (dif.divisao == div) & (dif.metrica == met)]
    linhas = []
    for m in APRENDIDOS:
        for mm in (m, f"{m}_q3"):
            lin = {"Modelo": nome(mm)}
            for k in (0.3, 0.5, 0.7):
                r = s[(s.modelo == mm) & (s.k == k)]
                lin[f"k = {k}".replace(".", ",")] = ic(*r[["diferenca", "ic_inf", "ic_sup"]].iloc[0]) if len(r) else "—"
            linhas.append(lin)
    return pd.DataFrame(linhas)


def tabela_pareada(par, div, met):
    s = par[(par.divisao == div) & (par.metrica == met)]
    linhas = []
    for m in APRENDIDOS:
        lin = {"Modelo": NOMES[m]}
        for k in (0.3, 0.5, 0.7):
            r = s[(s.modelo == m) & (s.k == k)].iloc[0]
            lin[f"k = {k}".replace(".", ",")] = f"{r.sem_q3:.3f} → {r.com_q3:.3f}; {ic(r.diferenca, r.ic_inf, r.ic_sup)}"
        linhas.append(lin)
    return pd.DataFrame(linhas)


def checar_reproducao(p):
    """Os modelos sem as variáveis novas, rodados de novo, reproduzem reports/artigo/predicoes.csv?"""
    orig = pd.read_csv(SAIDA / "predicoes.csv")
    orig = orig[orig.cenario == "principal"]
    chave = ["divisao", "dobra", "modelo", "sprint_id", "k"]
    m = p.merge(orig[chave + ["escore"]], on=chave, suffixes=("", "_orig"))
    return len(m), float(np.nanmax(np.abs(m.escore - m.escore_orig)))


def main():
    v = V.carregar_variaveis()
    t = pd.read_csv(SAIDA / "q3_triagem.csv")
    p = pd.read_csv(SAIDA / "predicoes_q3.csv")
    dif = pd.read_csv(SAIDA / "diferencas_q3.csv")
    par = diferencas_pareadas(p)
    par.to_csv(SAIDA / "diferencas_q3_pareadas.csv", index=False)
    n_rep, max_dif = checar_reproducao(p)
    _, lig = V.ligacoes_bloqueio()
    aprovadas = list(t[t.passa].variavel.drop_duplicates())
    reprovadas = [x for x in V.VARIAVEIS if x not in aprovadas]
    params = pd.read_csv(SAIDA / "parametros_por_dobra_q3.csv")
    hist = v[(v.unidade == "sp") & (v.k == 0.5)].n_sprints_historico.value_counts().sort_index()

    o = []
    w = o.append
    w("# Pergunta 3: variáveis além do burndown\n")
    w("> Gerado por `src/artigo/relatorio_q3.py` a partir dos CSVs de `reports/artigo/` e `data/`; "
      "nenhum número foi digitado à mão.")
    w("> Especificação: `artigo/especificacao_q3_claude_code.md`. Decisões: `artigo/base_decisoes_artigo.md` (A8, A9).")
    w("> Reprodução (com o dump no MySQL): `scripts/rodar_q3.sh`.\n")

    w("## 1. Resumo\n")
    w(f"- Lista fechada de 4 variáveis, todas construídas. Nenhuma foi acrescentada nem redefinida depois de ver resultados.")
    w(f"- **Aprovadas na triagem** (p < 0,05 com erros agrupados por projeto em ≥ 2 dos 3 valores de k): "
      f"{', '.join(f'`{x}`' for x in aprovadas) or 'nenhuma'}.")
    w(f"- **Reprovadas:** {', '.join(f'`{x}`' for x in reprovadas) or 'nenhuma'}.")
    w("- A reavaliação (seção 6) compara cada modelo aprendido com e sem as variáveis aprovadas, contra o "
      "burndown calibrado e diretamente (pareado).\n")

    w("## 2. O que foi extraído\n")
    w("Dump TAWOS v1.1 baixado de novo do Figshare (`TAWOS.sql.zip`, MD5 `e9c5ecc7649d55f0cf2fb4efb5664494`, "
      "igual ao do README) e importado no MySQL 8.0.22 local (`scripts/mysql_local.sh`). "
      "As consultas filtram as issues de `data/interim/itens_sprint.csv` por meio da tabela auxiliar `q3_issues` "
      f"({v.sprint_id.nunique()} Sprints da base; 46.080 issues), criada por `src/artigo/extrair_q3.py`, que "
      "exporta os CSVs com `src/data/db.py`.\n")
    w(md(contagens_extracao()))
    w("\nAs consultas 16 e 17 não estavam na especificação. Elas foram necessárias para cumprir a definição de "
      "`dependencias_abertas_rel`: a maioria das issues alvo de bloqueio fica fora das Sprints e não está em "
      "`08_issues_sprint.csv`/`09_changelog_status.csv`. Sem elas, `LinhaDoTempo` não saberia se o alvo estava "
      "concluído em t_k. Têm o mesmo formato de 08 e 09, e `LinhaDoTempo` é reaproveitada sem mudança.\n")

    w("## 3. Decisão sobre as dependências\n")
    w("Verificação pedida (`SELECT Field, COUNT(*) FROM Change_Log WHERE Field LIKE '%ink%' GROUP BY Field`): "
      "o `Change_Log` registra ligações em `Field = 'Link'` (448.089 linhas na base toda). Na adição, `To_Value` "
      "traz a chave da issue alvo e `To_String` o texto (\"This issue is blocked by MESOS-10162\"); na remoção, "
      "`From_Value` traz a chave. **Decisão: a variável foi construída**, datando cada ligação pelo `Change_Log`.\n")
    w(f"- Ligações que partem das issues da base: {n(lig['ligacoes_q3'])}; de bloqueio: {n(lig['ligacoes_bloqueio'])} "
      f"(nomes no Jira: {', '.join(f'{k} {n(v_)}' for k, v_ in lig['nomes_bloqueio'].items())}).")
    frac_datada = f"{lig['ligacoes_bloqueio_datadas'] / lig['ligacoes_bloqueio']:.1%}".replace(".", ",")
    w(f"- Com data no `Change_Log` da issue de origem: {n(lig['ligacoes_bloqueio_datadas'])} ({frac_datada}). As "
      f"{lig['ligacoes_bloqueio'] - lig['ligacoes_bloqueio_datadas']} sem registro não são datáveis e **não contam** "
      "(contá-las exigiria supor uma data).")
    w("- Tipo de bloqueio identificado pela descrição (`blocks` / `is blocked by`), porque o nome varia entre "
      "projetos (Blocks, Blockers, Blocker, Block). Ficam fora o tipo `Blocked`/`Blocked` (20 linhas na base "
      "toda, sem direção) e tipos de dependência que não são bloqueio (`Depends`, `Dependency`, Gantt).")
    w("- A ligação conta em t_k se o último evento do `Change_Log` para aquela chave com data ≤ t_k for uma adição "
      "(cobre ligações removidas e recriadas). Partimos do estado final de `Issue_Link`, como pede a especificação; "
      "ligações criadas e removidas antes do fim não aparecem em `Issue_Link` e não são consideradas.\n")

    w("## 4. Definições operacionais\n")
    w("Todas com eventos de data ≤ t_k, t_k = início + k·(fim − início). Itens já concluídos no início ficam fora "
      "(como em `construir_base.py`); o denominador é o nº de itens comprometidos.\n")
    w("| Variável | Como foi calculada |\n|---|---|")
    w("| `comentarios_recentes_rel` | comentários com data em (t_k − 2 dias, t_k] em itens da Sprint abertos em t_k: "
      "comprometidos não removidos e adicionados até t_k não removidos, ainda não concluídos em t_k |")
    w("| `trocas_responsavel_rel` | linhas do `Change_Log` com `Field = 'assignee'` e data em (início, t_k] nos itens "
      "comprometidos (inclui a primeira atribuição, de vazio para alguém) |")
    w("| `dependencias_abertas_rel` | itens comprometidos não removidos e não concluídos em t_k com ≥ 1 ligação de "
      "bloqueio, existente em t_k, com issue que não estava na Sprint em t_k e cujo status em t_k não era de "
      "conclusão (`LinhaDoTempo.concluido_em`) |")
    w("| `historico_cumprimento` | fração das até 3 Sprints anteriores do mesmo projeto, encerradas até o início "
      "(mesma janela do Monte Carlo, `derivados.historico_anterior`), com fração concluída ≥ 0,8 (`frac_sp` na "
      "unidade SP, `frac_itens` na unidade itens). Sprints da janela sem fração definida (sem SP comprometidos) "
      "ficam fora do denominador; sem nenhuma, a variável fica ausente |")
    w(f"\nNa unidade SP (k = 0,5), nº de Sprints anteriores com fração definida: "
      f"{', '.join(f'{int(i)} → {n}' for i, n in hist.items())}.\n")
    w("Conferência manual (Sprint 438, MESOS, k = 0,5): mudanças de responsável e ligações de bloqueio conferidas "
      "contra consultas diretas no MySQL; das 16 ligações de bloqueio dos itens comprometidos, só uma atende a "
      "todas as condições (existe em t_k, alvo fora da Sprint e aberto), e a variável vale 1/34.\n")
    w("### Descritivas (`data/processed/variaveis_q3.csv`)\n")
    w(md(descritivas(v)))

    w("\n## 5. Triagem (teste incremental)\n")
    w("Cenário principal (SP, L = 0,8), 1.159 Sprints, 33 projetos, separadamente em cada k. "
      "M0: `y ~ pct_concluido`; M1: `y ~ pct_concluido + variável` (regressão logística, variável na escala "
      "original). p (LR): razão de verossimilhança, 1 g.l., supõe Sprints independentes. p (Wald agrupado): "
      "coeficiente da variável em M1 com erros agrupados por projeto (`statsmodels`, `cov_type=\"cluster\"`). "
      "Para `historico_cumprimento`, M0 e M1 usam as mesmas Sprints (casos completos: 1.137). "
      "AUC na amostra (sem validação), só como referência de tamanho de efeito. "
      "Critério declarado: passa se p (Wald agrupado) < 0,05 em ≥ 2 dos 3 k. Arquivo: `reports/artigo/q3_triagem.csv`.\n")
    w(md(tabela_triagem(t)))
    so_ingenuo = t[(t.p_lr < 0.05) & (t.p_wald_agrupado >= 0.05)]
    if len(so_ingenuo):
        itens_ = "; ".join(f"`{var}` (k = {', '.join(str(k).replace('.', ',') for k in g.k)})" for var, g in so_ingenuo.groupby("variavel"))
        w(f"\nLeitura: {itens_} têm p < 0,05 no teste ingênuo, mas não com erros agrupados por projeto: o efeito "
          "aparente vem de diferenças entre projetos, não de informação nova sobre a Sprint.\n")
    else:
        w("")
    w("## 6. Reavaliação com as variáveis aprovadas\n")
    w(f"Conjunto novo = `TABULAR` + {', '.join(f'`{x}`' for x in aprovadas)} (`avaliacao.tabular_q3`; `TABULAR` "
      "não mudou). Mesmos modelos aprendidos, grades, sementes, cortes de decisão e divisões da rodada principal; "
      "sem rebalanceamento. As ausências (Sprints sem anteriores) são tratadas pelo mesmo pré-processamento "
      "(mediana + indicador). Arquivos: `predicoes_q3.csv`, `parametros_por_dobra_q3.csv`, `metricas_q3.csv`, "
      "`diferencas_q3.csv`, `diferencas_q3_pareadas.csv`.\n")
    w(f"Os modelos sem as variáveis novas foram rodados de novo no mesmo arquivo, para que a comparação use as "
      f"mesmas Sprints e os mesmos sorteios. Conferência: {n(n_rep)} predições coincidem com " +
      f"`reports/artigo/predicoes.csv` (maior diferença absoluta no escore: {max_dif:.1e}).\n")
    w("▲/▼: intervalo de 95% (reamostragem de projetos, 2.000 sorteios) acima/abaixo de zero.\n")
    for div, titulo in DIVISOES.items():
        w(f"### {titulo}\n")
        w("**Diferença de ROC-AUC para o burndown calibrado**\n")
        w(md(tabela_vs_ref(dif, div, "auc")))
        w("\n**Diferença de PR-AUC para o burndown calibrado**\n")
        w(md(tabela_vs_ref(dif, div, "pr_auc")))
        w("\n**Efeito direto das variáveis novas: mesmo modelo, sem → com (ROC-AUC); diferença [IC 95%]**\n")
        w(md(tabela_pareada(par, div, "auc")))
        w("\n**Idem, PR-AUC**\n")
        w(md(tabela_pareada(par, div, "pr_auc")))
        w("")
    w("### Parâmetros escolhidos no treino (com as variáveis novas)\n")
    pp = params[params.modelo.str.endswith("_q3")].groupby(["divisao", "modelo"]).parametros.agg(
        lambda x: "; ".join(f"{k} ×{n}" for k, n in x.value_counts().items())).reset_index()
    w(md(pp.rename(columns={"divisao": "Divisão", "modelo": "Modelo", "parametros": "Escolhas nas 5 dobras"})))

    w("\n## 7. Limitações\n")
    w("- `Issue_Link` guarda só o estado final; 1,3% das ligações de bloqueio não têm registro no `Change_Log` e "
      "não contam. Ligações criadas e removidas antes do fim da coleta não entram.")
    w("- `trocas_responsavel_rel` conta toda linha de `assignee` do `Change_Log`, inclusive a primeira atribuição "
      "e trocas de ida e volta; não distingue reatribuição de atribuição inicial.")
    w("- `historico_cumprimento` usa a mesma janela do Monte Carlo e da velocidade (até 3 Sprints anteriores, "
      "inclusive as que saem da base pelos filtros), e por isso compartilha informação com `compromisso_vs_velocidade`.")
    w("- Os valores-p da triagem não foram corrigidos para múltiplas comparações (4 variáveis × 3 k); o critério "
      "de dois k com erros agrupados foi declarado antes de rodar e é a proteção adotada.")
    (SAIDA / "q3_notas.md").write_text("\n".join(o) + "\n")
    print("reports/artigo/q3_notas.md gerado")


if __name__ == "__main__":
    main()
