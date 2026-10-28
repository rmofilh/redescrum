"""Conexão com o MySQL que hospeda o dump do TAWOS e execução das consultas versionadas em sql/."""
import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = ROOT / "sql"
CSV_DIR = ROOT / "data" / "raw" / "csv"

DB_URL = os.environ.get("TAWOS_DB_URL", "mysql+pymysql://tawos:tawos@127.0.0.1:3307/TAWOS")


def engine():
    return create_engine(DB_URL)


def run_sql_file(name, eng=None):
    """Executa sql/<name>.sql e retorna um DataFrame."""
    eng = eng or engine()
    query = (SQL_DIR / f"{name}.sql").read_text()
    with eng.connect() as con:
        return pd.read_sql(text(query), con)


def export(name, eng=None):
    """Executa a consulta e salva data/raw/csv/<name>.csv."""
    df = run_sql_file(name, eng)
    CSV_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_DIR / f"{name}.csv", index=False)
    return df


if __name__ == "__main__":
    import sys

    eng = engine()
    names = sys.argv[1:] or sorted(p.stem for p in SQL_DIR.glob("[1-9]*.sql"))
    for n in names:
        df = export(n, eng)
        print(f"{n}: {len(df)} linhas")
