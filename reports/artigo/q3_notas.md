# Pergunta 3: variáveis além do burndown

> Gerado por `src/artigo/relatorio_q3.py` a partir dos CSVs de `reports/artigo/` e `data/`; nenhum número foi digitado à mão.
> Especificação: `artigo/especificacao_q3_claude_code.md`. Decisões: `artigo/base_decisoes_artigo.md` (A8, A9).
> Reprodução (com o dump no MySQL): `scripts/rodar_q3.sh`.

## 1. Resumo

- Lista fechada de 4 variáveis, todas construídas. Nenhuma foi acrescentada nem redefinida depois de ver resultados.
- **Aprovadas na triagem** (p < 0,05 com erros agrupados por projeto em ≥ 2 dos 3 valores de k): `historico_cumprimento`.
- **Reprovadas:** `comentarios_recentes_rel`, `trocas_responsavel_rel`, `dependencias_abertas_rel`.
- A reavaliação (seção 6) compara cada modelo aprendido com e sem as variáveis aprovadas, contra o burndown calibrado e diretamente (pareado).

## 2. O que foi extraído

Dump TAWOS v1.1 baixado de novo do Figshare (`TAWOS.sql.zip`, MD5 `e9c5ecc7649d55f0cf2fb4efb5664494`, igual ao do README) e importado no MySQL 8.0.22 local (`scripts/mysql_local.sh`). As consultas filtram as issues de `data/interim/itens_sprint.csv` por meio da tabela auxiliar `q3_issues` (2027 Sprints da base; 46.080 issues), criada por `src/artigo/extrair_q3.py`, que exporta os CSVs com `src/data/db.py`.

| Consulta | Conteúdo | Linhas | Issues |
|---|---|---|---|
| `sql/12_comentarios.sql` | datas dos comentários | 187.302 | 35.737 |
| `sql/13_changelog_assignee.sql` | mudanças de assignee | 54.314 | 28.095 |
| `sql/14_issue_links.sql` | ligações (estado final, sem data) | 32.651 | 16.981 |
| `sql/15_changelog_links.sql` | Change_Log com Field = 'Link' (adição/remoção datada) | 50.155 | 21.729 |
| `sql/16_issues_alvo.sql` | issues alvo de ligações de bloqueio | 4.329 | 4.329 |
| `sql/17_changelog_status_alvo.sql` | transições de status das issues alvo | 26.430 | 4.137 |

As consultas 16 e 17 não estavam na especificação. Elas foram necessárias para cumprir a definição de `dependencias_abertas_rel`: a maioria das issues alvo de bloqueio fica fora das Sprints e não está em `08_issues_sprint.csv`/`09_changelog_status.csv`. Sem elas, `LinhaDoTempo` não saberia se o alvo estava concluído em t_k. Têm o mesmo formato de 08 e 09, e `LinhaDoTempo` é reaproveitada sem mudança.

## 3. Decisão sobre as dependências

Verificação pedida (`SELECT Field, COUNT(*) FROM Change_Log WHERE Field LIKE '%ink%' GROUP BY Field`): o `Change_Log` registra ligações em `Field = 'Link'` (448.089 linhas na base toda). Na adição, `To_Value` traz a chave da issue alvo e `To_String` o texto ("This issue is blocked by MESOS-10162"); na remoção, `From_Value` traz a chave. **Decisão: a variável foi construída**, datando cada ligação pelo `Change_Log`.

- Ligações que partem das issues da base: 32.651; de bloqueio: 6.282 (nomes no Jira: Blocks 3.872, Blockers 1.433, Blocker 737, Block 240).
- Com data no `Change_Log` da issue de origem: 6.200 (98,7%). As 82 sem registro não são datáveis e **não contam** (contá-las exigiria supor uma data).
- Tipo de bloqueio identificado pela descrição (`blocks` / `is blocked by`), porque o nome varia entre projetos (Blocks, Blockers, Blocker, Block). Ficam fora o tipo `Blocked`/`Blocked` (20 linhas na base toda, sem direção) e tipos de dependência que não são bloqueio (`Depends`, `Dependency`, Gantt).
- A ligação conta em t_k se o último evento do `Change_Log` para aquela chave com data ≤ t_k for uma adição (cobre ligações removidas e recriadas). Partimos do estado final de `Issue_Link`, como pede a especificação; ligações criadas e removidas antes do fim não aparecem em `Issue_Link` e não são consideradas.

## 4. Definições operacionais

Todas com eventos de data ≤ t_k, t_k = início + k·(fim − início). Itens já concluídos no início ficam fora (como em `construir_base.py`); o denominador é o nº de itens comprometidos.

| Variável | Como foi calculada |
|---|---|
| `comentarios_recentes_rel` | comentários com data em (t_k − 2 dias, t_k] em itens da Sprint abertos em t_k: comprometidos não removidos e adicionados até t_k não removidos, ainda não concluídos em t_k |
| `trocas_responsavel_rel` | linhas do `Change_Log` com `Field = 'assignee'` e data em (início, t_k] nos itens comprometidos (inclui a primeira atribuição, de vazio para alguém) |
| `dependencias_abertas_rel` | itens comprometidos não removidos e não concluídos em t_k com ≥ 1 ligação de bloqueio, existente em t_k, com issue que não estava na Sprint em t_k e cujo status em t_k não era de conclusão (`LinhaDoTempo.concluido_em`) |
| `historico_cumprimento` | fração das até 3 Sprints anteriores do mesmo projeto, encerradas até o início (mesma janela do Monte Carlo, `derivados.historico_anterior`), com fração concluída ≥ 0,8 (`frac_sp` na unidade SP, `frac_itens` na unidade itens). Sprints da janela sem fração definida (sem SP comprometidos) ficam fora do denominador; sem nenhuma, a variável fica ausente |

Na unidade SP (k = 0,5), nº de Sprints anteriores com fração definida: 0 → 22, 1 → 88, 2 → 307, 3 → 742.

Conferência manual (Sprint 438, MESOS, k = 0,5): mudanças de responsável e ligações de bloqueio conferidas contra consultas diretas no MySQL; das 16 ligações de bloqueio dos itens comprometidos, só uma atende a todas as condições (existe em t_k, alvo fora da Sprint e aberto), e a variável vale 1/34.

### Descritivas (`data/processed/variaveis_q3.csv`)

| Unidade | k | Variável | Média | Mediana | % > 0 | Ausentes |
|---|---|---|---|---|---|---|
| itens | 0.3 | `comentarios_recentes_rel` | 0.185 | 0.020 | 51% | 0 |
| itens | 0.3 | `trocas_responsavel_rel` | 0.243 | 0.053 | 55% | 0 |
| itens | 0.3 | `dependencias_abertas_rel` | 0.023 | 0.000 | 22% | 0 |
| itens | 0.3 | `historico_cumprimento` | 0.142 | 0.000 | 26% | 53 |
| itens | 0.5 | `comentarios_recentes_rel` | 0.157 | 0.000 | 46% | 0 |
| itens | 0.5 | `trocas_responsavel_rel` | 0.304 | 0.087 | 61% | 0 |
| itens | 0.5 | `dependencias_abertas_rel` | 0.022 | 0.000 | 21% | 0 |
| itens | 0.5 | `historico_cumprimento` | 0.142 | 0.000 | 26% | 53 |
| itens | 0.7 | `comentarios_recentes_rel` | 0.152 | 0.000 | 47% | 0 |
| itens | 0.7 | `trocas_responsavel_rel` | 0.373 | 0.125 | 65% | 0 |
| itens | 0.7 | `dependencias_abertas_rel` | 0.021 | 0.000 | 21% | 0 |
| itens | 0.7 | `historico_cumprimento` | 0.142 | 0.000 | 26% | 53 |
| sp | 0.3 | `comentarios_recentes_rel` | 0.186 | 0.034 | 54% | 0 |
| sp | 0.3 | `trocas_responsavel_rel` | 0.161 | 0.000 | 50% | 0 |
| sp | 0.3 | `dependencias_abertas_rel` | 0.028 | 0.000 | 27% | 0 |
| sp | 0.3 | `historico_cumprimento` | 0.131 | 0.000 | 25% | 22 |
| sp | 0.5 | `comentarios_recentes_rel` | 0.158 | 0.000 | 48% | 0 |
| sp | 0.5 | `trocas_responsavel_rel` | 0.206 | 0.045 | 56% | 0 |
| sp | 0.5 | `dependencias_abertas_rel` | 0.028 | 0.000 | 27% | 0 |
| sp | 0.5 | `historico_cumprimento` | 0.131 | 0.000 | 25% | 22 |
| sp | 0.7 | `comentarios_recentes_rel` | 0.165 | 0.019 | 51% | 0 |
| sp | 0.7 | `trocas_responsavel_rel` | 0.245 | 0.071 | 61% | 0 |
| sp | 0.7 | `dependencias_abertas_rel` | 0.025 | 0.000 | 26% | 0 |
| sp | 0.7 | `historico_cumprimento` | 0.131 | 0.000 | 25% | 22 |

## 5. Triagem (teste incremental)

Cenário principal (SP, L = 0,8), 1.159 Sprints, 33 projetos, separadamente em cada k. M0: `y ~ pct_concluido`; M1: `y ~ pct_concluido + variável` (regressão logística, variável na escala original). p (LR): razão de verossimilhança, 1 g.l., supõe Sprints independentes. p (Wald agrupado): coeficiente da variável em M1 com erros agrupados por projeto (`statsmodels`, `cov_type="cluster"`). Para `historico_cumprimento`, M0 e M1 usam as mesmas Sprints (casos completos: 1.137). AUC na amostra (sem validação), só como referência de tamanho de efeito. Critério declarado: passa se p (Wald agrupado) < 0,05 em ≥ 2 dos 3 k. Arquivo: `reports/artigo/q3_triagem.csv`.

| Variável | k | n | coef. | EP agrupado | p (LR) | p (Wald agrupado) | AUC sem → com | Passa |
|---|---|---|---|---|---|---|---|---|
| `comentarios_recentes_rel` | 0.3 | 1159 | +0.080 | 0.315 | 0.776 | 0.801 | 0.772 → 0.772 | não |
| `comentarios_recentes_rel` | 0.5 | 1159 | -0.263 | 0.551 | 0.499 | 0.632 | 0.849 → 0.848 | não |
| `comentarios_recentes_rel` | 0.7 | 1159 | +0.069 | 0.337 | 0.850 | 0.838 | 0.904 → 0.904 | não |
| `trocas_responsavel_rel` | 0.3 | 1159 | +0.517 | 0.334 | 0.012 | 0.122 | 0.772 → 0.785 | não |
| `trocas_responsavel_rel` | 0.5 | 1159 | +0.409 | 0.226 | 0.037 | 0.070 | 0.849 → 0.854 | não |
| `trocas_responsavel_rel` | 0.7 | 1159 | +0.173 | 0.259 | 0.323 | 0.504 | 0.904 → 0.905 | não |
| `dependencias_abertas_rel` | 0.3 | 1159 | -5.357 | 3.815 | 0.036 | 0.160 | 0.772 → 0.782 | não |
| `dependencias_abertas_rel` | 0.5 | 1159 | -3.249 | 3.822 | 0.231 | 0.395 | 0.849 → 0.850 | não |
| `dependencias_abertas_rel` | 0.7 | 1159 | +1.001 | 2.564 | 0.740 | 0.696 | 0.904 → 0.904 | não |
| `historico_cumprimento` | 0.3 | 1137 | +1.859 | 0.312 | 1.59e-07 | 2.69e-09 | 0.772 → 0.808 | sim |
| `historico_cumprimento` | 0.5 | 1137 | +1.437 | 0.316 | 1.68e-04 | 5.50e-06 | 0.847 → 0.864 | sim |
| `historico_cumprimento` | 0.7 | 1137 | +1.165 | 0.332 | 0.004 | 4.49e-04 | 0.902 → 0.906 | sim |

Leitura: `dependencias_abertas_rel` (k = 0,3); `trocas_responsavel_rel` (k = 0,3, 0,5) têm p < 0,05 no teste ingênuo, mas não com erros agrupados por projeto: o efeito aparente vem de diferenças entre projetos, não de informação nova sobre a Sprint.

## 6. Reavaliação com as variáveis aprovadas

Conjunto novo = `TABULAR` + `historico_cumprimento` (`avaliacao.tabular_q3`; `TABULAR` não mudou). Mesmos modelos aprendidos, grades, sementes, cortes de decisão e divisões da rodada principal; sem rebalanceamento. As ausências (Sprints sem anteriores) são tratadas pelo mesmo pré-processamento (mediana + indicador). Arquivos: `predicoes_q3.csv`, `parametros_por_dobra_q3.csv`, `metricas_q3.csv`, `diferencas_q3.csv`, `diferencas_q3_pareadas.csv`.

Os modelos sem as variáveis novas foram rodados de novo no mesmo arquivo, para que a comparação use as mesmas Sprints e os mesmos sorteios. Conferência: 31.302 predições coincidem com `reports/artigo/predicoes.csv` (maior diferença absoluta no escore: 7.8e-16).

▲/▼: intervalo de 95% (reamostragem de projetos, 2.000 sorteios) acima/abaixo de zero.

### Equipe nova (StratifiedGroupKFold por projeto)

**Diferença de ROC-AUC para o burndown calibrado**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | +0.010 [-0.022; +0.037] | -0.002 [-0.031; +0.020] | -0.003 [-0.019; +0.009] |
| Regressão logística + Q3 | +0.035 [+0.001; +0.062] ▲ | +0.010 [-0.025; +0.037] | -0.001 [-0.019; +0.010] |
| MLP | -0.048 [-0.092; +0.006] | -0.045 [-0.085; -0.007] ▼ | -0.027 [-0.051; -0.008] ▼ |
| MLP + Q3 | +0.006 [-0.039; +0.044] | -0.017 [-0.061; +0.019] | -0.014 [-0.036; -0.000] ▼ |
| Gradient Boosting | -0.049 [-0.104; +0.035] | -0.050 [-0.077; -0.000] ▼ | -0.033 [-0.055; +0.001] |
| Gradient Boosting + Q3 | -0.029 [-0.064; +0.029] | -0.042 [-0.069; +0.006] | -0.031 [-0.053; -0.001] ▼ |
| MLP + curva | -0.015 [-0.055; +0.031] | -0.022 [-0.057; +0.010] | -0.010 [-0.032; +0.011] |
| MLP + curva + Q3 | +0.001 [-0.050; +0.043] | -0.015 [-0.072; +0.021] | -0.014 [-0.048; +0.004] |

**Diferença de PR-AUC para o burndown calibrado**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | -0.018 [-0.047; +0.017] | -0.021 [-0.046; +0.007] | -0.020 [-0.048; +0.008] |
| Regressão logística + Q3 | +0.022 [-0.008; +0.054] | -0.004 [-0.032; +0.022] | -0.005 [-0.035; +0.019] |
| MLP | -0.066 [-0.099; -0.013] ▼ | -0.055 [-0.084; -0.024] ▼ | -0.044 [-0.074; -0.020] ▼ |
| MLP + Q3 | -0.066 [-0.101; -0.031] ▼ | -0.108 [-0.160; -0.049] ▼ | -0.098 [-0.147; -0.045] ▼ |
| Gradient Boosting | -0.043 [-0.097; +0.041] | -0.054 [-0.089; +0.005] | -0.055 [-0.104; +0.010] |
| Gradient Boosting + Q3 | -0.030 [-0.076; +0.044] | -0.047 [-0.083; +0.007] | -0.047 [-0.088; +0.008] |
| MLP + curva | -0.056 [-0.089; -0.002] ▼ | -0.058 [-0.091; -0.019] ▼ | -0.070 [-0.113; -0.020] ▼ |
| MLP + curva + Q3 | -0.024 [-0.055; +0.012] | -0.022 [-0.070; +0.015] | -0.040 [-0.081; -0.009] ▼ |

**Efeito direto das variáveis novas: mesmo modelo, sem → com (ROC-AUC); diferença [IC 95%]**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | 0.768 → 0.793; +0.025 [-0.000; +0.039] | 0.839 → 0.851; +0.012 [-0.003; +0.025] | 0.896 → 0.899; +0.003 [-0.006; +0.007] |
| MLP | 0.710 → 0.764; +0.054 [-0.025; +0.123] | 0.796 → 0.824; +0.028 [-0.014; +0.072] | 0.873 → 0.886; +0.013 [-0.009; +0.034] |
| Gradient Boosting | 0.710 → 0.730; +0.020 [-0.014; +0.044] | 0.791 → 0.799; +0.008 [-0.002; +0.015] | 0.867 → 0.868; +0.002 [-0.007; +0.007] |
| MLP + curva | 0.744 → 0.760; +0.016 [-0.022; +0.038] | 0.819 → 0.826; +0.007 [-0.027; +0.029] | 0.889 → 0.885; -0.004 [-0.027; +0.011] |

**Idem, PR-AUC**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | 0.380 → 0.420; +0.040 [+0.004; +0.066] ▲ | 0.503 → 0.521; +0.017 [-0.011; +0.033] | 0.619 → 0.634; +0.015 [-0.008; +0.033] |
| MLP | 0.331 → 0.332; +0.001 [-0.051; +0.034] | 0.469 → 0.417; -0.052 [-0.106; +0.006] | 0.595 → 0.542; -0.053 [-0.108; +0.003] |
| Gradient Boosting | 0.355 → 0.368; +0.013 [-0.010; +0.027] | 0.471 → 0.478; +0.007 [-0.006; +0.017] | 0.584 → 0.592; +0.008 [-0.011; +0.023] |
| MLP + curva | 0.341 → 0.373; +0.032 [-0.016; +0.071] | 0.467 → 0.503; +0.036 [-0.025; +0.081] | 0.570 → 0.600; +0.030 [-0.026; +0.072] |

### Equipe com histórico (5 cortes no tempo)

**Diferença de ROC-AUC para o burndown calibrado**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | +0.046 [-0.001; +0.116] | +0.012 [-0.021; +0.034] | +0.002 [-0.012; +0.020] |
| Regressão logística + Q3 | +0.074 [-0.001; +0.175] | +0.032 [-0.027; +0.099] | -0.007 [-0.030; +0.004] |
| MLP | +0.049 [-0.020; +0.147] | +0.006 [-0.028; +0.030] | -0.013 [-0.050; +0.014] |
| MLP + Q3 | +0.057 [-0.039; +0.198] | -0.001 [-0.082; +0.087] | -0.040 [-0.097; -0.017] ▼ |
| Gradient Boosting | +0.043 [-0.033; +0.170] | +0.020 [-0.028; +0.059] | -0.010 [-0.042; +0.022] |
| Gradient Boosting + Q3 | +0.063 [-0.013; +0.200] | +0.030 [-0.032; +0.082] | -0.019 [-0.061; +0.006] |
| MLP + curva | +0.028 [-0.049; +0.138] | -0.013 [-0.071; +0.016] | -0.008 [-0.044; +0.024] |
| MLP + curva + Q3 | +0.067 [-0.017; +0.203] | +0.013 [-0.069; +0.085] | -0.010 [-0.039; +0.013] |

**Diferença de PR-AUC para o burndown calibrado**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | -0.011 [-0.050; +0.029] | -0.004 [-0.035; +0.032] | -0.007 [-0.041; +0.059] |
| Regressão logística + Q3 | -0.003 [-0.047; +0.043] | -0.023 [-0.057; +0.020] | -0.007 [-0.057; +0.081] |
| MLP | +0.017 [-0.013; +0.049] | +0.000 [-0.036; +0.024] | -0.016 [-0.049; +0.106] |
| MLP + Q3 | +0.011 [-0.033; +0.034] | -0.044 [-0.087; -0.006] ▼ | -0.068 [-0.131; -0.004] ▼ |
| Gradient Boosting | -0.012 [-0.061; +0.034] | -0.024 [-0.070; +0.060] | -0.064 [-0.111; +0.032] |
| Gradient Boosting + Q3 | -0.002 [-0.039; +0.024] | -0.013 [-0.054; +0.071] | -0.065 [-0.117; +0.018] |
| MLP + curva | -0.060 [-0.101; +0.004] | -0.062 [-0.113; -0.003] ▼ | -0.115 [-0.191; +0.004] |
| MLP + curva + Q3 | -0.012 [-0.061; +0.017] | -0.009 [-0.069; +0.032] | -0.102 [-0.163; +0.031] |

**Efeito direto das variáveis novas: mesmo modelo, sem → com (ROC-AUC); diferença [IC 95%]**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | 0.735 → 0.764; +0.028 [-0.039; +0.114] | 0.823 → 0.843; +0.020 [-0.029; +0.094] | 0.907 → 0.898; -0.009 [-0.032; +0.001] |
| MLP | 0.739 → 0.747; +0.008 [-0.074; +0.106] | 0.817 → 0.810; -0.007 [-0.068; +0.076] | 0.891 → 0.864; -0.027 [-0.082; -0.006] ▼ |
| Gradient Boosting | 0.733 → 0.753; +0.020 [-0.027; +0.080] | 0.831 → 0.840; +0.010 [-0.027; +0.058] | 0.894 → 0.886; -0.008 [-0.030; -0.000] ▼ |
| MLP + curva | 0.718 → 0.756; +0.039 [-0.035; +0.137] | 0.798 → 0.824; +0.026 [-0.026; +0.121] | 0.896 → 0.894; -0.002 [-0.037; +0.030] |

**Idem, PR-AUC**

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Regressão logística | 0.259 → 0.266; +0.008 [-0.018; +0.030] | 0.364 → 0.345; -0.019 [-0.054; +0.015] | 0.583 → 0.584; +0.000 [-0.065; +0.078] |
| MLP | 0.287 → 0.281; -0.006 [-0.046; +0.023] | 0.368 → 0.324; -0.044 [-0.078; -0.000] ▼ | 0.574 → 0.522; -0.052 [-0.184; -0.005] ▼ |
| Gradient Boosting | 0.258 → 0.267; +0.010 [-0.019; +0.031] | 0.344 → 0.355; +0.011 [-0.023; +0.036] | 0.526 → 0.526; -0.001 [-0.049; +0.023] |
| MLP + curva | 0.210 → 0.258; +0.048 [-0.002; +0.084] | 0.306 → 0.359; +0.053 [-0.033; +0.125] | 0.475 → 0.488; +0.013 [-0.051; +0.102] |

### Parâmetros escolhidos no treino (com as variáveis novas)

| Divisão | Modelo | Escolhas nas 5 dobras |
|---|---|---|
| equipe_com_historico | gradient_boosting_q3 | {'m__learning_rate': 0.05, 'm__max_depth': 2, 'm__max_iter': 100} ×5 |
| equipe_com_historico | mlp_curva_q3 | {'m__alpha': 0.1, 'm__hidden_layer_sizes': (5,)} ×5 |
| equipe_com_historico | mlp_q3 | {'m__alpha': 0.1, 'm__hidden_layer_sizes': (5,)} ×3; {'m__alpha': 0.1, 'm__hidden_layer_sizes': (10,)} ×1; {'m__alpha': 0.1, 'm__hidden_layer_sizes': (15,)} ×1 |
| equipe_com_historico | reg_logistica_q3 | {'m__C': 0.1} ×4; {'m__C': 0.01} ×1 |
| equipe_nova | gradient_boosting_q3 | {'m__learning_rate': 0.05, 'm__max_depth': 2, 'm__max_iter': 100} ×5 |
| equipe_nova | mlp_curva_q3 | {'m__alpha': 0.1, 'm__hidden_layer_sizes': (5,)} ×5 |
| equipe_nova | mlp_q3 | {'m__alpha': 0.1, 'm__hidden_layer_sizes': (15,)} ×2; {'m__alpha': 0.1, 'm__hidden_layer_sizes': (10,)} ×1; {'m__alpha': 0.001, 'm__hidden_layer_sizes': (5,)} ×1; {'m__alpha': 0.1, 'm__hidden_layer_sizes': (5,)} ×1 |
| equipe_nova | reg_logistica_q3 | {'m__C': 0.1} ×5 |

## 7. Limitações

- `Issue_Link` guarda só o estado final; 1,3% das ligações de bloqueio não têm registro no `Change_Log` e não contam. Ligações criadas e removidas antes do fim da coleta não entram.
- `trocas_responsavel_rel` conta toda linha de `assignee` do `Change_Log`, inclusive a primeira atribuição e trocas de ida e volta; não distingue reatribuição de atribuição inicial.
- `historico_cumprimento` usa a mesma janela do Monte Carlo e da velocidade (até 3 Sprints anteriores, inclusive as que saem da base pelos filtros), e por isso compartilha informação com `compromisso_vs_velocidade`.
- Os valores-p da triagem não foram corrigidos para múltiplas comparações (4 variáveis × 3 k); o critério de dois k com erros agrupados foi declarado antes de rodar e é a proteção adotada.
