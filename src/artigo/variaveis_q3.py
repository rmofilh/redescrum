"""Pergunta 3, passo 3: variáveis além do burndown, uma linha por Sprint × k × unidade.

Lista fechada (artigo/base_decisoes_artigo.md, A8; definições em artigo/especificacao_q3_claude_code.md).
Toda variável usa só eventos com data <= t_k, t_k = início + k·(fim − início). Como em
src/features/construir_base.py, itens já concluídos no início ficam fora e o denominador é o nº de
itens comprometidos.

  comentarios_recentes_rel  comentários com data em (t_k − 2 dias, t_k] em itens da Sprint ainda abertos
                            em t_k (comprometidos não removidos + adicionados até t_k não removidos, ainda
                            não concluídos), ÷ nº de itens comprometidos.
  trocas_responsavel_rel    mudanças do campo assignee com data em (início, t_k] em itens comprometidos,
                            ÷ nº de itens comprometidos.
  dependencias_abertas_rel  itens comprometidos abertos em t_k (não removidos, não concluídos) com ao menos
                            uma ligação de bloqueio (Issue_Link.Description "blocks" ou "is blocked by")
                            que já existia em t_k segundo o Change_Log (Field = 'Link'), com issue que não
                            estava na Sprint em t_k e não estava concluída em t_k, ÷ nº de itens
                            comprometidos. Ligações sem registro no Change_Log não são datáveis e não contam.
  historico_cumprimento     fração das até 3 Sprints anteriores do mesmo projeto (encerradas até o início)
                            com fração concluída >= 0,8 do compromisso (frac_sp na unidade SP, frac_itens na
                            unidade itens). Mesma janela do Monte Carlo (src/artigo/derivados.py). Sprints da
                            janela sem fração definida (sem SP comprometidos) não entram no denominador;
                            sem nenhuma: ausente.

Entradas: data/interim/itens_sprint.csv, sprints_resumo.csv, data/processed/base_modelagem.csv e
data/raw/csv/12–17 (src/artigo/extrair_q3.py). Saída: data/processed/variaveis_q3.csv.
"""
import numpy as np
import pandas as pd

from src.artigo.derivados import historico_anterior
from src.data import carregar
from src.data.reconstrucao import LinhaDoTempo

VARIAVEIS = ["comentarios_recentes_rel", "trocas_responsavel_rel", "dependencias_abertas_rel",
             "historico_cumprimento"]
JANELA_COMENTARIOS = pd.Timedelta(days=2)
L_HISTORICO = 0.8
# Issue_Link.Description das ligações de bloqueio (Name varia por projeto: Blocks, Blockers, Blocker, Block)
DESCRICOES_BLOQUEIO = {"blocks", "is blocked by"}
ARQUIVO = carregar.PROCESSED / "variaveis_q3.csv"


def _datas(df, cols):
    for c in cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def _por_issue(df):
    """{issue_id: vetor ordenado de datas}."""
    df = df.dropna(subset=["data"]).sort_values(["issue_id", "data"])
    return {i: g.data.values for i, g in df.groupby("issue_id")}


def _contar(eventos, ids, ini, fim):
    """Nº de eventos com data em (ini, fim] somando as issues de ids."""
    ini, fim = np.datetime64(ini), np.datetime64(fim)
    n = 0
    for i in ids:
        ts = eventos.get(i)
        if ts is not None:
            n += np.searchsorted(ts, fim, side="right") - np.searchsorted(ts, ini, side="right")
    return int(n)


# ---------- ligações de bloqueio datadas pelo Change_Log ----------

def ligacoes_bloqueio():
    """Ligações de bloqueio do estado final (Issue_Link) com seus intervalos de existência.

    Retorna (DataFrame issue_id, target_issue_id, descricao, eventos) e contagens para o relatório.
    eventos = lista ordenada de (data, +1 adicionada / −1 removida) do Change_Log da issue de origem
    para a chave da issue alvo.
    """
    links = pd.read_csv(carregar.CSV / "14_issue_links.csv")
    cl = _datas(pd.read_csv(carregar.CSV / "15_changelog_links.csv",
                            dtype={"de": str, "para": str}), ["data"])
    blq = links[links.descricao.isin(DESCRICOES_BLOQUEIO)].copy()

    ev = {}
    add = cl[cl.para.notna()]
    rem = cl[cl.de.notna()]
    for (i, key), g in add.groupby(["issue_id", "para"]):
        ev.setdefault((i, key), []).extend((t, 1) for t in g.data)
    for (i, key), g in rem.groupby(["issue_id", "de"]):
        ev.setdefault((i, key), []).extend((t, -1) for t in g.data)
    blq["eventos"] = [sorted(ev.get((i, k), []), key=lambda x: (x[0], x[1]))
                      for i, k in zip(blq.issue_id, blq.target_key)]
    datada = blq.eventos.map(lambda e: any(s == 1 for _, s in e))
    contagens = {
        "ligacoes_q3": len(links), "ligacoes_bloqueio": len(blq),
        "ligacoes_bloqueio_datadas": int(datada.sum()),
        "nomes_bloqueio": blq.nome.value_counts().to_dict(),
    }
    return blq[datada].reset_index(drop=True), contagens


def existe_em(eventos, t):
    """Estado da ligação em t: último evento com data <= t é uma adição."""
    t = pd.Timestamp(t)
    estado = False
    for d, s in eventos:
        if d > t:
            break
        estado = s == 1
    return estado


def linha_do_tempo_ampliada():
    """LinhaDoTempo das issues em Sprints + issues alvo de ligações de bloqueio (16 e 17)."""
    iss = carregar.issues()
    alvo = _datas(pd.read_csv(carregar.CSV / "16_issues_alvo.csv"),
                  ["creation_date", "resolution_date", "estimation_date"])
    alvo = alvo[~alvo.issue_id.isin(iss.issue_id)]
    st = carregar.changelog_status()
    st_alvo = _datas(pd.read_csv(carregar.CSV / "17_changelog_status_alvo.csv"), ["data"])
    st_alvo = st_alvo[~st_alvo.issue_id.isin(st.issue_id)]
    return LinhaDoTempo(issues=pd.concat([iss, alvo], ignore_index=True),
                        cl_status=pd.concat([st, st_alvo], ignore_index=True))


# ---------- histórico de cumprimento ----------

def historico_cumprimento(resumo):
    """{(sprint_id, unidade): (fração das anteriores que cumpriram, nº de anteriores com fração definida)}."""
    hist = historico_anterior(resumo)
    frac = {"sp": resumo.set_index("sprint_id").frac_sp, "itens": resumo.set_index("sprint_id").frac_itens}
    out = {}
    for sid, ant in hist.items():
        for u, f in frac.items():
            v = f.reindex(ant).dropna().to_numpy()
            out[(sid, u)] = ((v >= L_HISTORICO - 1e-9).mean() if len(v) else np.nan, len(v))
    return out


# ---------- construção ----------

def construir():
    itens = pd.read_csv(carregar.INTERIM / "itens_sprint.csv",
                        parse_dates=["t_in", "t_out", "inicio", "fim", "removido_em", "concluido_em"])
    resumo = pd.read_csv(carregar.INTERIM / "sprints_resumo.csv", parse_dates=["start_date", "end_date"])
    resumo = resumo[resumo.n_comprometidos.notna()]
    base = pd.read_csv(carregar.PROCESSED / "base_modelagem.csv", parse_dates=["start_date", "end_date"])

    coment = _por_issue(_datas(pd.read_csv(carregar.CSV / "12_comentarios.csv"), ["data"]))
    assig = _por_issue(_datas(pd.read_csv(carregar.CSV / "13_changelog_assignee.csv",
                                          dtype={"de": str, "para": str}), ["data"]))
    blq, cont_lig = ligacoes_bloqueio()
    lig = {i: list(zip(g.target_issue_id, g.eventos)) for i, g in blq.groupby("issue_id")}
    linha = linha_do_tempo_ampliada()
    hist = historico_cumprimento(resumo)

    por_sprint = dict(tuple(itens[itens.sprint_id.isin(base.sprint_id)].groupby("sprint_id")))
    linhas = []
    for s in base[["sprint_id", "k", "start_date", "end_date", "usa_sp"]].itertuples(index=False):
        it = por_sprint[s.sprint_id]
        inicio, fim = it.inicio.iloc[0], it.fim.iloc[0]
        t = inicio + s.k * (fim - inicio)
        membros = set(it.issue_id[(it.t_in <= t) & ~(it.removido_em <= t)])
        it = it[~it.concluido_antes_inicio]
        comp = it[it.papel == "comprometido"]
        adic = it[(it.papel == "adicionado") & (it.t_in <= t)]
        n = len(comp)
        ativos = pd.concat([comp[~(comp.removido_em <= t)], adic[~(adic.removido_em <= t)]])
        abertos = ativos[~(ativos.concluido_em <= t)]
        comp_abertos = comp[~(comp.removido_em <= t) & ~(comp.concluido_em <= t)]

        n_dep = 0
        for i in comp_abertos.issue_id:
            n_dep += any(alvo not in membros and existe_em(ev, t) and not linha.concluido_em(alvo, t)
                         for alvo, ev in lig.get(i, []))

        comum = {
            "sprint_id": s.sprint_id, "k": s.k,
            "comentarios_recentes_rel": _contar(coment, abertos.issue_id, t - JANELA_COMENTARIOS, t) / n,
            "trocas_responsavel_rel": _contar(assig, comp.issue_id, inicio, t) / n,
            "dependencias_abertas_rel": n_dep / n,
        }
        for u in ("sp", "itens"):
            if u == "sp" and not s.usa_sp:
                continue
            h, nh = hist.get((s.sprint_id, u), (np.nan, 0))
            linhas.append({**comum, "unidade": u, "historico_cumprimento": h, "n_sprints_historico": nh})
    return pd.DataFrame(linhas), cont_lig


def carregar_variaveis():
    return pd.read_csv(ARQUIVO)


if __name__ == "__main__":
    df, cont = construir()
    df.to_csv(ARQUIVO, index=False)
    print(cont)
    print(f"variaveis_q3: {len(df)} linhas")
    print(df.groupby(["unidade", "k"])[VARIAVEIS].agg(["mean", lambda x: (x > 0).mean()]).round(3).T)
