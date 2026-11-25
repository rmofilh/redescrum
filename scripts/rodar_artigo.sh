#!/usr/bin/env bash
# Reproduz os resultados do artigo a partir dos CSVs exportados do TAWOS (data/raw/csv/).
# Não precisa do MySQL; para gerar data/raw/csv/ a partir do dump, ver README (etapa 1).
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
$PY -m src.data.sprints_reconstruidas   # compromisso, escopo e conclusão por Sprint -> data/interim/
$PY -m src.features.construir_base      # variáveis em k = 0,3/0,5/0,7 -> data/processed/base_modelagem.csv
$PY -m src.artigo.derivados             # Monte Carlo e curva do burndown -> data/processed/
$PY -m src.artigo.avaliacao             # 7 modelos x 6 execuções -> reports/artigo/predicoes.csv (~10 min)
$PY -m src.artigo.metricas              # métricas e IC por reamostragem de projetos
$PY -m src.artigo.avaliacao --grade-estendida   # análise suplementar
$PY -m src.artigo.metricas --grade-estendida
$PY -m src.artigo.figuras               # reports/artigo/figuras/
