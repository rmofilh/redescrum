#!/usr/bin/env bash
# Pergunta 3 do artigo (artigo/especificacao_q3_claude_code.md). Requer o dump do TAWOS no MySQL (ver README)
# só na 1ª etapa; com data/raw/csv/12–17 já exportados, use SKIP_SQL=1.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=${PY:-.venv/bin/python}
SKIP_SQL=${SKIP_SQL:-0}; [ "$SKIP_SQL" = 1 ] || $PY -m src.artigo.extrair_q3   # sql/12–17 -> data/raw/csv/
$PY -m src.artigo.variaveis_q3          # data/processed/variaveis_q3.csv
$PY -m src.artigo.triagem_q3            # reports/artigo/q3_triagem.csv
$PY -m src.artigo.avaliacao --q3        # reports/artigo/predicoes_q3.csv (~5 min)
$PY -m src.artigo.metricas --q3         # metricas_q3.csv, diferencas_q3.csv
$PY -m src.artigo.relatorio_q3          # diferencas_q3_pareadas.csv, q3_notas.md
