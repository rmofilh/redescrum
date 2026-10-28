#!/usr/bin/env bash
# Reproduz a fase de modelagem (Perceptron, Adaline, PMC) a partir de data/processed/base_modelagem.csv.
# Para refazer também a base a partir do MySQL: scripts/rodar_tudo.sh antes deste script.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
$PY -m src.models.experimentos   # experimentos 1–4 -> reports/resultados/*.csv, reports/figures/redes/*.png (~7 min)
$PY -m src.models.relatorio      # reports/resultados.md
