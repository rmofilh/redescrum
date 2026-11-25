"""Pergunta 3: extrai do dump do TAWOS (MySQL) os eventos usados por src/artigo/variaveis_q3.py.

1. Cria no MySQL a tabela auxiliar q3_issues com as issues de data/interim/itens_sprint.csv,
   para que as consultas tragam só essas issues (CSVs pequenos).
2. Roda sql/12–17 pelo mesmo mecanismo de src/data/db.py (export -> data/raw/csv/<nome>.csv).

Requer o MySQL com o dump importado (ver README). Uso: python -m src.artigo.extrair_q3
"""
import pandas as pd
from sqlalchemy import text

from src.data import carregar, db

CONSULTAS = ["12_comentarios", "13_changelog_assignee", "14_issue_links", "15_changelog_links",
             "16_issues_alvo", "17_changelog_status_alvo"]


def criar_q3_issues(eng):
    ids = pd.read_csv(carregar.INTERIM / "itens_sprint.csv", usecols=["issue_id"]).issue_id.unique()
    with eng.begin() as con:
        con.execute(text("DROP TABLE IF EXISTS q3_issues"))
        con.execute(text("CREATE TABLE q3_issues (issue_id INT PRIMARY KEY)"))
        for i in range(0, len(ids), 5000):
            con.execute(text("INSERT INTO q3_issues (issue_id) VALUES (:i)"),
                        [{"i": int(x)} for x in ids[i:i + 5000]])
    return len(ids)


def main():
    eng = db.engine()
    print(f"q3_issues: {criar_q3_issues(eng)} issues")
    for n in CONSULTAS:
        df = db.export(n, eng)
        print(f"{n}: {len(df)} linhas", flush=True)


if __name__ == "__main__":
    main()
