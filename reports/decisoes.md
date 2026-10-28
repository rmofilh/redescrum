# Registro de decisões

## Decisões do usuário

| # | Data | Decisão | Consequência registrada |
|---|---|---|---|
| D1 | 28/10/2026 | **Rótulo:** `cumpriu = concluído / comprometido ≥ 0,8` | Em SP, 10,9% das Sprints "cumpriu" (127 de 1.166), abaixo dos 20% do critério SIGA. A modelagem usa `class_weight="balanced"` (ou sobreamostragem só no treino) e é julgada por acurácia balanceada, F1 e AUC. L = 0,6 fica só como sensibilidade. |
| D2 | 28/10/2026 | **Unidade principal:** story points; contagem de itens só para verificar robustez | Base principal: 1.166 Sprints de 33 projetos (cobertura de SP no início ≥ 70%). Robustez: 2.027 Sprints de 35 projetos, contando itens, com o mesmo L = 0,8 (13,0% de positivos). |
| D3 | 28/10/2026 | **Modelagem:** bibliotecas prontas permitidas. Perceptron = `sklearn.linear_model.Perceptron`; Adaline = `SGDClassifier(loss="squared_error")`; PMC = `MLPClassifier` com 5, 10 ou 15 neurônios ocultos escolhidos por validação cruzada no treino. Cenários: principal SP com L = 0,8 (GroupKFold por projeto); robustez itens com L = 0,8; sensibilidade SP com L = 0,8 sem o DM | Implementado em `src/models/`; resultados em `reports/resultados.md`. |

## Decisões tomadas pelo assistente durante o estudo de viabilidade

| # | Decisão | Motivo | Situação |
|---|---|---|---|
| 1 | MySQL 8.0.22 em espaço de usuário, em vez de Docker | sem acesso ao socket do Docker; evitar `sudo` | vigente |
| 2 | Usuário de banco `tawos/tawos` | a conexão TCP do root era recusada | vigente |
| 3 | Unidade de análise = Sprint × projeto | `Sprint.JiraID` só é único por projeto | vigente |
| 4 | Escopo reconstruído pelo histórico do campo Sprint, e não por `Issue.Sprint_ID` | `Sprint_ID` é inconsistente (1ª Sprint em 61% dos casos) | vigente |
| 5 | Início = `Start_Date` + 1 h de tolerância | pico de entradas entre 15 min e 1 h; `Activated_Date` vazio em 92% | vigente |
| 6 | "Concluído" = {closed, resolved, done, complete, completed}, com nomes normalizados; Won't Fix, Invalid e Duplicate não contam | categoria Done do Jira; entrega real | vigente |
| 7 | Itens já concluídos no início saem do compromisso; itens reabertos ficam | 2.310 itens residuais | vigente |
| 8 | Itens removidos durante a Sprint contam como não cumpridos | o compromisso original não foi entregue | vigente |
| 9 | SP congelado no valor do início (ou da entrada); SP fora de [0, 100] = ausente | sem vazamento; valores absurdos | vigente |
| 10 | Prazo do rótulo = `End_Date` | roteiro; só 2,5% dos itens fecham no dia seguinte | vigente |
| 11 | DM mantido, apesar de "não aderente" pelo critério de 7–28 dias | ciclos mensais; 93% das Sprints cabem em 5–31 dias | vigente (sensibilidade sem o DM em `resultados.md`) |
| 12 | Duas unidades (SP com cobertura ≥ 70%, e itens) | cobertura de SP no início é baixa em vários projetos | vigente, hierarquizada por D2 |
| 13 | Recomendação de L = 0,6 | L = 0,8 dá 10,9% de positivos (< 20%) | **substituída por D1** |
| 14 | Modelo único com os três k juntos; GroupKFold com 5 dobras; divisão temporal 70/30 | avaliar por k sem treinar três modelos | vigente |
| 15 | `log1p` nas razões; regressão logística balanceada; MLP com sobreamostragem | caudas longas; desbalanceamento | vigente |
| 16 | Lista de status "a fazer/aguardando" montada pelo assistente | define `itens_em_andamento_rel` | vigente |
| 17 | Velocidade só com Sprints do mesmo projeto já encerradas no início | evitar vazamento | vigente |

## Arrumação final (28/10/2026, autorizada pelo usuário)

| Removido | Motivo |
|---|---|
| `data/raw/dump/` (TAWOS.sql, 4,1 GB; TAWOS.sql.zip, 609 MB; tempos de download e importação) | rebaixável pelo DOI 10.5522/04/21308124; os CSVs de `data/raw/csv/` bastam para refazer tudo |
| Servidor MySQL local (`~/.local/share/tawos-mysql`, 6,5 GB; `~/.local/opt/mysql*`, 360 MB) | `scripts/mysql_local.sh install/init` recria |
| Cenários L = 0,6 (figuras `metrica_vs_k_*_L06_*` e linhas de `resultados_sinal.csv`/`ablacao_variaveis.csv`) | descartados por D1; `analise_sinal.CENARIOS` só tem L = 0,8; números antigos ficam no relatório como registro (commit `5560aa1`) |
| 17 dos 20 burndowns da amostra | não citados no relatório; `amostra.py` só desenha MULE_4351, MESOS_425 e TIMOB_4697 (as checagens das 20 continuam em `amostra_poc.csv`) |
| `notebooks/01_viabilidade.ipynb` (e `jupyter`/`nbconvert` do `requirements.txt`) | só repetia tabelas e figuras dos relatórios |
| `__pycache__/` | gerado pelo Python |
| `data/interim/` sai do git (fica no disco) | regenerado por `rodar_tudo.sh` a partir dos CSVs |
