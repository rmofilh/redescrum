"""Reconstrução, a partir do Change_Log, de:
- intervalos de pertinência issue <-> Sprint (campo Sprint);
- data da primeira conclusão de cada issue (campo status);
- status e story points vigentes em qualquer instante t (sem vazamento).
"""
import numpy as np
import pandas as pd

from src.data import carregar
from src.data.carregar import parse_lista

# Faixa válida de story points; fora dela o valor é tratado como ausente.
SP_MIN, SP_MAX = 0, 100


def normalizar_status(s):
    """'RESOLVED', 'In  Review' -> 'resolved', 'in review' (o Jira tem variações de caixa e espaços)."""
    return " ".join(str(s).lower().split()) if isinstance(s, str) else s


# Status que significam "entregue" (categoria Done do Jira) nos 36 projetos com Sprints.
# Won't Fix / Invalid / Duplicate (estados terminais sem entrega) NÃO contam como entrega.
STATUS_CONCLUIDO = {"closed", "resolved", "done", "complete", "completed"}

# Status de "não está em execução": ainda não iniciado (categoria To Do do Jira), aguardando/bloqueado
# ou encerrado sem entrega. Todo status fora deste conjunto e de STATUS_CONCLUIDO conta como "em andamento".
STATUS_A_FAZER = {normalizar_status(s) for s in [
    "Open", "To Do", "New", "Reopened", "Backlog", "Accepted", "Ready for Work", "To Develop",
    "Gathering Impact", "Gathering Interest", "Short Term Backlog", "Long Term Backlog",
    "Needs Triage", "Not Being Considered", "Waiting for Triage", "Triage", "Triaged",
    "Selected for Development", "Ready", "Ready for Development", "Planned", "Prioritized", "Pending",
    "Ready To Start", "Ready for Engineering", "ToDo", "Draft", "Investigating", "Awaiting Development",
    "Need more info", "Needs More Info", "Waiting for Information", "On Hold", "Monitor / On Hold",
    "Blocked", "Waiting (Blocked)", "Deferred", "Defered", "Unplanned", "Under Consideration",
    "Future Consideration", "Scheduled", "Raw", "Ready to Groom", "Refine", "Received", "Icebox",
    "Design Backlog", "Open - untriaged", "In Backlog", "Planning", "Assessed", "Assessment", "Unverified",
    "Waiting for Customer", "Waiting for Support", "Waiting for Feedback", "Waiting for Response",
    "Pending 3rd-Party", "Inactive - Pending Closure", "Won't Fix", "Invalid", "Duplicate",
]}


def intervalos_pertinencia(issues=None, cl=None):
    """Retorna DataFrame (issue_id, project_id, sprint_jira_id, t_in, t_out, origem).

    Regras:
    - antes da 1ª mudança, a issue pertence às Sprints de From_Value da 1ª mudança, desde a criação;
    - cada mudança fecha os intervalos das Sprints que saíram e abre os das que entraram;
    - issue com Sprint_ID e sem histórico do campo Sprint: pertence à Sprint desde a criação
      (origem='sem_historico');
    - t_out = NaT significa "ainda na lista" (o Jira mantém Sprints fechadas no campo).
    """
    issues = carregar.issues() if issues is None else issues
    cl = carregar.changelog_sprint() if cl is None else cl
    criacao = issues.set_index("issue_id").creation_date
    proj = issues.set_index("issue_id").project_id

    linhas, incoerencias = [], 0
    for iid, g in cl.groupby("issue_id", sort=False):
        g = g.sort_values(["data", "change_id"])
        abertos = {}
        primeira = parse_lista(g.from_value.iloc[0])
        for j in primeira:
            abertos[j] = criacao.get(iid, pd.NaT)
        anterior = primeira
        for de, para, t in zip(g.from_value, g.to_value, g.data):
            de, para = parse_lista(de), parse_lista(para)
            if de != anterior:
                incoerencias += 1
            for j in set(abertos) - para:
                linhas.append((iid, j, abertos.pop(j), t, "historico"))
            for j in para - set(abertos):
                abertos[j] = t
            anterior = para
        for j, t_in in abertos.items():
            linhas.append((iid, j, t_in, pd.NaT, "historico"))

    df = pd.DataFrame(linhas, columns=["issue_id", "sprint_jira_id", "t_in", "t_out", "origem"])
    df["project_id"] = df.issue_id.map(proj)

    # issues ligadas via Sprint_ID e sem histórico do campo Sprint
    sem = issues[issues.sprint_id_final.notna() & ~issues.issue_id.isin(cl.issue_id)]
    return df, incoerencias, sem


def mapear_sprints(df, sprints):
    """sprint_jira_id + project_id -> Sprint.ID (JiraID é único dentro de cada projeto)."""
    m = sprints[["project_id", "sprint_jira_id", "sprint_id"]]
    return df.merge(m, on=["project_id", "sprint_jira_id"], how="left")


def tabela_pertinencia():
    """Intervalos de pertinência já mapeados para Sprint.ID (inclui issues sem histórico)."""
    issues, cl, sprints = carregar.issues(), carregar.changelog_sprint(), carregar.sprints()
    df, incoer, sem = intervalos_pertinencia(issues, cl)
    df = mapear_sprints(df, sprints)
    extra = pd.DataFrame({
        "issue_id": sem.issue_id.values,
        "sprint_jira_id": sem.sprint_id_final.map(sprints.set_index("sprint_id").sprint_jira_id).values,
        "t_in": sem.creation_date.values, "t_out": pd.NaT, "origem": "sem_historico",
        "project_id": sem.project_id.values, "sprint_id": sem.sprint_id_final.astype(int).values,
    })
    return pd.concat([df, extra], ignore_index=True), incoer


class LinhaDoTempo:
    """Consulta de status e story points vigentes em t, usando só eventos com data <= t."""

    def __init__(self, issues=None, cl_status=None, cl_sp=None):
        issues = carregar.issues() if issues is None else issues
        cl_status = carregar.changelog_status() if cl_status is None else cl_status
        cl_sp = carregar.changelog_story_points() if cl_sp is None else cl_sp
        self.final_status = issues.set_index("issue_id").status.map(normalizar_status).to_dict()
        self.final_sp = issues.set_index("issue_id").story_point.to_dict()
        self.resolucao = issues.set_index("issue_id").resolution_date.to_dict()

        st = cl_status[cl_status.field == "status"].sort_values(["issue_id", "data"])
        st = st.assign(de=st.de.map(normalizar_status), para=st.para.map(normalizar_status))
        self.status = {i: (g.data.values, g.de.values, g.para.values) for i, g in st.groupby("issue_id")}
        sp = cl_sp[cl_sp.field == "Story Points"].sort_values(["issue_id", "data"])
        self.sp = {i: (g.data.values, g.de.values, g.para.values) for i, g in sp.groupby("issue_id")}

        # todas as entradas em status concluído (uma issue reaberta pode ter várias)
        self.conclusoes = {}
        for i, (ts, _, para) in self.status.items():
            idx = np.flatnonzero(np.isin(para, list(STATUS_CONCLUIDO)))
            if len(idx):
                self.conclusoes[i] = ts[idx]
        # sem histórico de status mas status final concluído: usa Resolution_Date
        for i, s in self.final_status.items():
            if i not in self.status and s in STATUS_CONCLUIDO and pd.notna(self.resolucao.get(i)):
                self.conclusoes[i] = np.array([np.datetime64(self.resolucao[i])])

    @staticmethod
    def _valor_em(hist, t):
        ts, de, para = hist
        k = np.searchsorted(ts, np.datetime64(t), side="right")
        if k > 0:
            return para[k - 1]
        return de[0]

    def status_em(self, iid, t):
        h = self.status.get(iid)
        return self.final_status.get(iid) if h is None else self._valor_em(h, t)

    def concluido_em(self, iid, t):
        """Status vigente em t é de concluído? (sem histórico: usa a 1ª conclusão conhecida)."""
        if iid in self.status:
            return self.status_em(iid, t) in STATUS_CONCLUIDO
        c = self.conclusoes.get(iid)
        return c is not None and c[0] <= np.datetime64(t)

    def primeira_conclusao_apos(self, iid, t):
        """Primeira entrada em status concluído estritamente depois de t (NaT se não houver)."""
        c = self.conclusoes.get(iid)
        if c is None:
            return pd.NaT
        k = np.searchsorted(c, np.datetime64(t), side="right")
        return pd.Timestamp(c[k]) if k < len(c) else pd.NaT

    def sp_em(self, iid, t):
        h = self.sp.get(iid)
        if h is None:
            v = self.final_sp.get(iid, np.nan)
        else:
            v = self._valor_em(h, t)
        try:
            v = float(v)
        except (TypeError, ValueError):
            return np.nan
        # valores fora da escala usual (negativos, 1000, 2,6e7...) são erros de preenchimento
        return v if SP_MIN <= v <= SP_MAX else np.nan
