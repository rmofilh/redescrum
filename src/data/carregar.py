"""Leitura dos CSVs exportados de sql/ (data/raw/csv) com tipos corretos."""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CSV = ROOT / "data" / "raw" / "csv"
INTERIM = ROOT / "data" / "interim"
PROCESSED = ROOT / "data" / "processed"
FIG = ROOT / "reports" / "figures"


def _datas(df, cols):
    # errors="coerce": há uma Sprint com ano 0015 (erro de preenchimento) -> NaT
    for c in cols:
        df[c] = pd.to_datetime(df[c], errors="coerce")
    return df


def projetos():
    return pd.read_csv(CSV / "01_projetos.csv")


def sprints():
    s = pd.read_csv(CSV / "02_sprints.csv")
    s = _datas(s, ["start_date", "end_date", "activated_date", "complete_date"])
    s["duracao_dias"] = (s.end_date - s.start_date).dt.total_seconds() / 86400
    return s


def issues():
    i = pd.read_csv(CSV / "08_issues_sprint.csv")
    return _datas(i, ["creation_date", "resolution_date", "estimation_date"])


def changelog_sprint():
    c = pd.read_csv(CSV / "07_changelog_sprint.csv", dtype={"from_value": str, "to_value": str})
    return _datas(c, ["data"])


def changelog_status():
    return _datas(pd.read_csv(CSV / "09_changelog_status.csv"), ["data"])


def changelog_story_points():
    return _datas(pd.read_csv(CSV / "10_changelog_story_points.csv"), ["data"])


def changelog_flagged():
    return _datas(pd.read_csv(CSV / "11_changelog_flagged.csv"), ["data"])


def parse_lista(v):
    """'299, 629' -> {299, 629}; vazio/NaN -> set()."""
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return frozenset()
    return frozenset(int(x) for x in str(v).split(",") if x.strip())
