# scrum-alerta-sprint

Estudo de viabilidade do trabalho de Inteligência Artificial (Redes Neurais — Perceptron, Adaline, PMC; ref.: Silva, Spatti & Flauzino, *Redes Neurais Artificiais para Engenharia e Ciências Aplicadas*).

**Pergunta:** quando já se passaram 30%, 50% ou 70% do tempo de uma Sprint, é possível prever se a equipe vai cumprir o compromisso assumido no início?
**Dados:** TAWOS v1.1 (Tawosi et al., MSR 2022), licença Apache 2.0, para uso em pesquisa.
**Resultado:** `reports/viabilidade_scrum.md`. Veredito: **SIGA COM AJUSTES**.
**Decisões de modelagem** (do usuário; ver `reports/decisoes.md`): rótulo `cumpriu = concluído / comprometido ≥ 0,8`; unidade principal story points, com contagem de itens só para verificar robustez.

**Modelagem:** Perceptron, Adaline e PMC (scikit-learn) em `src/models/`. Resultados em `reports/resultados.md`.

## Estrutura

```
sql/                 consultas versionadas (00 = esquema oficial do GitHub; 01–11 = inventário e extração)
src/data/            db.py (conexão + exportação), carregar.py, reconstrucao.py, sprints_reconstruidas.py,
                     inventario.py, amostra.py
src/features/        construir_base.py (variáveis por Sprint × k, rótulos)
src/models/          redes.py (Perceptron, Adaline, PMC com interface treinar/prever/escore), experimentos.py
                     (experimentos 1–4 no formato do livro), relatorio.py (gera reports/resultados.md)
src/analise_sinal.py baselines B0/B1, regressão logística, MLP; GroupKFold por projeto e divisão temporal
src/viz.py           estilo dos gráficos
scripts/             mysql_local.sh (MySQL 8.0.22 sem root), rodar_tudo.sh (viabilidade, etapas 1–4),
                     experimentos.sh (modelagem com as redes)
data/raw/dump/       dump baixado (não versionar)    data/raw/csv/  resultados das consultas
data/interim/        pertinência issue↔Sprint, itens por Sprint, resumo por Sprint, inventário, amostra
data/processed/      base_modelagem.csv, base_filtros.csv, balanceamento.csv
notebooks/           01_viabilidade.ipynb (lê as saídas e mostra tabelas e figuras)
reports/             viabilidade_scrum.md, esquema_tawos.md, decisoes.md, resultados.md, resultados_sinal.csv,
                     ablacao_variaveis.csv, resultados/ (CSVs das redes), figures/ (figures/redes/ = modelagem)
```

## Como reproduzir

### 1. Python

```bash
uv venv .venv --python 3.10 && uv pip install -p .venv -r requirements.txt
# ou: python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

### 2. MySQL 8 com o dump

Baixe o dump (DOI 10.5522/04/21308124; arquivo `TAWOS.sql.zip`, 637.550.449 bytes, MD5 `e9c5ecc7649d55f0cf2fb4efb5664494`):

```bash
curl -L -o data/raw/dump/TAWOS.sql.zip https://ndownloader.figshare.com/files/37806375
unzip data/raw/dump/TAWOS.sql.zip -d data/raw/dump/      # TAWOS.sql, 4,3 GB
```

**Opção A — Docker (recomendada).** Requer acesso ao daemon do Docker.

```bash
docker compose up -d
docker exec -i tawos-mysql mysql -utawos -ptawos TAWOS < data/raw/dump/TAWOS.sql
```

**Opção B — sem root.** Foi a usada neste estudo, porque o usuário não tinha acesso ao Docker. O script instala o MySQL 8.0.22 oficial (mesma versão do dump) em `~/.local/opt`, junto com `libaio` e as bibliotecas de compatibilidade `ncurses5`.

```bash
scripts/mysql_local.sh install && scripts/mysql_local.sh init && scripts/mysql_local.sh start
scripts/mysql_local.sh client --max_allowed_packet=1G TAWOS < data/raw/dump/TAWOS.sql
```

Nos dois casos o servidor fica em `127.0.0.1:3307`, com usuário e senha `tawos`/`tawos` e banco `TAWOS`. Para usar outro endereço, defina `TAWOS_DB_URL` (padrão `mysql+pymysql://tawos:tawos@127.0.0.1:3307/TAWOS`).

### 3. Pipeline

```bash
scripts/rodar_tudo.sh              # ~10 min: consultas SQL (~6 min) + reconstrução, base e modelos (~3,5 min)
SKIP_SQL=1 scripts/rodar_tudo.sh   # reaproveita os CSVs de data/raw/csv/
scripts/experimentos.sh            # ~7 min: Perceptron, Adaline e PMC -> reports/resultados.md
```

Todas as etapas são determinísticas (semente 42).
