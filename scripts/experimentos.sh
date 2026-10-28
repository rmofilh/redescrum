#!/usr/bin/env bash
# Reproduz a fase de modelagem (Perceptron, Adaline, PMC) a partir de data/processed/base_modelagem.csv.
# Para refazer também a base a partir do MySQL: scripts/rodar_tudo.sh antes deste script.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
$PY -m src.models.experimentos     # experimentos 1–4 -> reports/resultados/*.csv, reports/figures/redes/*.png (~7 min)
$PY -m src.models.relatorio        # reports/resultados.md
$PY -m src.models.figuras_extras   # matrizes de confusão em k = 0,5 -> reports/figures/redes/exp4_matrizes_confusao_k05.png
$PY -m src.curva_media             # curva média de conclusão por classe -> reports/resultados/, reports/figures/ (usa data/interim/)
