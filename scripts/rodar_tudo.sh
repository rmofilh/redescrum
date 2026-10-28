#!/usr/bin/env bash
# Reproduz todas as etapas a partir do dump já importado no MySQL (ver README).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
SKIP_SQL=${SKIP_SQL:-0}; [ "$SKIP_SQL" = 1 ] || $PY -m src.data.db                       # Etapa 1: executa sql/*.sql -> data/raw/csv/
$PY -m src.data.sprints_reconstruidas    # pertinência issue<->Sprint, escopo e conclusão -> data/interim/
$PY -m src.data.inventario               # P1/P2/P3 por projeto -> data/interim/inventario_projetos.csv
$PY -m src.data.amostra                  # Etapa 2: amostra de 20 Sprints + burndowns -> reports/figures/
$PY -m src.features.construir_base       # Etapa 3: data/processed/base_modelagem.csv
$PY -m src.analise_sinal                 # Etapa 4: reports/resultados_sinal.csv + figuras métrica x k
