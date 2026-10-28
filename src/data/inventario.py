"""Etapa 1 — inventário por projeto (perguntas decisivas P1, P2 e P3). Saída: data/interim/inventario_*.csv."""
import pandas as pd

from src.data import carregar

# Projeto "aderente a Scrum": >= 70% das Sprints com duração (arredondada) entre 7 e 28 dias.
DUR_MIN, DUR_MAX, PCT_ADERENCIA = 7, 28, 0.70


def p1_sprints(s=None):
    s = carregar.sprints() if s is None else s
    s = s.assign(dur=s.duracao_dias.round())
    g = s.groupby("projeto")
    t = pd.DataFrame({
        "n_sprints": g.size(),
        "com_start_end": g.apply(lambda x: (x.start_date.notna() & x.end_date.notna()).sum()),
        "dur_q1": g.duracao_dias.quantile(.25), "dur_mediana": g.duracao_dias.median(),
        "dur_q3": g.duracao_dias.quantile(.75),
        "pct_7a28": g.dur.apply(lambda x: x.between(DUR_MIN, DUR_MAX).sum() / max(x.notna().sum(), 1)),
        "itens_ligados_q1": g.n_issues_ligadas.quantile(.25),
        "itens_ligados_mediana": g.n_issues_ligadas.median(),
        "itens_ligados_q3": g.n_issues_ligadas.quantile(.75),
        "states": g.state.apply(lambda x: ", ".join(f"{k}:{v}" for k, v in x.value_counts().items())),
    })
    t["aderente_scrum"] = t.pct_7a28 >= PCT_ADERENCIA
    return t


def p3_cobertura(itens):
    """Cobertura de SP no escopo comprometido (SP vigente no início), por projeto."""
    c = itens[(itens.papel == "comprometido") & ~itens.concluido_antes_inicio]
    g = c.groupby("project_id")
    t = pd.DataFrame({"n_itens_comprometidos": g.size(), "pct_com_sp_no_inicio": g.sp.apply(lambda x: x.notna().mean()),
                      "pct_com_sp_final": g.sp_final.apply(lambda x: x.notna().mean())})
    return t


def tabela_por_projeto(resumo, itens, sprints):
    p1 = p1_sprints(sprints)
    proj = carregar.projetos().set_index("project_id").projeto
    p3 = p3_cobertura(itens).rename(index=proj)
    r = resumo.groupby("projeto").agg(
        sprints_c_comprometidos=("n_comprometidos", lambda x: (x > 0).sum()),
        comprometidos_mediana=("n_comprometidos", "median"),
        adicionados_mediana=("n_adicionados", "median"),
        cobertura_sp_mediana=("cobertura_sp", "median"),
        frac_itens_mediana=("frac_itens", "median"),
    )
    return p1.join(p3).join(r)


if __name__ == "__main__":
    itens = pd.read_csv(carregar.INTERIM / "itens_sprint.csv")
    resumo = pd.read_csv(carregar.INTERIM / "sprints_resumo.csv")
    t = tabela_por_projeto(resumo, itens, carregar.sprints())
    t.to_csv(carregar.INTERIM / "inventario_projetos.csv")
    print(t.round(2).to_string())
