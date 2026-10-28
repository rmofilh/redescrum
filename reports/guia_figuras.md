# Guia de leitura das figuras

Este guia é para quem vai **apresentar** os resultados. Cada figura segue o mesmo roteiro:
1. o que está desenhado;
2. como ler, com um exemplo concreto;
3. a mensagem em uma frase;
4. uma pergunta provável da banca, com a resposta.

Todos os números vêm dos arquivos do projeto. As fontes estão indicadas em cada seção; os caminhos partem de `reports/`.

**Cenário principal** (decisões D1 e D2 em `decisoes.md`):

| Item | Valor |
|---|---|
| Unidade | story points (SP) |
| Rótulo | "cumpriu" quando a Sprint concluiu ≥ 80% dos SP comprometidos (L = 0,8) |
| Base | 1.166 Sprints de 33 projetos do TAWOS |
| Positivos | 127 "cumpriu" (10,9%) e 1.039 "não cumpriu" |

O glossário está no fim.

**Exemplo que atravessa todo o guia:** a Sprint *SDK Qin 4* do projeto MULE (`sprint_id` 4351).

| Fração do tempo (k) | SP comprometidos concluídos |
|---|---:|
| 0,3 | 16% |
| 0,5 | 16% |
| 0,7 | 29% |
| fim | 74% |

Como 74% < 80%, o rótulo é "não cumpriu". Fonte: `resultados/exp4_predicoes.csv` e `data/interim/amostra_poc.csv`.

---

## 0. O burndown de uma Sprint real — `figures/burndown_amostra/MULE_4351.png`

Use esta figura no slide do problema, para mostrar o que é um burndown.

**O que está desenhado**

| Elemento | Significado |
|---|---|
| Eixo x | dias desde o início da Sprint (0 a 15) |
| Eixo y | story points que ainda faltam entregar |
| Linha tracejada cinza ("ideal") | o burndown ideal: o trabalho cai em ritmo constante, de 100 SP no dia 0 a zero no último dia |
| Linha azul | o que falta do escopo **comprometido** no início |
| Linha laranja | o que falta incluindo os itens **adicionados** durante a Sprint (aparece quando difere da azul, como entre os dias 11 e 12) |
| Linhas verticais cinza | os momentos k = 0,3, 0,5 e 0,7 (dias 4,5, 7,5 e 10,5) |

**Como ler**
1. Procure o dia 7,5, a metade da Sprint.
2. A linha ideal está em 50 SP.
3. A linha azul está em 84 SP: só 16% foi concluído.
4. A equipe está bem acima do ideal, ou seja, atrasada.
5. No fim, a Sprint concluiu 74% dos SP comprometidos (título da figura), abaixo dos 80%, então o rótulo é "não cumpriu".

**Mensagem:** o burndown mostra, a cada momento, se a equipe está à frente ou atrás do ritmo necessário. A pergunta do trabalho é se dá para prever o resultado final olhando só até a metade.

**Pergunta provável:** "Por que a linha é em degraus?"
**Resposta:** porque um item só conta como feito quando muda para um status de conclusão. Os SP caem de uma vez, no momento em que o item fecha.

---

## (a) Retas aprendidas × diagonal do burndown ideal — `figures/redes/exp2_fronteiras_2entradas.png`

**O que está desenhado**

| Elemento | Significado |
|---|---|
| Eixo x | `pct_tempo`, a fração do tempo da Sprint que já passou. Só existem 3 valores (0,3, 0,5 e 0,7); os pontos foram espalhados um pouco na horizontal só para não se sobreporem |
| Eixo y | `pct_pontos_concluidos`, a fração dos SP comprometidos já concluída nesse momento |
| Pontos | cada um é uma Sprint num momento k (1.166 × 3 = 3.498 pontos). **Laranja** = cumpriu; **cinza** = não cumpriu |
| Diagonal tracejada preta | o baseline **B1**, burndown ideal: "concluído = tempo decorrido". Acima dela, B1 diz "vai cumprir" |
| Retas verdes | as fronteiras do **Adaline** nas 5 sementes. Estão quase sobrepostas: as 5 chegaram à mesma reta |
| Retas azuis | as fronteiras do **Perceptron** nas 5 sementes, espalhadas. Duas delas ficam abaixo do gráfico (ver b) |

**A reta do Adaline** (pesos de `resultados/exp1_perceptron_adaline_2entradas.csv`; o intervalo cobre as 5 sementes):

```
u = w0 + w1·pct_tempo + w2·pct_concluido,
w0 ≈ −0,12 a −0,14,  w1 ≈ −1,15,  w2 ≈ 2,24
```

A fronteira é u = 0. Isolando o concluído:

```
pct_concluido* = (0,13 + 1,15 · pct_tempo) / 2,24
```

| Fração do tempo | Fronteira do Adaline | Diagonal do B1 |
|---|---:|---:|
| 0,3 | 21% | 30% |
| 0,5 | **31%** (0,308 a 0,318 nas 5 sementes) | **50%** |
| 0,7 | 42% | 70% |

A inclinação da reta do Adaline é 0,51, cerca de metade da inclinação da diagonal.

**Como ler, passo a passo**
1. Fique na coluna k = 0,5.
2. O ponto da MULE 4351 está em (0,5; 0,16): abaixo da diagonal e abaixo da reta verde. As duas regras dão alerta, e acertam, porque a Sprint não cumpriu.
3. Agora imagine uma Sprint com 40% concluído na metade do tempo. Ela está **abaixo** da diagonal, então B1 dá alerta. Mas está **acima** da reta verde (31%), então o Adaline diz "vai cumprir".
4. Toda a faixa entre 31% e 50% é onde as duas regras discordam.

**Por que o Adaline corta k = 0,5 em ≈ 31%, e não em 50%?**

- **O que os dados mostram.** Calculamos a curva média de conclusão das Sprints de cada classe (figura `figures/curva_media_concluido.png`; números em `resultados/curva_media_concluido.csv`). Em t = 0,5:

  | Classe | Média | Mediana | 1º quartil |
  |---|---:|---:|---:|
  | Cumpriu | 46,6% | 42,9% | 30,4% |
  | Não cumpriu | 15,7% | 12,5% | — |

- **A explicação que os dados sustentam.** A reta passa **entre as duas nuvens**, mais ou menos no meio de 15,7% e 46,6%, e não sobre a diagonal. O Adaline minimiza o erro quadrático com as duas classes pesando o mesmo (ponderação "balanced"). Ele procura a reta que melhor separa *estas* Sprints, não a reta que o Scrum Guide considera ideal. Com o corte em 31%, em k = 0,5:

  | Regra | Sprints que cumpriram, acima do corte | Sprints que não cumpriram, abaixo do corte |
  |---|---:|---:|
  | Adaline (31%) | 74,8% | 84,4% |
  | B1, diagonal (50%) | só 40,2% | 95,9% |

  Fonte: `data/processed/base_modelagem.csv`.

- **Hipótese que verificamos e NÃO se confirmou.** A ideia era que "o fim da Sprint concentra entregas", ou seja, que o burndown das equipes que cumprem seria convexo. Os dados não mostram isso.
  - A curva média das Sprints que cumprem é **quase linear**: 46,6% em t = 0,5, contra 50% na diagonal.
  - Ela fica um pouco *acima* da diagonal até ~35% do tempo e um pouco abaixo depois. Chega a 91% no fim.
  - Há um pequeno salto nos últimos 5% do tempo (+7,8 pontos percentuais), mas pequeno demais para explicar o corte em 31%.
  - Portanto, não apresente essa ideia como fato.

**O que isso significa para um Scrum Master**

| Situação na metade da Sprint | Leitura |
|---|---|
| Menos de ~31% dos SP concluídos | sinal forte de risco: 84% das Sprints que não cumpriram estavam aí |
| Entre 31% e 50% | zona cinzenta: a maioria das Sprints que cumprem passa por ela (só 40% estão acima da diagonal); a diagonal exige demais |
| Acima de 50% | quase sempre ok |

- A reta é uma regra prática aprendida dos dados, mas vem de projetos *open source*, em que só 10,9% das Sprints cumprem. Em outra equipe, a reta precisa ser reaprendida.

**Mensagem:** o Adaline aprendeu que, na metade da Sprint, ~31% concluído já separa bem quem cumpre de quem não cumpre. A diagonal do burndown ideal (50%) é exigente demais para estes dados.

**Pergunta provável:** "Se a reta é tão diferente da diagonal, por que a AUC do Adaline (0,85) é igual à do B1 (0,85)?"
**Resposta:**
- A AUC mede só a **ordem** das Sprints, do mais provável ao menos provável de cumprir, e não o ponto de corte.
- Dentro de um mesmo k, as duas regras ordenam as Sprints praticamente pelo mesmo critério: o quanto já foi concluído. A diferença entre elas é **onde** cortam (31% contra 50%).
- Por isso a AUC empata, mas a acurácia balanceada, que depende do corte, não: 0,78 contra 0,68 em k = 0,5.

---

## (b) Curvas de treinamento — `figures/redes/exp1_curvas_treinamento.png`

Experimento 1: Perceptron e Adaline com 2 entradas (`pct_tempo` e `pct_concluido`), treinados com os 3.498 pontos e 5 sementes. Fonte: `resultados/exp1_perceptron_adaline_2entradas.csv`.

**O que está desenhado**

| Painel | Eixos e linhas |
|---|---|
| Esquerdo, Perceptron | x = época (1 a 100); y = número de amostras classificadas errado no fim da época. Uma cor por semente |
| Direito, Adaline | x = época; y = erro quadrático médio (EQM), em escala logarítmica, ponderado pelas classes, na fórmula do livro: ½(d − u)² |

**Como ler o Adaline**
1. As 5 curvas descem rápido nas primeiras 10 épocas (de ~0,40–0,47 para ~0,33).
2. Depois achatam.
3. O treino para quando o EQM muda menos que ε = 10⁻⁶ entre duas épocas. Isso aconteceu entre a 55ª e a 62ª época.
4. O EQM final é 0,3277 nas 5 sementes, e os pesos finais são praticamente iguais.

**Como ler o Perceptron**
1. Nenhuma curva chega a zero erros, o critério de parada do livro. Todas param no limite de 100 épocas.
2. As curvas oscilam sem tendência de queda. Exemplo: a semente 1 fica entre ~1.600 e ~2.500 erros.
3. A linha rosa reta, no alto, em **3.117 erros**, é a semente 5. A semente 2 (laranja) fica escondida embaixo dela, no mesmo valor.
4. Esse valor é exatamente o número de pontos "não cumpriu" (1.039 × 3). A reta final dessas sementes classifica **tudo como "cumpriu"**: a fronteira fica abaixo de 0% de concluído, por isso não aparece na figura (a).
5. A acurácia balanceada dessas duas sementes no treino é 0,5, a mesma de um palpite constante.

**Por que o Perceptron não converge**
- O teorema de convergência do Perceptron (Silva, Spatti & Flauzino, cap. 3) garante parada só se as classes forem **linearmente separáveis**.
- Aqui não são: na figura (a), pontos laranja e cinza se misturam em toda a faixa vertical. Nenhuma reta deixa zero erros.
- A regra de Hebb corrige os pesos a cada amostra errada (com η = 1), então a reta "pula" de época em época e nunca se acomoda.
- Os pesos finais são os da última época, por acaso. Em k = 0,5 as fronteiras das 5 sementes cortam em 0,05, −0,48, 0,66, 0,34 e −0,19.

**Por que o Adaline converge**
- Ele não persegue zero erros: minimiza o EQM da saída linear u, antes do degrau.
- A superfície do EQM é uma "tigela" com um único fundo. Com η pequeno (10⁻³), o gradiente desce até esse fundo mesmo com classes misturadas.
- Por isso as 5 sementes chegam à mesma reta.

**Mensagem:** com classes sobrepostas, o Perceptron oscila indefinidamente. O Adaline converge sempre para a mesma reta, a de menor erro quadrático. É o comportamento previsto nos capítulos 3 e 4 do livro.

**Pergunta provável:** "Por que duas sementes do Perceptron caíram em 'tudo é cumpriu'?"
**Resposta:**
- O treino usa pesos que equilibram as classes: cada erro num ponto "cumpriu" pesa ~8× mais que um erro num ponto "não cumpriu".
- Com esses pesos, "errar todos os negativos" e "errar todos os positivos" custam o mesmo, e o Perceptron pode terminar numa dessas retas triviais.
- Sem convergência, onde ele para depende da ordem das amostras, ou seja, da semente.

---

## (c) Curva de perda do PMC — `figures/redes/exp3_pmc_loss_curve.png`

Experimento 3: PMC com todas as 6 variáveis, 1 camada oculta logística, retropropagação com momentum.
- Topologia escolhida por validação cruzada por projeto (`resultados/exp3_pmc_topologias_cv.csv`), pela AUC fora da dobra:

  | Neurônios ocultos | AUC fora da dobra |
  |---|---:|
  | 5 | 0,789 |
  | **10 (escolhida)** | **0,798** |
  | 15 | 0,792 |

- 5 treinamentos com a base completa (`resultados/exp3_pmc_treinamentos.csv`).

**O que está desenhado**
- Eixo x: época (até 2.000).
- Eixo y: a perda que o `MLPClassifier` minimiza, a **entropia cruzada** (o livro usa o EQM).
- Uma cor por semente.

**Como ler**
1. A perda cai de ~0,70 para ~0,46 nas primeiras ~20 épocas.
2. Depois desce devagar até **0,391–0,406** na época 2.000.
3. Nenhum treinamento atingiu o critério de parada (melhora < 10⁻⁵ por 20 épocas seguidas). Todos pararam no limite de 2.000 épocas.

**O sobreajuste**

| Medida | AUC |
|---|---|
| PMC, no treino (3 momentos juntos) | 0,895 a 0,903 |
| PMC, fora da dobra (projetos nunca vistos), k = 0,3 / 0,5 / 0,7 | 0,68 / 0,78 / 0,86 |
| Adaline, fora da dobra, k = 0,3 / 0,5 / 0,7 | 0,79 / 0,85 / 0,90 |

- O Adaline é linear e mais simples, e mesmo assim generaliza melhor.
- Dentro das dobras, a validação escolheu a menor rede (5 neurônios) em 4 das 5 vezes (`resultados/exp4_topologias_por_dobra.csv`).
- Leitura: a capacidade extra do PMC aprende particularidades dos projetos do treino, que não valem para projetos novos.
- A perda continuar caindo no treino não significa que o modelo esteja melhorando para dados novos.

**Mensagem:** o PMC aprende bem o treino, mas não generaliza melhor que o Adaline para projetos que nunca viu. Mais neurônios não compensam a falta de variáveis com sinal novo.

**Pergunta provável:** "Por que não treinar mais épocas, ou usar outra topologia?"
**Resposta:**
- Mais épocas reduziriam a perda no treino e aumentariam o sobreajuste.
- As topologias 5, 10 e 15 ficaram a menos de 0,01 de AUC uma da outra.
- O limite está nas variáveis: quase todo o sinal está no próprio burndown, que um modelo linear já captura (a ablação da viabilidade mostra isso).
- Também ajustamos o PMC uma vez depois de ver o primeiro resultado (taxa de aprendizagem e regularização). Não ajustamos mais para não otimizar no conjunto de teste.

---

## (d) Métrica × k — `figures/redes/exp4_metrica_vs_k_principal.png`

As variações de robustez estão em `exp4_metrica_vs_k_robustez.png` (contagem de itens) e `exp4_metrica_vs_k_sem_DM.png` (sem o projeto DM).

**O que está desenhado**

| Elemento | Significado |
|---|---|
| Painéis | três métricas: AUC, acurácia balanceada e F1 |
| Eixo x | o momento k (0,3, 0,5, 0,7) |
| Eixo y | o valor da métrica (0 a 1) |
| Linhas | um modelo cada. Tracejadas = baselines: B0 em azul, B1 em laranja. Contínuas = redes: Perceptron em verde, Adaline em amarelo, PMC em rosa |
| B0 | não aparece no painel da AUC: dá a mesma resposta para todos, então a AUC não se define |

Todos os valores são **fora da dobra**: cada Sprint foi prevista por um modelo que não viu nenhuma Sprint do seu projeto (`resultados/exp4_avaliacao.csv`).

**Como ler, cenário principal**

| AUC | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---:|---:|---:|
| B1 | 0,77 | 0,85 | 0,90 |
| Perceptron | 0,73 | 0,71 | 0,60 |
| **Adaline** | **0,79** | **0,85** | **0,90** |
| PMC | 0,68 | 0,78 | 0,86 |

| Acurácia balanceada | k = 0,3 | k = 0,5 | k = 0,7 |
|---|---:|---:|---:|
| B0 | 0,50 | 0,50 | 0,50 |
| B1 | 0,70 | 0,68 | 0,68 |
| Perceptron | 0,68 | 0,66 | 0,55 |
| **Adaline** | **0,73** | **0,78** | **0,82** |
| PMC | 0,63 | 0,72 | 0,76 |

1. **Quanto mais tarde, mais fácil prever.** Para B1, Adaline e PMC as curvas sobem com k. É o resultado central do estudo.
2. **Em AUC, Adaline e B1 andam juntos** (as linhas amarela e laranja se sobrepõem).
3. **Em acurácia balanceada, o Adaline se afasta do B1** e a vantagem cresce com k (de +0,03 para +0,14). O B1 fica parado em ~0,68, porque seu corte (a diagonal) é fixo e exigente demais.
4. **Em F1, Adaline e B1 empatam** (0,46 em k = 0,5).
5. **O Perceptron piora com k.** Sua reta final é arbitrária (ver b).

**Robustez**

| Cenário | AUC em k = 0,5 | Conclusão |
|---|---|---|
| Itens, L = 0,8 (2.027 Sprints, 35 projetos, 13,0% cumpriu) | Adaline 0,88, B1 0,87, PMC 0,86, Perceptron 0,83 | mesma ordem e mesma conclusão |
| Sem DM (929 Sprints, 32 projetos, 13,5% cumpriu) | B1 0,84, Adaline 0,83 | empate; o DM, com 1% de positivos, não distorce o resultado |

**Mensagem:** todas as redes ficam mais precisas à medida que a Sprint avança. O Adaline é a melhor das três e acerta mais Sprints de ambas as classes que o burndown ideal (acurácia balanceada), mas não ordena as Sprints melhor do que ele (AUC).

**Pergunta provável:** "O B0 tem 89% de acurácia. Por que ele não é o melhor?"
**Resposta:**
- O B0 responde "não cumpriu" para todas as Sprints. Como 89,1% delas não cumprem, acerta 89,1% sem detectar nenhuma Sprint que cumpre.
- Por isso usamos acurácia balanceada (B0 = 0,50) e AUC, que não se deixam enganar pelo desequilíbrio entre as classes.

---

## (e) Matrizes de confusão em k = 0,5 — `figures/redes/exp4_matrizes_confusao_k05.png`

**O que está desenhado**
- Duas matrizes 2 × 2, B1 à esquerda e Adaline à direita, com as 1.166 Sprints na metade do tempo.
- Linhas: o que aconteceu de fato. Colunas: o que o modelo previu.
- Fundo azul = acerto; cinza = erro.
- A "classe positiva" é **cumpriu**:

| Célula | Situação | Para o Scrum Master |
|---|---|---|
| VN (verdadeiro negativo) | não cumpriu, previsto "não cumpre" | Sprint em risco, **com alerta**: acerto |
| FP (falso positivo) | não cumpriu, previsto "cumpre" | Sprint em risco que **passa sem alerta** (contorno laranja) |
| FN (falso negativo) | cumpriu, previsto "não cumpre" | **alarme falso** numa Sprint que ia bem |
| VP (verdadeiro positivo) | cumpriu, previsto "cumpre" | Sprint que cumpre, reconhecida: acerto |

**Como ler** (fonte: `resultados/exp4_avaliacao.csv`)

| | VN | FP | FN | VP | Alertas emitidos |
|---|---:|---:|---:|---:|---:|
| B1 | 996 | **43** | 76 | 51 | 1.072 (92% das Sprints) |
| Adaline | 843 | **196** | 31 | 96 | 874 (75% das Sprints) |

**A troca entre os erros**
- Das 127 Sprints que cumpriram, o Adaline reconhece **96** e o B1 só **51**. O Adaline gera muito menos alarmes falsos (31 contra 76).
- Em troca, das 1.039 Sprints em risco, o Adaline **deixa passar 196 sem alerta**; o B1 deixa passar 43.

**Qual erro é mais grave para o Scrum Master: o FP, a Sprint em risco sem alerta.**
- O alerta existe para dar tempo de agir: renegociar o escopo com o Product Owner, remover impedimentos, avisar os interessados.
- Uma Sprint em risco sem alerta é uma surpresa na Sprint Review, quando já não dá para fazer nada.
- Um alarme falso custa uma conversa a mais no Daily Scrum.
- Por esse critério, o B1 é **mais seguro** (43 contra 196).
- Mas o B1 dispara alerta em 92% das Sprints. Um alarme que toca quase sempre é ignorado pela equipe ("fadiga de alarme").

**A troca é definida pelo ponto de corte, não pelo modelo.** Como os dois têm a mesma AUC (0,85), fizemos um teste com as predições salvas (`resultados/exp4_predicoes.csv`):

| Teste | Resultado |
|---|---|
| Subir o corte do Adaline até ele deixar passar só 43 Sprints em risco | a matriz fica **exatamente igual** à do B1 (996 / 43 / 76 / 51) |
| Baixar o corte do B1 para "concluído ≥ tempo − 20 pontos percentuais" | 863 / 176 / 31 / 96, praticamente a matriz do Adaline |

Esses cortes foram escolhidos olhando o próprio conjunto de teste. Servem só para **ilustrar**, não como resultado.

**Mensagem:** Adaline e B1 enxergam as Sprints de forma muito parecida. A escolha entre "reconhecer mais Sprints que cumprem" e "deixar passar menos Sprints em risco" é uma decisão de gestão, tomada ao ajustar o ponto de corte.

**Pergunta provável:** "Então qual você recomendaria a um Scrum Master?"
**Resposta:**
- Se o custo de uma surpresa é alto, um corte mais conservador, como o do B1, que deixa passar só 43 Sprints em risco.
- Se a equipe já ignora alertas, o corte do Adaline, que dispara em 75% das Sprints em vez de 92%.
- Em ambos os casos, o ideal é escolher o corte com dados da própria equipe, numa validação separada, e não no conjunto de teste.

---

## Apoio: curva média de conclusão — `figures/curva_media_concluido.png`

Use-a para responder à pergunta da seção (a).

**O que está desenhado**

| Elemento | Significado |
|---|---|
| Eixo x | fração do tempo da Sprint |
| Eixo y | fração média dos SP comprometidos já concluída |
| Linha azul | Sprints que cumpriram (127) |
| Linha laranja | Sprints que não cumpriram (1.039) |
| Faixas claras | do 1º ao 3º quartil de cada classe |
| Tracejado cinza | o burndown ideal |
| Pontos marcados | t = 0,5: 47% para quem cumpriu e 16% para quem não cumpriu |

**Mensagem:** quem cumpre segue quase a diagonal; quem não cumpre anda a cerca de um terço desse ritmo. A reta do Adaline passa entre as duas.

---

## Glossário

- **k:** a fração do tempo da Sprint em que fazemos a previsão (0,3 = 30% do tempo decorrido). Só usamos o que aconteceu até esse momento, sem "espiar o futuro".
- **L:** o limiar do rótulo. A Sprint "cumpriu" se concluiu pelo menos L (aqui, 80%) do que foi comprometido no início.
- **B0, classe majoritária:** responde sempre a classe mais comum ("não cumpriu"). Mostra o mínimo que qualquer modelo precisa superar.
- **B1, burndown ideal:** responde "cumpre" se o percentual concluído for pelo menos o percentual de tempo decorrido (estar sobre ou acima da diagonal). É a regra que um Scrum Master aplicaria olhando o gráfico.
- **Matriz de confusão:** tabela 2 × 2 que cruza o que aconteceu com o que foi previsto: VN, FP, FN e VP (ver seção e).
- **Acurácia balanceada:** a média entre "% das Sprints que cumpriram, reconhecidas" e "% das Sprints que não cumpriram, reconhecidas". Dá o mesmo peso às duas classes; chutar sempre a mesma resposta dá 0,5.
- **F1:** resume o quanto o modelo acerta quando diz "cumpre" e quantas das que cumprem ele encontra (média harmônica de precisão e revocação). Vai de 0 a 1 e é baixo quando a classe positiva é rara.
- **AUC:** a probabilidade de o modelo dar uma nota maior a uma Sprint que cumpriu do que a uma que não cumpriu, sorteando uma de cada. 0,5 = sorte; 1 = perfeito. Não depende do ponto de corte.
- **GroupKFold (por projeto):** validação cruzada em 5 rodadas. Em cada uma, os projetos são divididos em grupos: o modelo treina com uns e é testado em outros, que nunca viu. Simula usar o modelo numa equipe nova e impede que ele "decore" um projeto.
- **Sobreajuste:** quando o modelo aprende detalhes do treino que não se repetem em dados novos. Fica muito bom no treino e pior no teste.
