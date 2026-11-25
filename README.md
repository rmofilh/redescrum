# Do Learned Models Beat the Burndown? — replication package

Code and data to reproduce every number, table and figure of the paper *Do Learned Models Beat the Burndown? An Empirical Comparison of Early Sprint-Outcome Prediction on Open-Source Agile Projects*.

**Question.** When 30%, 50% or 70% of a Sprint's time has elapsed, can we predict whether the team will deliver at least 80% of the story points it committed to at the start? And do learned models (logistic regression, MLP, gradient boosting, an MLP over the burndown curve) predict this better than the burndown itself?

**Data.** TAWOS v1.1 (Tawosi et al., MSR 2022; DOI [10.5522/04/21308124](https://doi.org/10.5522/04/21308124)), Apache License 2.0. The SQL query results the analysis needs are versioned in `data/raw/csv/` (≈ 43 MB), so the full analysis runs without the 4.3 GB dump or a database server.

## Environment

The results in `reports/artigo/` were produced with Python 3.13 and the versions pinned in `requirements.txt` (pandas 2.3.3, NumPy 2.2.6, SciPy 1.15.3, scikit-learn 1.7.2, matplotlib 3.10.9, statsmodels 0.15.0).

```bash
python -m venv .venv && .venv/bin/pip install -r requirements.txt
# or: uv venv .venv --python 3.13 && uv pip install -p .venv -r requirements.txt
```

Every step uses fixed random seeds.

## Reproducing the paper (from the versioned CSVs)

```bash
scripts/rodar_artigo.sh
```

The script runs, in order:

| Step | Module | Output |
|---|---|---|
| Sprint reconstruction (commitment, scope changes, completion) | `src.data.sprints_reconstruidas` | `data/interim/` |
| Features at k = 0.3 / 0.5 / 0.7 and labels | `src.features.construir_base` | `data/processed/base_modelagem.csv` |
| Monte Carlo simulation and burndown curves | `src.artigo.derivados` | `data/processed/monte_carlo.csv`, `curvas.csv` |
| 7 models × 2 evaluation splits × sensitivity scenarios | `src.artigo.avaliacao` | `reports/artigo/predicoes.csv`, `parametros_por_dobra.csv` |
| Metrics and project-cluster bootstrap intervals | `src.artigo.metricas` | `reports/artigo/metricas.csv`, `diferencas.csv`, `por_projeto.csv`, `calibracao.csv` |
| Supplementary extended hyperparameter grid | `src.artigo.avaliacao --grade-estendida`, `src.artigo.metricas --grade-estendida` | `reports/artigo/*_grade_estendida.csv` |
| Figures | `src.artigo.figuras` | `reports/artigo/figuras/fig_diferencas.png`, `fig_calibracao.png` |

`python -m src.artigo.resumo` prints all result tables in Markdown; `reports/artigo/resumo_resultados.md` holds a commented copy.

### Variables beyond the burndown (RQ3)

```bash
SKIP_SQL=1 scripts/rodar_q3.sh
```

Starts from the versioned `data/raw/csv/12–17` and runs: variable construction (`src.artigo.variaveis_q3` → `data/processed/variaveis_q3.csv`), the incremental screening (`src.artigo.triagem_q3` → `reports/artigo/q3_triagem.csv`), the re-evaluation of the learned models with the approved variables (`src.artigo.avaliacao --q3`, `src.artigo.metricas --q3` → `reports/artigo/*_q3.csv`) and the report (`src.artigo.relatorio_q3` → `reports/artigo/q3_notas.md`, `diferencas_q3_pareadas.csv`). Without `SKIP_SQL=1`, it first re-exports queries 12–17 from the TAWOS database (`src.artigo.extrair_q3`).

### Where each result comes from

| In the paper | File | Filter |
|---|---|---|
| Performance tables (new-team and team-with-history splits) | `reports/artigo/metricas.csv` | `cenario == "principal"`, by `divisao` and `k` |
| Differences to the calibrated burndown (Figure 1) | `reports/artigo/diferencas.csv` | `cenario == "principal"` |
| Sensitivity analyses (L = 0.7, L = 0.6, item counts, without project DM) | `reports/artigo/diferencas.csv` | `cenario` in `L70`, `L60`, `itens`, `sem_DM` |
| Extended grid | `reports/artigo/diferencas_grade_estendida.csv` | — |
| Per-project results | `reports/artigo/por_projeto.csv` | — |
| Reliability diagram (Figure 2) | `reports/artigo/calibracao.csv` | — |
| Learned cutoffs and chosen hyperparameters per fold | `reports/artigo/parametros_por_dobra*.csv` | — |
| RQ3 screening | `reports/artigo/q3_triagem.csv` | `p_wald_agrupado`, `passa` |
| RQ3 re-evaluation: vs. calibrated burndown / with vs. without the new variable | `reports/artigo/diferencas_q3.csv` / `diferencas_q3_pareadas.csv` | models with suffix `_q3` |

## Full reproduction (from the TAWOS dump)

Only needed to regenerate `data/raw/csv/` from the original database.

1. Download the dump (file `TAWOS.sql.zip`, 637,550,449 bytes, MD5 `e9c5ecc7649d55f0cf2fb4efb5664494`):

   ```bash
   mkdir -p data/raw/dump
   curl -L -o data/raw/dump/TAWOS.sql.zip https://ndownloader.figshare.com/files/37806375
   unzip data/raw/dump/TAWOS.sql.zip -d data/raw/dump/      # TAWOS.sql, 4.3 GB
   ```

2. Start MySQL 8 and import the dump. Either way the server listens on `127.0.0.1:3307`, user/password `tawos`/`tawos`, database `TAWOS` (override with `TAWOS_DB_URL`, default `mysql+pymysql://tawos:tawos@127.0.0.1:3307/TAWOS`). Install the extra packages first: `.venv/bin/pip install -r requirements-sql.txt`.

   **Option A — Docker.**

   ```bash
   docker compose up -d
   docker exec -i tawos-mysql mysql -utawos -ptawos TAWOS < data/raw/dump/TAWOS.sql
   ```

   **Option B — without root.** Installs the official MySQL 8.0.22 (the dump's version) under `~/.local/opt`.

   ```bash
   scripts/mysql_local.sh install && scripts/mysql_local.sh init && scripts/mysql_local.sh start
   scripts/mysql_local.sh client --max_allowed_packet=1G TAWOS < data/raw/dump/TAWOS.sql
   ```

3. Export the query results and run the paper pipeline:

   ```bash
   .venv/bin/python -m src.data.db     # runs sql/01–11 -> data/raw/csv/
   scripts/rodar_artigo.sh
   scripts/rodar_q3.sh                 # runs sql/12–17 (they need an auxiliary table the script creates), then RQ3
   scripts/mysql_local.sh stop         # option B only
   ```

## Repository layout

```
sql/                  versioned queries (00 = official TAWOS schema; 01–11 = extraction)
data/raw/csv/         query results (versioned; the starting point of the analysis)
src/data/             db.py (query export), carregar.py, reconstrucao.py (Sprint membership from the
                      changelog, story points at Sprint start), sprints_reconstruidas.py
src/features/         construir_base.py (features per Sprint × k, labels, filters)
src/artigo/           derivados.py, avaliacao.py, metricas.py, figuras.py, resumo.py;
                      RQ3: extrair_q3.py, variaveis_q3.py, triagem_q3.py, relatorio_q3.py
scripts/              rodar_artigo.sh (paper pipeline), rodar_q3.sh (RQ3), mysql_local.sh
reports/artigo/       all results of the paper (CSVs, figures, summary)
docker-compose.yml    MySQL 8.0.22 container (option A)
```

Identifiers and comments in the code are in Portuguese. Key terms: *Sprint comprometida* = committed scope at Sprint start; *concluído* = done; *folga* = slack (% done − % elapsed); *equipe nova* = new-team split (grouped by project); *equipe com histórico* = team-with-history split (temporal); *cenário* = scenario; *dobra* = fold.

## Citation

Paper: *to be added after acceptance.* Replication package: Zenodo DOI *to be added*.

If you use the data, please also cite TAWOS:

> Tawosi, V., Al-Subaihin, A., Moussa, R., Sarro, F. (2022). A Versatile Dataset of Agile Open Source Software Projects. In *Proceedings of the 19th International Conference on Mining Software Repositories (MSR)*, pp. 707–711. ACM. https://doi.org/10.1145/3524842.3528029
