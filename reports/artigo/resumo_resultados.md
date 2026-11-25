# Resultados para a parcial (25/11)

> Gerado a partir de `reports/artigo/*.csv` por `src/artigo/resumo.py`. Os números das tabelas não foram digitados à mão.
> Todo o código desta etapa está em `src/artigo/`; para reproduzir, rode `scripts/rodar_artigo.sh`.
> As decisões de método estão em `artigo/base_decisoes_artigo.md` (seção "Atualização de 23/11").

## 1. O que foi rodado

- **Base:** reconstrução refeita com a correção do vazamento de story points (A5). A base principal passou de 1.166 para **1.159 Sprints** (33 projetos, 125 positivas, 10,8%). Saíram 7 Sprints, porque a cobertura de story points delas caiu abaixo de 70%. Nenhum rótulo de Sprint que permaneceu mudou. A base por contagem de itens continua com 2.027 Sprints.
- **Modelos (7):**
  - burndown ideal;
  - burndown calibrado (regressão logística sobre a folga);
  - Monte Carlo sobre as entregas diárias das até 3 Sprints anteriores;
  - regressão logística;
  - MLP;
  - Gradient Boosting;
  - MLP + curva (as variáveis tabulares mais 9 pontos da curva do burndown até k).
- **Treino:** sem rebalanceamento de classes. Parâmetros escolhidos por validação cruzada interna agrupada por projeto (log-loss). O corte de decisão de cada modelo é a proporção de positivos no treino.
- **Divisões:**
  - *Equipe nova:* `StratifiedGroupKFold` com 5 dobras por projeto. Todas as 1.159 Sprints são avaliadas.
  - *Equipe com histórico:* 5 cortes no tempo. O treino usa só Sprints encerradas antes de cada corte. O teste reúne as 580 Sprints mais recentes, com apenas 34 positivas, e por isso os intervalos são largos.
- **Intervalos:** reamostragem de projetos com reposição (2.000 sorteios). ▲ indica que o modelo é melhor que o burndown calibrado com intervalo que não inclui o zero; ▼ indica que é pior. Para o Brier, a diferença negativa é a melhor.

## 2. Cenário principal: equipe nova (SP, L = 0,8)

### k = 0,5 (metade da Sprint)

n = 1159 Sprints, 33 projetos, 125 positivas (prevalência 0.108, que é a PR-AUC de um modelo ao acaso).

| Modelo | ROC-AUC [IC 95%] | PR-AUC [IC 95%] | Brier | BSS [IC 95%] | Acur. bal. | F1 |
|---|---|---|---|---|---|---|
| Burndown ideal | 0.849 [0.796; 0.893] | 0.545 [0.370; 0.683] | — | — [—; —] | 0.679 | 0.459 |
| Burndown calibrado | 0.841 [0.788; 0.887] | 0.525 [0.360; 0.670] | 0.0714 | +0.258 [+0.134; +0.366] | 0.794 | 0.483 |
| Monte Carlo | 0.833 [0.757; 0.889] | 0.514 [0.326; 0.673] | 0.0777 | +0.192 [+0.012; +0.337] | 0.766 | 0.445 |
| Regressão logística | 0.839 [0.778; 0.882] | 0.503 [0.341; 0.644] | 0.0734 | +0.237 [+0.080; +0.345] | 0.790 | 0.456 |
| MLP | 0.796 [0.735; 0.856] | 0.469 [0.301; 0.631] | 0.0779 | +0.190 [-0.012; +0.307] | 0.743 | 0.384 |
| Gradient Boosting | 0.791 [0.724; 0.859] | 0.471 [0.316; 0.621] | 0.0757 | +0.214 [+0.089; +0.320] | 0.771 | 0.445 |
| MLP + curva | 0.819 [0.753; 0.874] | 0.467 [0.316; 0.613] | 0.0769 | +0.201 [+0.016; +0.314] | 0.764 | 0.436 |

### k = 0,3

n = 1159 Sprints, 33 projetos, 125 positivas (prevalência 0.108, que é a PR-AUC de um modelo ao acaso).

| Modelo | ROC-AUC [IC 95%] | PR-AUC [IC 95%] | Brier | BSS [IC 95%] | Acur. bal. | F1 |
|---|---|---|---|---|---|---|
| Burndown ideal | 0.772 [0.696; 0.833] | 0.428 [0.250; 0.581] | — | — [—; —] | 0.697 | 0.438 |
| Burndown calibrado | 0.759 [0.684; 0.825] | 0.398 [0.242; 0.550] | 0.0856 | +0.110 [-0.142; +0.238] | 0.695 | 0.309 |
| Monte Carlo | 0.785 [0.701; 0.842] | 0.389 [0.234; 0.517] | 0.0927 | +0.036 [-0.191; +0.168] | 0.721 | 0.379 |
| Regressão logística | 0.768 [0.685; 0.830] | 0.380 [0.233; 0.521] | 0.0837 | +0.130 [-0.032; +0.237] | 0.717 | 0.379 |
| MLP | 0.710 [0.624; 0.800] | 0.331 [0.192; 0.481] | 0.0876 | +0.089 [-0.072; +0.190] | 0.662 | 0.317 |
| Gradient Boosting | 0.710 [0.610; 0.816] | 0.355 [0.221; 0.495] | 0.0846 | +0.121 [+0.016; +0.210] | 0.693 | 0.374 |
| MLP + curva | 0.744 [0.652; 0.818] | 0.341 [0.216; 0.480] | 0.0877 | +0.089 [-0.074; +0.192] | 0.700 | 0.357 |

### k = 0,7

n = 1159 Sprints, 33 projetos, 125 positivas (prevalência 0.108, que é a PR-AUC de um modelo ao acaso).

| Modelo | ROC-AUC [IC 95%] | PR-AUC [IC 95%] | Brier | BSS [IC 95%] | Acur. bal. | F1 |
|---|---|---|---|---|---|---|
| Burndown ideal | 0.904 [0.865; 0.931] | 0.654 [0.458; 0.774] | — | — [—; —] | 0.674 | 0.492 |
| Burndown calibrado | 0.900 [0.859; 0.929] | 0.639 [0.448; 0.765] | 0.0673 | +0.301 [+0.187; +0.419] | 0.776 | 0.542 |
| Monte Carlo | 0.864 [0.790; 0.917] | 0.615 [0.397; 0.753] | 0.0644 | +0.330 [+0.142; +0.476] | 0.793 | 0.510 |
| Regressão logística | 0.896 [0.849; 0.926] | 0.619 [0.415; 0.751] | 0.0631 | +0.344 [+0.160; +0.456] | 0.806 | 0.471 |
| MLP | 0.873 [0.827; 0.909] | 0.595 [0.388; 0.740] | 0.0654 | +0.320 [+0.123; +0.451] | 0.793 | 0.454 |
| Gradient Boosting | 0.867 [0.821; 0.909] | 0.584 [0.418; 0.730] | 0.0660 | +0.314 [+0.168; +0.439] | 0.796 | 0.427 |
| MLP + curva | 0.889 [0.835; 0.928] | 0.570 [0.381; 0.718] | 0.0673 | +0.300 [+0.073; +0.433] | 0.803 | 0.480 |

### Diferença para o burndown calibrado: ROC-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.013 [-0.005; +0.026] | +0.008 [+0.003; +0.013] ▲ | +0.004 [+0.000; +0.007] ▲ |
| Monte Carlo | +0.026 [-0.022; +0.069] | -0.008 [-0.067; +0.034] | -0.036 [-0.088; +0.003] |
| Regressão logística | +0.010 [-0.022; +0.037] | -0.002 [-0.031; +0.020] | -0.003 [-0.019; +0.009] |
| MLP | -0.048 [-0.092; +0.006] | -0.045 [-0.085; -0.007] ▼ | -0.027 [-0.051; -0.008] ▼ |
| Gradient Boosting | -0.049 [-0.104; +0.035] | -0.050 [-0.077; -0.000] ▼ | -0.033 [-0.055; +0.001] |
| MLP + curva | -0.015 [-0.055; +0.031] | -0.022 [-0.057; +0.010] | -0.010 [-0.032; +0.011] |

### Diferença para o burndown calibrado: PR-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.030 [-0.003; +0.044] | +0.021 [-0.003; +0.033] | +0.015 [+0.001; +0.026] ▲ |
| Monte Carlo | -0.008 [-0.063; +0.038] | -0.011 [-0.076; +0.047] | -0.025 [-0.083; +0.034] |
| Regressão logística | -0.018 [-0.047; +0.017] | -0.021 [-0.046; +0.007] | -0.020 [-0.048; +0.008] |
| MLP | -0.066 [-0.099; -0.013] ▼ | -0.055 [-0.084; -0.024] ▼ | -0.044 [-0.074; -0.020] ▼ |
| Gradient Boosting | -0.043 [-0.097; +0.041] | -0.054 [-0.089; +0.005] | -0.055 [-0.104; +0.010] |
| MLP + curva | -0.056 [-0.089; -0.002] ▼ | -0.058 [-0.091; -0.019] ▼ | -0.070 [-0.113; -0.020] ▼ |

### Diferença para o burndown calibrado: Brier

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Monte Carlo | +0.007 [-0.003; +0.018] | +0.006 [+0.000; +0.013] ▼ | -0.003 [-0.010; +0.005] |
| Regressão logística | -0.002 [-0.008; +0.006] | +0.002 [-0.000; +0.005] | -0.004 [-0.013; +0.004] |
| MLP | +0.002 [-0.006; +0.012] | +0.007 [+0.002; +0.010] ▼ | -0.002 [-0.011; +0.007] |
| Gradient Boosting | -0.001 [-0.014; +0.016] | +0.004 [+0.000; +0.009] ▼ | -0.001 [-0.008; +0.004] |
| MLP + curva | +0.002 [-0.005; +0.012] | +0.005 [+0.001; +0.012] ▼ | +0.000 [-0.010; +0.011] |

Figura: `reports/artigo/figuras/fig_diferencas.png`. Calibração em k = 0,5: `reports/artigo/figuras/fig_calibracao.png`.

## 3. Cenário principal: equipe com histórico (5 cortes no tempo)

### k = 0,5

n = 580 Sprints, 24 projetos, 34 positivas (prevalência 0.059, que é a PR-AUC de um modelo ao acaso).

| Modelo | ROC-AUC [IC 95%] | PR-AUC [IC 95%] | Brier | BSS [IC 95%] | Acur. bal. | F1 |
|---|---|---|---|---|---|---|
| Burndown ideal | 0.815 [0.720; 0.869] | 0.360 [0.141; 0.509] | — | — [—; —] | 0.619 | 0.310 |
| Burndown calibrado | 0.811 [0.693; 0.865] | 0.368 [0.134; 0.522] | 0.0464 | +0.159 [-0.130; +0.252] | 0.758 | 0.382 |
| Monte Carlo | 0.830 [0.691; 0.902] | 0.353 [0.131; 0.488] | 0.0527 | +0.045 [-0.269; +0.171] | 0.776 | 0.368 |
| Regressão logística | 0.823 [0.696; 0.880] | 0.364 [0.142; 0.537] | 0.0465 | +0.158 [-0.146; +0.257] | 0.736 | 0.339 |
| MLP | 0.817 [0.696; 0.869] | 0.368 [0.137; 0.510] | 0.0475 | +0.140 [-0.217; +0.259] | 0.739 | 0.321 |
| Gradient Boosting | 0.831 [0.697; 0.889] | 0.344 [0.154; 0.507] | 0.0467 | +0.153 [-0.125; +0.244] | 0.751 | 0.356 |
| MLP + curva | 0.798 [0.658; 0.853] | 0.306 [0.095; 0.470] | 0.0511 | +0.074 [-0.432; +0.228] | 0.744 | 0.333 |

### Diferença para o burndown calibrado: ROC-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.006 [-0.016; +0.056] | +0.004 [-0.008; +0.029] | +0.006 [-0.001; +0.021] |
| Monte Carlo | +0.103 [+0.016; +0.296] ▲ | +0.019 [-0.065; +0.089] | -0.042 [-0.122; +0.051] |
| Regressão logística | +0.046 [-0.001; +0.116] | +0.012 [-0.021; +0.034] | +0.002 [-0.012; +0.020] |
| MLP | +0.049 [-0.020; +0.147] | +0.006 [-0.028; +0.030] | -0.013 [-0.050; +0.014] |
| Gradient Boosting | +0.043 [-0.033; +0.170] | +0.020 [-0.028; +0.059] | -0.010 [-0.042; +0.022] |
| MLP + curva | +0.028 [-0.049; +0.138] | -0.013 [-0.071; +0.016] | -0.008 [-0.044; +0.024] |

### Diferença para o burndown calibrado: PR-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | -0.007 [-0.019; +0.004] | -0.008 [-0.020; +0.013] | -0.013 [-0.024; +0.013] |
| Monte Carlo | +0.023 [-0.073; +0.102] | -0.015 [-0.094; +0.074] | -0.104 [-0.203; +0.066] |
| Regressão logística | -0.011 [-0.050; +0.029] | -0.004 [-0.035; +0.032] | -0.007 [-0.041; +0.059] |
| MLP | +0.017 [-0.013; +0.049] | +0.000 [-0.036; +0.024] | -0.016 [-0.049; +0.106] |
| Gradient Boosting | -0.012 [-0.061; +0.034] | -0.024 [-0.070; +0.060] | -0.064 [-0.111; +0.032] |
| MLP + curva | -0.060 [-0.101; +0.004] | -0.062 [-0.113; -0.003] ▼ | -0.115 [-0.191; +0.004] |

### Diferença para o burndown calibrado: Brier

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Monte Carlo | -0.001 [-0.015; +0.015] | +0.006 [-0.001; +0.016] | +0.002 [-0.002; +0.007] |
| Regressão logística | -0.011 [-0.018; -0.005] ▲ | +0.000 [-0.001; +0.001] | -0.001 [-0.007; +0.004] |
| MLP | -0.010 [-0.017; -0.005] ▲ | +0.001 [-0.002; +0.004] | -0.001 [-0.006; +0.003] |
| Gradient Boosting | -0.012 [-0.023; +0.000] | +0.000 [-0.002; +0.002] | +0.002 [-0.004; +0.007] |
| MLP + curva | -0.006 [-0.013; +0.003] | +0.005 [+0.001; +0.011] ▼ | +0.003 [-0.004; +0.011] |

## 4. Sensibilidade (equipe nova)

### L = 0,7: ROC-AUC e PR-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.008 [-0.013; +0.024] | +0.004 [-0.003; +0.010] | +0.003 [-0.001; +0.006] |
| Monte Carlo | +0.024 [-0.031; +0.074] | -0.020 [-0.073; +0.020] | -0.026 [-0.056; +0.005] |
| Regressão logística | +0.017 [-0.013; +0.039] | -0.012 [-0.048; +0.010] | -0.011 [-0.032; +0.004] |
| MLP | -0.001 [-0.046; +0.040] | -0.019 [-0.069; +0.011] | -0.016 [-0.045; +0.003] |
| Gradient Boosting | -0.007 [-0.038; +0.024] | -0.039 [-0.058; -0.013] ▼ | -0.027 [-0.039; -0.011] ▼ |
| MLP + curva | -0.001 [-0.038; +0.031] | -0.019 [-0.057; +0.007] | -0.017 [-0.045; +0.004] |

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.021 [+0.000; +0.034] ▲ | +0.019 [-0.001; +0.034] | +0.013 [-0.000; +0.025] |
| Monte Carlo | +0.013 [-0.055; +0.086] | -0.007 [-0.083; +0.063] | -0.008 [-0.052; +0.043] |
| Regressão logística | -0.009 [-0.044; +0.019] | -0.021 [-0.057; +0.011] | -0.033 [-0.073; +0.003] |
| MLP | -0.035 [-0.077; -0.000] ▼ | -0.022 [-0.076; +0.011] | -0.038 [-0.087; -0.007] ▼ |
| Gradient Boosting | -0.026 [-0.051; +0.003] | -0.054 [-0.083; -0.020] ▼ | -0.070 [-0.103; -0.026] ▼ |
| MLP + curva | -0.042 [-0.075; -0.012] ▼ | -0.025 [-0.074; +0.007] | -0.048 [-0.106; -0.010] ▼ |

### L = 0,6: ROC-AUC e PR-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.002 [-0.009; +0.015] | +0.002 [-0.002; +0.007] | +0.003 [-0.001; +0.007] |
| Monte Carlo | +0.031 [-0.019; +0.082] | -0.009 [-0.044; +0.017] | -0.007 [-0.033; +0.025] |
| Regressão logística | +0.029 [-0.008; +0.064] | +0.009 [-0.019; +0.030] | +0.007 [-0.010; +0.023] |
| MLP | -0.039 [-0.102; +0.049] | -0.039 [-0.085; +0.013] | -0.027 [-0.062; +0.011] |
| Gradient Boosting | -0.010 [-0.052; +0.046] | -0.018 [-0.038; +0.013] | -0.013 [-0.025; +0.006] |
| MLP + curva | -0.005 [-0.044; +0.053] | -0.020 [-0.035; +0.002] | -0.009 [-0.023; +0.008] |

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.004 [-0.008; +0.011] | +0.004 [-0.002; +0.009] | +0.002 [-0.002; +0.006] |
| Monte Carlo | +0.010 [-0.040; +0.059] | -0.009 [-0.053; +0.028] | -0.008 [-0.033; +0.027] |
| Regressão logística | +0.016 [-0.012; +0.045] | +0.004 [-0.024; +0.032] | -0.003 [-0.025; +0.020] |
| MLP | -0.078 [-0.144; +0.025] | -0.060 [-0.118; +0.015] | -0.047 [-0.100; +0.006] |
| Gradient Boosting | -0.022 [-0.063; +0.027] | -0.024 [-0.054; +0.015] | -0.039 [-0.070; -0.006] ▼ |
| MLP + curva | -0.049 [-0.104; +0.021] | -0.049 [-0.088; -0.007] ▼ | -0.043 [-0.072; -0.014] ▼ |

### Unidade = itens (2.027 Sprints, 35 projetos): ROC-AUC e PR-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.006 [-0.001; +0.012] | +0.003 [-0.001; +0.007] | +0.003 [-0.001; +0.006] |
| Monte Carlo | +0.022 [-0.015; +0.062] | +0.003 [-0.024; +0.033] | +0.008 [-0.014; +0.032] |
| Regressão logística | +0.026 [+0.003; +0.051] ▲ | +0.018 [+0.003; +0.034] ▲ | +0.015 [+0.002; +0.033] ▲ |
| MLP | +0.023 [-0.012; +0.057] | +0.018 [-0.006; +0.042] | +0.016 [-0.004; +0.041] |
| Gradient Boosting | +0.018 [-0.009; +0.051] | +0.011 [-0.009; +0.034] | +0.009 [-0.009; +0.029] |
| MLP + curva | +0.008 [-0.022; +0.044] | +0.006 [-0.017; +0.030] | +0.011 [-0.007; +0.035] |

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.003 [-0.006; +0.009] | -0.000 [-0.007; +0.006] | -0.001 [-0.005; +0.002] |
| Monte Carlo | -0.062 [-0.094; -0.027] ▼ | -0.024 [-0.053; +0.011] | -0.008 [-0.034; +0.018] |
| Regressão logística | +0.036 [+0.005; +0.066] ▲ | +0.027 [+0.001; +0.056] ▲ | +0.008 [-0.010; +0.030] |
| MLP | +0.023 [-0.014; +0.055] | +0.025 [-0.002; +0.056] | +0.015 [-0.004; +0.035] |
| Gradient Boosting | +0.011 [-0.011; +0.040] | +0.006 [-0.012; +0.027] | -0.005 [-0.020; +0.009] |
| MLP + curva | +0.013 [-0.015; +0.044] | +0.012 [-0.018; +0.050] | -0.004 [-0.027; +0.020] |

### Sem o projeto DM: ROC-AUC e PR-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.018 [+0.002; +0.027] ▲ | +0.013 [+0.002; +0.018] ▲ | +0.007 [+0.001; +0.012] ▲ |
| Monte Carlo | +0.013 [-0.035; +0.049] | -0.015 [-0.081; +0.026] | -0.040 [-0.089; +0.002] |
| Regressão logística | -0.012 [-0.036; +0.010] | -0.021 [-0.059; +0.003] | -0.014 [-0.037; +0.002] |
| MLP | -0.062 [-0.089; -0.018] ▼ | -0.046 [-0.091; -0.014] ▼ | -0.035 [-0.076; -0.010] ▼ |
| Gradient Boosting | -0.034 [-0.056; -0.008] ▼ | -0.037 [-0.075; -0.007] ▼ | -0.025 [-0.049; -0.007] ▼ |
| MLP + curva | -0.043 [-0.065; -0.022] ▼ | -0.038 [-0.090; -0.006] ▼ | -0.030 [-0.068; -0.006] ▼ |

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.015 [+0.002; +0.023] ▲ | +0.017 [-0.000; +0.030] | +0.015 [+0.001; +0.026] ▲ |
| Monte Carlo | -0.023 [-0.078; +0.027] | -0.013 [-0.075; +0.046] | -0.027 [-0.081; +0.029] |
| Regressão logística | -0.028 [-0.048; +0.001] | -0.030 [-0.062; -0.003] ▼ | -0.033 [-0.063; -0.008] ▼ |
| MLP | -0.071 [-0.102; -0.022] ▼ | -0.073 [-0.116; -0.029] ▼ | -0.077 [-0.119; -0.036] ▼ |
| Gradient Boosting | -0.060 [-0.086; -0.018] ▼ | -0.082 [-0.107; -0.045] ▼ | -0.059 [-0.088; -0.037] ▼ |
| MLP + curva | -0.089 [-0.118; -0.043] ▼ | -0.080 [-0.128; -0.026] ▼ | -0.098 [-0.161; -0.043] ▼ |

## 5. Por projeto (k = 0,5, equipe nova, projetos com ≥ 10 Sprints positivas): ROC-AUC

| Projeto | Sprints | Positivas | Burndown ideal | Burndown calibrado | Monte Carlo | Regressão logística | MLP | Gradient Boosting | MLP + curva |
|---|---|---|---|---|---|---|---|---|---|
| MULE | 124 | 33 | 0.739 | 0.739 | 0.737 | 0.732 | 0.715 | 0.688 | 0.719 |
| NEXUS | 37 | 20 | 0.851 | 0.851 | 0.862 | 0.841 | 0.853 | 0.809 | 0.832 |
| TIDOC | 49 | 11 | 0.870 | 0.870 | 0.666 | 0.766 | 0.742 | 0.813 | 0.749 |
| TISTUD | 98 | 12 | 0.907 | 0.907 | 0.912 | 0.929 | 0.882 | 0.923 | 0.871 |
| XD | 55 | 14 | 0.810 | 0.810 | 0.826 | 0.812 | 0.834 | 0.854 | 0.855 |

## 6. Análise suplementar: grade estendida

Na grade declarada, MLP, Gradient Boosting e regressão logística escolheram a configuração mais regularizada disponível (MLP com alpha = 0,1 em todas as dobras; Gradient Boosting com profundidade 2 e taxa 0,05 em todas). Para afastar a objeção "o empate vem do limite da grade", os modelos aprendidos foram rodados de novo com uma grade estendida, com mais regularização e modelos menores. A grade estendida foi decidida **depois** de ver a 1ª rodada; por isso ela é suplementar e deve aparecer assim no artigo.

Com a grade estendida, o MLP passa a escolher alpha = 1,0, um valor interno da grade, e o Gradient Boosting passa a usar árvores de profundidade 1 ou 2.

### Equipe nova: ROC-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.013 [-0.005; +0.026] | +0.008 [+0.003; +0.013] ▲ | +0.004 [+0.000; +0.007] ▲ |
| Regressão logística | +0.010 [-0.022; +0.037] | -0.002 [-0.031; +0.020] | -0.003 [-0.019; +0.009] |
| MLP | +0.007 [-0.035; +0.056] | -0.008 [-0.045; +0.020] | -0.007 [-0.024; +0.008] |
| Gradient Boosting | -0.041 [-0.086; +0.030] | -0.030 [-0.054; +0.012] | -0.016 [-0.031; +0.003] |
| MLP + curva | -0.010 [-0.050; +0.033] | -0.017 [-0.057; +0.011] | -0.008 [-0.029; +0.008] |

### Equipe nova: PR-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.030 [-0.003; +0.044] | +0.021 [-0.003; +0.033] | +0.015 [+0.001; +0.026] ▲ |
| Regressão logística | -0.018 [-0.047; +0.017] | -0.021 [-0.046; +0.007] | -0.020 [-0.048; +0.008] |
| MLP | -0.033 [-0.060; -0.003] ▼ | -0.022 [-0.047; -0.003] ▼ | -0.027 [-0.052; -0.008] ▼ |
| Gradient Boosting | -0.042 [-0.083; +0.028] | -0.058 [-0.090; -0.002] ▼ | -0.050 [-0.090; +0.005] |
| MLP + curva | -0.052 [-0.078; -0.011] ▼ | -0.042 [-0.067; -0.015] ▼ | -0.051 [-0.086; -0.014] ▼ |

### Equipe com histórico: ROC-AUC

| Modelo | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---|---|---|
| Burndown ideal | +0.006 [-0.016; +0.056] | +0.004 [-0.008; +0.029] | +0.006 [-0.001; +0.021] |
| Regressão logística | +0.046 [-0.001; +0.116] | +0.012 [-0.021; +0.034] | +0.002 [-0.012; +0.020] |
| MLP | +0.041 [-0.029; +0.119] | -0.004 [-0.055; +0.019] | -0.015 [-0.046; -0.001] ▼ |
| Gradient Boosting | +0.042 [-0.025; +0.156] | +0.015 [-0.044; +0.047] | -0.018 [-0.061; +0.011] |
| MLP + curva | +0.018 [-0.057; +0.119] | +0.007 [-0.050; +0.068] | +0.000 [-0.035; +0.050] |

## 7. Leitura dos resultados frente às hipóteses

**H1. A regressão logística empata com o burndown calibrado.** Confirmada para ordenar as Sprints. Em todos os k e nas duas divisões, a diferença de ROC-AUC e de PR-AUC tem intervalo que inclui o zero. No Brier também há empate, com uma exceção: em k = 0,3 no cenário com histórico, a regressão logística é mais bem calibrada que o burndown calibrado (−0,011 [−0,018; −0,005]).

**H2. Os modelos complexos não superam as regras.**
- *Confirmada no cenário principal.* Nenhum modelo aprendido supera o burndown em ROC-AUC ou PR-AUC, em nenhum k e em nenhuma divisão. A única vantagem dos modelos aprendidos aparece no Brier, em k = 0,3 com histórico (regressão logística e MLP). Na equipe nova, o MLP fica abaixo do burndown em ROC-AUC (k = 0,5 e 0,7) e em PR-AUC (todos os k). O MLP + curva fica abaixo em PR-AUC nos três k. O Gradient Boosting fica abaixo em k = 0,5, no limite do intervalo.
- *A curva inteira ajuda pouco.* Entregar ao MLP a trajetória do burndown sobe a ROC-AUC do MLP (de 0,796 para 0,819 em k = 0,5), sem chegar ao burndown. A PR-AUC fica no mesmo nível do MLP comum, ou seja, abaixo do burndown.
- *Com mais regularização (grade estendida),* o MLP deixa de ser pior em ROC-AUC e passa a empatar com o burndown, mas segue pior em PR-AUC. Quanto mais regularizado, mais o modelo se aproxima do burndown, sem superá-lo.

**H3. A vantagem das regras é maior para equipe nova do que para equipe com histórico.** Confirmada na direção, mas com pouca força estatística (só 34 positivas no teste temporal):
- Com histórico, nenhum modelo aprendido fica significativamente abaixo do burndown em ROC-AUC. Em k = 0,3, os modelos aprendidos ficam até 0,05 acima, mas com intervalos que incluem o zero.
- Também em k = 0,3, a regressão logística e o MLP têm Brier significativamente melhor que o burndown calibrado. Isso indica que, cedo na Sprint, a folga sozinha calibra mal.
- O Monte Carlo é o único que supera o burndown com intervalo fora do zero: ROC-AUC +0,103 em k = 0,3.

**H4 (pergunta 3).** Pendente: depende das variáveis novas, que exigem o dump (ver `artigo/especificacao_q3_claude_code.md`).

**Sensibilidade.**
- *L = 0,7 e L = 0,6:* o padrão se mantém. Nenhum modelo supera o burndown; os modelos não lineares ficam abaixo em várias combinações.
- *Sem o DM:* os modelos não lineares ficam significativamente abaixo do burndown em todos os k.
- *Base por contagem de itens:* é a **exceção**. A regressão logística supera o burndown com intervalo fora do zero: ROC-AUC de +0,015 a +0,026 nos três k, e PR-AUC de +0,027 a +0,036 em k = 0,3 e 0,5. Os demais modelos aprendidos ficam ligeiramente acima, sem significância. Com itens, que é uma medida mais grosseira do trabalho, as variáveis além do burndown acrescentam um pouco. A diferença é pequena e precisa ser relatada.

**Por projeto.** Nenhum modelo domina. O burndown é o melhor em MULE e TIDOC. Nos outros três há algum modelo acima dele: em NEXUS por margem mínima (Monte Carlo 0,862 contra 0,851); em TISTUD e XD por 0,02 a 0,05 (regressão logística e Gradient Boosting). Esses valores não têm intervalo de confiança, porque há poucas Sprints por projeto.

## 8. Cuidados para o texto

1. **Burndown ideal × burndown calibrado na ROC-AUC.** Dentro de um mesmo k, os dois ordenam as Sprints de forma idêntica. A pequena diferença a favor do ideal (+0,004 a +0,013) vem de o calibrado ser ajustado separadamente em cada dobra: ao juntar as predições das dobras, a ordenação se altera um pouco. Como o ideal fica sempre igual ou acima do calibrado, compará-los com o ideal só reforça a conclusão.
2. **A acurácia balanceada do burndown ideal** é a mais baixa em k = 0,5 e 0,7. Isso acontece porque o corte fixo (folga ≥ 0) é exigente demais para equipes que entregam, em média, só 38% do compromisso. É o mesmo achado do trabalho original (o corte aprendido fica em cerca de 31% concluído na metade da Sprint).
3. **O Monte Carlo** é a regra mais bem calibrada em média (probabilidade média de 0,105 contra prevalência de 0,108 em k = 0,5), mas tende a superestimar as probabilidades altas (ver a figura de calibração).
4. **Equipe com histórico:** com só 34 positivas, os intervalos são largos. Trate esse cenário como evidência de direção, não como prova.
5. **O modelo sequencial:** a decisão entre MLP + curva e GRU ainda está em aberto (ver a mensagem de 23/11). Rodei o MLP + curva, que foi a opção recomendada.
