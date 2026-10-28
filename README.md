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
scripts/             rodar_tudo.sh (viabilidade, etapas 1–4), experimentos.sh (modelagem com as redes),
                     mysql_local.sh (MySQL 8.0.22 sem root, só para a reprodução completa)
data/raw/csv/        resultados das consultas SQL (versionados: sem o dump, são eles que permitem refazer tudo)
data/interim/        gerado: pertinência issue↔Sprint, itens e resumo por Sprint, inventário, amostra (fora do git)
data/processed/      base_modelagem.csv, base_filtros.csv, balanceamento.csv
reports/             viabilidade_scrum.md, esquema_tawos.md, decisoes.md, resultados.md, resultados_sinal.csv,
                     ablacao_variaveis.csv, resultados/ (CSVs das redes), figures/ (figures/redes/ = modelagem)
docker-compose.yml   MySQL 8.0.22 em contêiner (alternativa ao mysql_local.sh)
```

## Ambiente Python

```bash
uv venv .venv --python 3.10 && uv pip install -p .venv -r requirements.txt
# ou: python -m venv .venv && .venv/bin/pip install -r requirements.txt
```

## Reprodução rápida (a partir dos CSVs versionados, ~9 min)

Não precisa de MySQL nem do dump.

```bash
SKIP_SQL=1 scripts/rodar_tudo.sh   # ~2 min: reconstrução das Sprints, base de modelagem, análise de sinal
scripts/experimentos.sh            # ~7 min: Perceptron, Adaline e PMC -> reports/resultados/, reports/resultados.md
```

Todas as etapas são determinísticas (sementes fixas); as tabelas de `reports/resultados/` saem idênticas.

## Reprodução completa (a partir do dump do TAWOS)

1. Baixe o dump (DOI [10.5522/04/21308124](https://doi.org/10.5522/04/21308124); arquivo `TAWOS.sql.zip`, 637.550.449 bytes, MD5 `e9c5ecc7649d55f0cf2fb4efb5664494`):

   ```bash
   mkdir -p data/raw/dump
   curl -L -o data/raw/dump/TAWOS.sql.zip https://ndownloader.figshare.com/files/37806375
   unzip data/raw/dump/TAWOS.sql.zip -d data/raw/dump/      # TAWOS.sql, 4,3 GB
   ```

2. Suba o MySQL 8 e importe o dump (~6 min). Em qualquer opção o servidor fica em `127.0.0.1:3307`, usuário e senha `tawos`/`tawos`, banco `TAWOS` (outro endereço: defina `TAWOS_DB_URL`, padrão `mysql+pymysql://tawos:tawos@127.0.0.1:3307/TAWOS`).

   **Opção A — Docker.** Requer acesso ao daemon do Docker.

   ```bash
   docker compose up -d
   docker exec -i tawos-mysql mysql -utawos -ptawos TAWOS < data/raw/dump/TAWOS.sql
   ```

   **Opção B — sem root** (a usada neste estudo). Instala o MySQL 8.0.22 oficial (mesma versão do dump) em `~/.local/opt`, com `libaio` e as bibliotecas de compatibilidade `ncurses5`.

   ```bash
   scripts/mysql_local.sh install && scripts/mysql_local.sh init && scripts/mysql_local.sh start
   scripts/mysql_local.sh client --max_allowed_packet=1G TAWOS < data/raw/dump/TAWOS.sql
   ```

3. Rode o pipeline completo (as consultas SQL regravam `data/raw/csv/`):

   ```bash
   scripts/rodar_tudo.sh              # ~8 min: consultas SQL (~6 min) + etapas seguintes
   scripts/experimentos.sh            # ~7 min
   scripts/mysql_local.sh stop        # (opção B) para o servidor
   ```
