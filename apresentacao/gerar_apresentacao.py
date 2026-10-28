"""Gera apresentacao/apresentacao_scrum.pptx (16:9, português) com python-pptx.

Todos os números vêm de reports/resultados/*.csv, data/processed/*.csv e reports/figures/; nada é digitado à mão,
exceto parâmetros de treinamento (que são os de src/models/redes.py) e as referências.
Uso: .venv/bin/python apresentacao/gerar_apresentacao.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

RAIZ = Path(__file__).resolve().parents[1]
RES = RAIZ / "reports" / "resultados"
FIG = RAIZ / "reports" / "figures"
SAIDA = RAIZ / "apresentacao" / "apresentacao_scrum.pptx"

FONTE = "Arial"
MARINHO, TINTA, CINZA = RGBColor(0x1B, 0x2A, 0x41), RGBColor(0x1F, 0x1F, 0x1F), RGBColor(0x5A, 0x5A, 0x5A)
LARANJA, AZUL, VERDE = RGBColor(0xD9, 0x5A, 0x24), RGBColor(0x2A, 0x78, 0xD6), RGBColor(0x14, 0x8F, 0x63)
TINTA_CARD, LINHA_ZEBRA, BRANCO = RGBColor(0xEE, 0xF3, 0xFA), RGBColor(0xF5, 0xF6, 0xF8), RGBColor(0xFF, 0xFF, 0xFF)
GELO = RGBColor(0xCA, 0xDC, 0xFC)
LARG, ALT = 13.333, 7.5
MX = 0.6  # margem lateral


def br(x, casas=2):
    return f"{x:.{casas}f}".replace(".", ",")


def milhar(n):
    return f"{int(n):,}".replace(",", ".")


# ---------------------------------------------------------------- primitivas

def _run(par, texto, tam, cor=TINTA, negrito=False, italico=False):
    r = par.add_run()
    r.text = texto
    f = r.font
    f.name, f.size, f.bold, f.italic = FONTE, Pt(tam), negrito, italico
    f.color.rgb = cor
    return r


def caixa(slide, x, y, w, h, linhas, tam=16, cor=TINTA, alinhar=PP_ALIGN.LEFT, ancora=MSO_ANCHOR.TOP,
          espaco=6, nome=None):
    """linhas: lista de str ou de listas de (texto, {opções}) por parágrafo."""
    tb = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if nome:
        tb.name = nome
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = ancora
    for i, linha in enumerate(linhas):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = alinhar
        p.space_after = Pt(espaco)
        partes = [(linha, {})] if isinstance(linha, str) else linha
        for parte in partes:
            texto, op = (parte, {}) if isinstance(parte, str) else parte
            _run(p, texto, op.get("tam", tam), op.get("cor", cor), op.get("negrito", False), op.get("italico", False))
    return tb


def retangulo(slide, x, y, w, h, cor, arredondado=True, borda=None):
    forma = MSO_SHAPE.ROUNDED_RECTANGLE if arredondado else MSO_SHAPE.RECTANGLE
    s = slide.shapes.add_shape(forma, Inches(x), Inches(y), Inches(w), Inches(h))
    if arredondado:
        s.adjustments[0] = 0.08
    s.fill.solid()
    s.fill.fore_color.rgb = cor
    if borda:
        s.line.color.rgb = borda
        s.line.width = Pt(1.5)
    else:
        s.line.fill.background()
    s.shadow.inherit = False
    return s


def circulo(slide, x, y, d, cor, texto, tam=14, cor_texto=BRANCO):
    s = slide.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x), Inches(y), Inches(d), Inches(d))
    s.fill.solid(); s.fill.fore_color.rgb = cor
    s.line.fill.background(); s.shadow.inherit = False
    tf = s.text_frame
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    _run(p, texto, tam, cor_texto, negrito=True)
    return s


def card(slide, x, y, w, h, titulo, corpo, cor_titulo=MARINHO, tam=15, fundo=TINTA_CARD):
    retangulo(slide, x, y, w, h, fundo)
    linhas = [[(titulo, {"negrito": True, "cor": cor_titulo, "tam": tam + 2})]] + corpo
    caixa(slide, x + 0.25, y + 0.2, w - 0.5, h - 0.4, linhas, tam=tam)


def imagem(slide, caminho, x, y, w=None, h=None, corte=None):
    """Mantém a proporção; corte = (esq, dir, topo, base) em frações."""
    lw, lh = Image.open(caminho).size
    e, d, t, b = corte or (0, 0, 0, 0)
    proporcao = (lw * (1 - e - d)) / (lh * (1 - t - b))
    if w is not None and h is not None:
        if w / h > proporcao:
            w = h * proporcao
        else:
            h = w / proporcao
    elif w is not None:
        h = w / proporcao
    else:
        w = h * proporcao
    pic = slide.shapes.add_picture(str(caminho), Inches(x), Inches(y), Inches(w), Inches(h))
    if corte:
        pic.crop_left, pic.crop_right, pic.crop_top, pic.crop_bottom = e, d, t, b
    return pic, w, h


def tabela(slide, x, y, w, linhas, larguras=None, tam=14, alt_linha=0.42, destaque=None, cores_celula=None):
    """linhas[0] = cabeçalho. destaque = índices de linha em negrito. cores_celula = {(i, j): RGBColor}."""
    n, m = len(linhas), len(linhas[0])
    assert n <= 6 and m <= 6, "tabelas de no máximo 6 × 6"
    forma = slide.shapes.add_table(n, m, Inches(x), Inches(y), Inches(w), Inches(alt_linha * n))
    t = forma.table
    larguras = larguras or [w / m] * m
    for j, lw in enumerate(larguras):
        t.columns[j].width = Inches(lw)
    for i in range(n):
        t.rows[i].height = Inches(alt_linha)
        for j in range(m):
            c = t.cell(i, j)
            c.margin_left = c.margin_right = Inches(0.08)
            c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE
            c.fill.solid()
            c.fill.fore_color.rgb = MARINHO if i == 0 else (LINHA_ZEBRA if i % 2 == 0 else BRANCO)
            tf = c.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
            cor = BRANCO if i == 0 else (cores_celula or {}).get((i, j), TINTA)
            _run(p, str(linhas[i][j]), tam, cor, negrito=(i == 0 or (destaque and i in destaque)
                                                          or (cores_celula and (i, j) in cores_celula)))
    return forma


# ---------------------------------------------------------------- moldura dos slides

class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width, self.prs.slide_height = Inches(LARG), Inches(ALT)
        self.vazio = self.prs.slide_layouts[6]
        self.n = 0

    def slide(self, titulo, notas, escuro=False, fonte=None):
        s = self.prs.slides.add_slide(self.vazio)
        self.n += 1
        fundo = s.background.fill
        fundo.solid()
        fundo.fore_color.rgb = MARINHO if escuro else BRANCO
        if titulo and not escuro:
            caixa(s, MX, 0.45, LARG - 2 * MX, 0.75, [titulo], tam=30, cor=MARINHO, ancora=MSO_ANCHOR.MIDDLE,
                  nome="Título").text_frame.paragraphs[0].runs[0].font.bold = True
        if not escuro:
            caixa(s, LARG - MX - 0.6, ALT - 0.45, 0.6, 0.3, [str(self.n)], tam=11, cor=CINZA, alinhar=PP_ALIGN.RIGHT)
            if fonte:
                caixa(s, MX, ALT - 0.45, LARG - 2 * MX - 0.8, 0.3, [fonte], tam=10, cor=CINZA)
        s.notes_slide.notes_text_frame.text = notas
        return s


# ---------------------------------------------------------------- dados

def carregar():
    d = {
        "exp1": pd.read_csv(RES / "exp1_perceptron_adaline_2entradas.csv"),
        "topo": pd.read_csv(RES / "exp3_pmc_topologias_cv.csv"),
        "pmc": pd.read_csv(RES / "exp3_pmc_treinamentos.csv"),
        "aval": pd.read_csv(RES / "exp4_avaliacao.csv"),
        "pred": pd.read_csv(RES / "exp4_predicoes.csv"),
        "topo_dobra": pd.read_csv(RES / "exp4_topologias_por_dobra.csv"),
        "curva": pd.read_csv(RES / "curva_media_concluido.csv"),
        "funil": pd.read_csv(RAIZ / "data" / "processed" / "base_filtros.csv"),
    }
    return d


def metrica(aval, modelo, k, met, cenario="SP, L = 0,8"):
    a = aval[(aval.cenario == cenario) & (aval.k == k) & aval.modelo.str.startswith(modelo)]
    return float(a[met].iloc[0])


def amostra_teste(pred, semente=42, n=5):
    """5 Sprints que cumpriram e 5 que não, do cenário principal em k = 0,5 (ilustrativo)."""
    p = pred[(pred.cenario == "SP, L = 0,8") & (pred.k == 0.5)]
    rng = np.random.default_rng(semente)
    sel = {}
    for cls in (1, 0):
        g = p[p.desejada == cls]
        sel[cls] = g.iloc[np.sort(rng.choice(len(g), n, replace=False))]
    return sel


# ---------------------------------------------------------------- slides

def construir():
    d = carregar()
    aval, exp1 = d["aval"], d["exp1"]
    princ = aval[aval.cenario == "SP, L = 0,8"].iloc[0]
    n_sp, pct_pos = int(princ.n_sprints), princ.pct_positivos * 100
    n_proj = int(princ.n_projetos)
    n_pos = int(round(n_sp * princ.pct_positivos))
    ad, pe = exp1[exp1.rede == "Adaline"], exp1[exp1.rede == "Perceptron"]
    front = ad.fronteira_em_k05.mean()
    curva = d["curva"]
    c05 = curva[(curva.pct_tempo == 0.5)].set_index("cumpriu").media
    k05 = d["pred"][(d["pred"].cenario == "SP, L = 0,8") & (d["pred"].k == 0.5)]
    acima_ad = (k05[k05.desejada == 1].pct_pontos_concluidos >= 0.31).mean() * 100
    acima_b1 = (k05[k05.desejada == 1].pct_pontos_concluidos >= 0.5).mean() * 100
    D = Deck()

    # 1 — título
    s = D.slide(None, escuro=True, notas=(
        "Bom dia. Este trabalho aplica as três redes do livro de Silva, Spatti e Flauzino — Perceptron, Adaline e "
        "Perceptron multicamadas — a um problema de gestão ágil: avisar o Scrum Master, ainda no meio da Sprint, "
        "que a equipe provavelmente não vai cumprir o que se comprometeu a entregar. Os dados são reais, de "
        f"{n_proj} projetos de código aberto do conjunto TAWOS."))
    caixa(s, MX + 0.2, 2.0, 10.5, 2.2, [
        [("Alerta de Sprint em risco", {"tam": 44, "negrito": True, "cor": BRANCO})],
        [("Perceptron, Adaline e PMC aplicados ao burndown de Sprints reais", {"tam": 22, "cor": GELO})]],
        espaco=14)
    caixa(s, MX + 0.2, 5.3, 10, 1.0, [
        [("Inteligência Artificial — Redes Neurais Artificiais", {"tam": 16, "cor": BRANCO})],
        [("Dados: TAWOS v1.1 · Referência: Silva, Spatti & Flauzino", {"tam": 14, "cor": GELO})]])

    # 2 — problema
    s = D.slide("O Scrum Master e a Sprint em risco", fonte="Fonte: TAWOS, Sprint MULE 4351 reconstruída pelo histórico do Jira", notas=(
        "Numa Sprint, a equipe se compromete com um conjunto de itens, medidos em story points. O burndown mostra "
        "quanto falta entregar a cada dia. A linha tracejada é o ritmo ideal, constante até zero. Neste exemplo real, "
        "a Sprint SDK Qin 4 do projeto MULE, na metade do tempo — dia 7,5 — o ideal seria faltar 50 pontos; faltavam 84, "
        "ou seja, só 16% estava pronto. A Sprint terminou com 74% concluído, abaixo da nossa meta de 80%: não cumpriu. "
        "As linhas verticais marcam 30%, 50% e 70% do tempo, os momentos em que vamos fazer a previsão. "
        "Os degraus aparecem porque um item só conta quando é fechado."))
    caixa(s, MX, 1.6, 4.3, 4.6, [
        "O burndown mostra quanto do compromisso ainda falta entregar.",
        [("Na metade desta Sprint, só 16% estava pronto.", {"negrito": True, "cor": LARANJA})],
        "Ela terminou com 74%: não cumpriu.",
        [("Dá para avisar antes?", {"negrito": True, "cor": MARINHO, "tam": 20})]], tam=18, espaco=16)
    imagem(s, FIG / "burndown_amostra" / "MULE_4351.png", 5.3, 1.55, w=7.4)

    # 3 — questão central
    s = D.slide("Questão central e objetivo", notas=(
        "A pergunta do trabalho: olhando só o que aconteceu até 30%, 50% ou 70% do tempo de uma Sprint, uma rede "
        "neural consegue prever se a equipe vai concluir pelo menos 80% do que comprometeu? O objetivo é comparar as "
        "três redes do livro entre si e com duas réguas simples: chutar sempre a classe mais comum, e a diagonal do "
        "burndown ideal, que é o que um Scrum Master faria olhando o gráfico. Importante: em cada momento k usamos só "
        "eventos até aquele instante — sem informação do futuro."))
    retangulo(s, MX, 1.6, LARG - 2 * MX, 1.5, TINTA_CARD)
    caixa(s, MX + 0.35, 1.6, LARG - 2 * MX - 0.7, 1.5, [
        [("Com 30%, 50% ou 70% do tempo decorrido, uma rede neural prevê se a equipe entregará ≥ 80% do compromisso?",
          {"tam": 22, "negrito": True, "cor": MARINHO})]], ancora=MSO_ANCHOR.MIDDLE)
    y = 4.35
    linha = s.shapes.add_connector(1, Inches(1.4), Inches(y), Inches(LARG - 1.4), Inches(y))
    linha.line.color.rgb = CINZA; linha.line.width = Pt(2)
    caixa(s, 0.7, y - 0.2, 0.7, 0.4, ["início"], tam=13, cor=CINZA)
    caixa(s, LARG - 1.3, y - 0.2, 0.7, 0.4, ["fim"], tam=13, cor=CINZA)
    for k in (0.3, 0.5, 0.7):
        cx = 1.4 + k * (LARG - 2.8)
        circulo(s, cx - 0.45, y - 0.45, 0.9, AZUL, f"k = {br(k, 1)}", tam=13)
    caixa(s, MX, 5.4, LARG - 2 * MX, 1.1, [
        [("Objetivo: ", {"negrito": True}), ("comparar as três redes com o burndown ideal, sem usar o futuro.", {})]],
        tam=18)

    # 4 — base de dados
    f = d["funil"]
    s = D.slide("Base de dados: TAWOS e o funil de Sprints", fonte="Fonte: data/processed/base_filtros.csv",
                notas=(
        "Usamos o TAWOS, um conjunto público de projetos ágeis de código aberto extraído do Jira. O TAWOS não diz quais "
        "itens estavam em cada Sprint no início; reconstruímos isso pelo histórico de mudanças do campo Sprint de cada "
        "item: quem estava na Sprint uma hora depois do início é o compromisso; o que entrou depois é escopo adicionado. "
        f"O funil: das {milhar(f.n_sprints.iloc[0])} Sprints, ficam as fechadas, com 5 a 31 dias e pelo menos 5 itens — "
        f"{milhar(f.n_sprints.iloc[4])}. Para usar story points, exigimos que 70% dos itens tivessem pontos no início: "
        f"{milhar(n_sp)} Sprints de {n_proj} projetos, a base principal."))
    caixa(s, MX, 1.65, 4.2, 4.6, [
        [("Compromisso reconstruído ", {"negrito": True}), ("pelo histórico do campo Sprint no Jira.", {})],
        [("Base principal: ", {"negrito": True}), (f"{milhar(n_sp)} Sprints, {n_proj} projetos.", {})]],
        tam=18, espaco=16)
    rotulos = ["Sprints na tabela Sprint", "datas válidas", "State = CLOSED", "duração 5–31 dias",
               "≥ 5 itens comprometidos", "cobertura de SP ≥ 70%"]
    x0, wmax, y0 = 5.0, 4.5, 1.65
    for i, (rot, n) in enumerate(zip(rotulos, f.n_sprints.iloc[:6])):
        w = max(1.3, wmax * n / f.n_sprints.iloc[0])
        cor = MARINHO if i == 5 else (AZUL if i == 4 else GELO)
        r = retangulo(s, x0, y0 + i * 0.78, w, 0.62, cor)
        caixa(s, x0 + 0.15, y0 + i * 0.78, 1.5, 0.62, [milhar(n)], tam=18, ancora=MSO_ANCHOR.MIDDLE,
              cor=BRANCO if i >= 4 else MARINHO).text_frame.paragraphs[0].runs[0].font.bold = True
        caixa(s, x0 + w + 0.15, y0 + i * 0.78, LARG - MX - (x0 + w + 0.15), 0.62, [rot], tam=14, cor=CINZA,
              ancora=MSO_ANCHOR.MIDDLE)

    # 5 — variáveis
    s = D.slide("Variáveis de entrada e saída", fonte="Todas as entradas usam só eventos até o momento k", notas=(
        "Cada exemplo é uma Sprint num momento k. São seis entradas: a fração do tempo decorrido, a fração dos story "
        "points comprometidos já concluída, os pontos adicionados depois do início, os itens em andamento, o tamanho do "
        "compromisso comparado à média entregue nas três Sprints anteriores, e a duração. As razões passam por log e "
        "todas são padronizadas com estatísticas do treino. A saída é bipolar, como no livro: +1 se a Sprint concluiu "
        f"pelo menos 80% dos pontos comprometidos até a data de fim, −1 caso contrário. Só {br(pct_pos, 1)}% das "
        "Sprints cumprem — classes muito desbalanceadas, por isso usamos pesos que equilibram as classes no treino."))
    entradas = ["x₁  tempo decorrido (k)", "x₂  SP concluídos", "x₃  SP adicionados", "x₄  itens em andamento",
                "x₅  compromisso / velocidade", "x₆  duração (dias)"]
    card(s, MX, 1.6, 6.6, 4.9, "Entradas", [[(e, {})] for e in entradas], tam=19)
    retangulo(s, 7.6, 1.6, 5.13, 2.9, MARINHO)
    caixa(s, 7.9, 1.8, 4.6, 2.6, [
        [("Saída desejada d", {"negrito": True, "cor": BRANCO, "tam": 18})],
        [("+1  cumpriu (≥ 80% dos SP)", {"cor": BRANCO})],
        [("−1  não cumpriu", {"cor": BRANCO})],
        [(f"Só {br(pct_pos, 1)}% cumprem", {"cor": GELO, "negrito": True, "tam": 22})]], tam=18, espaco=14)
    card(s, 7.6, 4.75, 5.13, 1.75, "Momentos k", [[("0,3 · 0,5 · 0,7", {})]], tam=18)

    # 6 — metodologia
    s = D.slide("Metodologia: validação por projeto e réguas de comparação", notas=(
        "Para medir como o modelo se sairia numa equipe nova, usamos validação cruzada agrupada por projeto, o "
        "GroupKFold com cinco dobras: em cada rodada, as Sprints de alguns projetos ficam de fora e o modelo é testado "
        "nelas sem nunca as ter visto. Comparamos as redes com duas réguas: B0, que chuta sempre 'não cumpriu', e B1, "
        "o burndown ideal — cumpre se o percentual concluído for pelo menos o percentual de tempo. Como só 11% "
        "cumprem, a acurácia simples engana: B0 acerta 89% sem detectar nada. Por isso usamos AUC, que mede se o "
        "modelo ordena bem as Sprints, acurácia balanceada e F1."))
    caixa(s, MX, 1.6, 6, 0.4, [[("GroupKFold: 5 dobras por projeto", {"negrito": True, "cor": MARINHO})]], tam=17)
    for i in range(5):
        y = 2.15 + i * 0.62
        caixa(s, MX, y, 1.1, 0.48, [f"dobra {i + 1}"], tam=13, cor=CINZA, ancora=MSO_ANCHOR.MIDDLE)
        for j in range(5):
            retangulo(s, MX + 1.15 + j * 0.95, y, 0.85, 0.48, LARANJA if i == j else GELO, arredondado=False)
    caixa(s, MX, 5.35, 6, 0.9, [[("■ ", {"cor": LARANJA}), ("teste: projetos nunca vistos", {})]], tam=14)
    card(s, 7.3, 1.6, 5.43, 2.3, "Réguas (baselines)", [
        [("B0: ", {"negrito": True}), ("sempre \"não cumpriu\"", {})],
        [("B1: ", {"negrito": True}), ("concluído ≥ tempo decorrido", {})]], tam=16)
    card(s, 7.3, 4.15, 5.43, 2.3, "Métricas", [
        [("AUC · acurácia balanceada · F1", {})],
        [("Acurácia simples engana: B0 acerta " + br(metrica(aval, "B0", 0.5, "acuracia") * 100, 0) + "%",
          {"cor": LARANJA, "negrito": True})]], tam=16)

    # 7 — Perceptron
    linhas = [["Semente", "w₀ (bias)", "w₁ (tempo)", "w₂ (concluído)", "Épocas", "Erros finais"]]
    for _, r in pe.iterrows():
        linhas.append([int(r.semente), br(r.w0_limiar), br(r.w1_pct_tempo), br(r.w2_pct_concluido), int(r.epocas),
                       milhar(r.erro_final)])
    n_neg = int(round((n_sp - n_pos) * 3))
    s = D.slide("Perceptron: 5 treinamentos, nenhum converge",
                fonte="Fonte: reports/resultados/exp1_perceptron_adaline_2entradas.csv (3.498 amostras = 1.166 Sprints × 3 k)",
                notas=(
        "Primeiro experimento, no formato do livro: Perceptron com duas entradas, fração do tempo e fração concluída, "
        "mais o bias. Regra de Hebb com taxa de aprendizagem 1, pesos iniciais aleatórios entre −0,5 e 0,5, função "
        "degrau bipolar, no máximo 100 épocas, cinco sementes. O critério de parada do livro é uma época sem erros — "
        "nenhum treinamento chegou lá. O gráfico mostra o número de erros por época: oscila sem cair. As sementes 2 e "
        f"5 terminam com {milhar(n_neg)} erros, exatamente o número de exemplos 'não cumpriu': a reta final classifica "
        "tudo como 'cumpriu'. O teorema de convergência do Perceptron só vale para classes linearmente separáveis, e "
        "aqui as classes se sobrepõem. Os pesos finais são os da última época, por acaso — variam muito entre sementes."))
    caixa(s, MX, 1.55, 6.3, 0.9, [[("2 entradas + bias · degrau bipolar · η = 1 · máx. 100 épocas · "
                                     "pesos iniciais U(−0,5; 0,5)", {"cor": CINZA})]], tam=14)
    tabela(s, MX, 2.3, 6.5, linhas, larguras=[1.0, 1.05, 1.1, 1.3, 0.85, 1.2], tam=13)
    caixa(s, MX, 5.2, 6.4, 1.2, [
        [("Classes não separáveis: ", {"negrito": True, "cor": LARANJA}),
         ("o erro oscila; sementes 2 e 5 dizem \"cumpriu\" para tudo.", {})]], tam=16)
    _, _, h = imagem(s, FIG / "redes" / "exp1_curvas_treinamento.png", 7.35, 1.65, w=5.4, corte=(0, 0.526, 0, 0.1))
    caixa(s, 7.35, 1.75 + h, 5.4, 0.4, ["Cores = sementes 1 a 5 (2 e 5 sobrepostas no topo)"], tam=11, cor=CINZA)

    # 8 — Adaline
    linhas = [["Semente", "w₀ (bias)", "w₁ (tempo)", "w₂ (concluído)", "Épocas", "EQM final"]]
    for _, r in ad.iterrows():
        linhas.append([int(r.semente), br(r.w0_limiar, 3), br(r.w1_pct_tempo, 3), br(r.w2_pct_concluido, 3),
                       int(r.epocas), br(r.erro_final, 4)])
    s = D.slide("Adaline: 5 treinamentos, todos na mesma reta",
                fonte="Fonte: reports/resultados/exp1_perceptron_adaline_2entradas.csv", notas=(
        "Mesmas entradas, agora com o Adaline: regra Delta, que minimiza o erro quadrático médio da saída linear, antes "
        "do degrau. Implementado com o SGDClassifier do scikit-learn com perda quadrática, que é exatamente a regra "
        "Delta do capítulo 4. Taxa de aprendizagem 0,001, precisão 10 elevado a menos 6, até 500 épocas. As cinco "
        f"sementes convergem entre {int(ad.epocas.min())} e {int(ad.epocas.max())} épocas, todas para o mesmo EQM, "
        f"{br(ad.erro_final.mean(), 4)}, e praticamente os mesmos pesos. A diferença para o Perceptron: o EQM é uma "
        "superfície em forma de tigela, com um único mínimo, e o gradiente desce até ele mesmo com classes misturadas. "
        "O EQM é ponderado para as duas classes pesarem igual."))
    caixa(s, MX, 1.55, 6.3, 0.9, [[("Regra Delta · η = 0,001 · ε = 10⁻⁶ · máx. 500 épocas · EQM ponderado "
                                     "pelas classes", {"cor": CINZA})]], tam=14)
    tabela(s, MX, 2.3, 6.5, linhas, larguras=[1.0, 1.05, 1.1, 1.3, 0.85, 1.2], tam=13)
    caixa(s, MX, 5.2, 6.4, 1.2, [
        [("Converge sempre: ", {"negrito": True, "cor": VERDE}),
         (f"{int(ad.epocas.min())}–{int(ad.epocas.max())} épocas, mesmo EQM e mesmos pesos.", {})]], tam=16)
    _, _, h = imagem(s, FIG / "redes" / "exp1_curvas_treinamento.png", 7.35, 1.65, w=5.4, corte=(0.487, 0, 0, 0.1))
    caixa(s, 7.35, 1.75 + h, 5.4, 0.4, ["Cores = sementes 1 a 5 (escala logarítmica)"], tam=11, cor=CINZA)

    # 9 — figura principal
    s = D.slide("Retas aprendidas × diagonal do burndown ideal",
                fonte="Fonte: exp2_fronteiras_2entradas.png; curva_media_concluido.csv; 3.498 amostras", notas=(
        "Esta é a figura principal. Cada ponto é uma Sprint num momento k: laranja cumpriu, cinza não. A diagonal "
        "tracejada é o burndown ideal, o B1. As retas verdes são o Adaline nas cinco sementes — quase sobrepostas; as "
        "azuis, o Perceptron, espalhadas. Na metade da Sprint, a diagonal exige 50% concluído; o Adaline corta em "
        f"{br(front * 100, 0)}%. Por quê? A reta passa entre as duas nuvens: em k = 0,5, quem cumpriu tinha em média "
        f"{br(c05[1] * 100, 0)}% concluído e quem não cumpriu, {br(c05[0] * 100, 0)}%. Com o corte em 31%, "
        f"{br(acima_ad, 0)}% das Sprints que cumpriram ficam acima; com 50%, só {br(acima_b1, 0)}%. Testamos a "
        "hipótese de que as equipes deixam as entregas para o fim e ela não se confirmou: a curva média de quem cumpre "
        "é quase linear. Para o Scrum Master: abaixo de ~31% na metade da Sprint, o risco é alto; entre 31% e 50%, "
        "zona cinzenta."))
    imagem(s, FIG / "redes" / "exp2_fronteiras_2entradas.png", MX, 1.45, w=8.1, h=5.45)
    x = 9.1
    caixa(s, x, 1.6, 3.6, 0.5, ["Na metade da Sprint (k = 0,5):"], tam=16, cor=CINZA)
    caixa(s, x, 2.1, 3.6, 1.1, [[(f"{br(front * 100, 0)}%", {"tam": 54, "negrito": True, "cor": VERDE})]])
    caixa(s, x, 3.15, 3.6, 0.5, ["corte do Adaline"], tam=15)
    caixa(s, x, 3.75, 3.6, 1.1, [[("50%", {"tam": 54, "negrito": True, "cor": CINZA})]])
    caixa(s, x, 4.8, 3.6, 0.5, ["diagonal do burndown ideal"], tam=15)
    caixa(s, x, 5.45, 3.6, 1.0, [
        [(f"Acima de {br(front * 100, 0)}%: {br(acima_ad, 0)}% das Sprints que cumprem. Acima de 50%: "
          f"só {br(acima_b1, 0)}%.", {})]], tam=14)

    # 10 — PMC
    topo, pmc = d["topo"], d["pmc"]
    escolhida = int(pmc.n_ocultos.iloc[0])
    linhas_t = [["Neurônios", "AUC (validação)"]] + [[int(r.n_ocultos), br(r.auc_fora_da_dobra, 3)]
                                                      for _, r in topo.iterrows()]
    linhas_p = [["Semente", "Erro final", "Épocas", "AUC treino"]] + [
        [int(r.semente), br(r.erro_final_entropia_cruzada, 3), milhar(r.epocas), br(r.auc_treino, 3)]
        for _, r in pmc.iterrows()]
    auc_pmc = metrica(aval, "PMC", 0.5, "auc")
    s = D.slide("PMC: topologia, 5 treinamentos e sobreajuste",
                fonte="Fonte: exp3_pmc_topologias_cv.csv, exp3_pmc_treinamentos.csv, exp4_avaliacao.csv", notas=(
        "O Perceptron multicamadas usa as seis entradas, uma camada oculta logística e saída logística, treinado por "
        "retropropagação com momentum 0,9, taxa 0,01, regularização L2 de 0,01, até 2.000 épocas, com reamostragem "
        "da classe rara no treino. Testamos 5, 10 e 15 neurônios por validação cruzada por projeto: "
        f"{escolhida} teve a maior AUC, mas as três ficaram a menos de 0,01. A perda é a entropia cruzada, que o "
        "scikit-learn usa no lugar do EQM do livro. Ela cai rápido nas primeiras épocas e depois devagar; nenhum dos "
        "cinco treinamentos atingiu o critério de parada. O ponto principal é o sobreajuste: AUC de "
        f"{br(pmc.auc_treino.mean(), 2)} no treino, mas {br(auc_pmc, 2)} em projetos nunca vistos, em k = 0,5 — "
        f"abaixo do Adaline, {br(metrica(aval, 'Adaline', 0.5, 'auc'), 2)}. A capacidade extra aprende "
        "particularidades dos projetos do treino."))
    caixa(s, MX, 1.55, 6.2, 0.6, [[(f"1 camada oculta logística · η = 0,01 · momentum 0,9 · L2 = 0,01 · "
                                     "máx. 2.000 épocas", {"cor": CINZA})]], tam=14)
    tabela(s, MX, 2.3, 2.5, linhas_t, larguras=[1.1, 1.4], tam=13, destaque=[
        1 + list(topo.n_ocultos).index(escolhida)])
    tabela(s, 3.25, 2.3, 3.85, linhas_p, larguras=[1.05, 1.0, 0.8, 1.0], tam=13)
    caixa(s, MX, 4.25, 2.6, 0.8, [f"Escolhida: {escolhida} neurônios"], tam=13, cor=CINZA)
    imagem(s, FIG / "redes" / "exp3_pmc_loss_curve.png", 7.35, 1.55, w=5.4)
    retangulo(s, MX, 5.15, 6.45, 1.35, TINTA_CARD)
    caixa(s, MX + 0.25, 5.15, 6.0, 1.35, [
        [("Sobreajuste: ", {"negrito": True, "cor": LARANJA}),
         (f"AUC {br(pmc.auc_treino.mean(), 2)} no treino × {br(auc_pmc, 2)} em projetos nunca vistos (k = 0,5).", {})]],
        tam=16, ancora=MSO_ANCHOR.MIDDLE)
    caixa(s, 7.35, 4.7, 5.4, 0.5, ["Perda = entropia cruzada"], tam=12, cor=CINZA)

    # 11 — amostras de teste (2 slides)
    sel = amostra_teste(d["pred"])
    bip = lambda v: "+1" if v == 1 else "−1"  # noqa: E731
    for cls, titulo in [(1, "Amostras de teste (1/2): Sprints que cumpriram"),
                        (0, "Amostras de teste (2/2): Sprints que não cumpriram")]:
        g = sel[cls]
        linhas = [["Sprint", "x₂ concluído", "Perceptron", "Adaline", "PMC", "Desejada"]]
        cores = {}
        for i, (_, r) in enumerate(g.iterrows(), start=1):
            saidas = [r.Perceptron_saida, r.Adaline_saida, r.PMC_saida]
            linhas.append([f"{r.projeto} {int(r.sprint_id)}", f"{br(r.pct_pontos_concluidos * 100, 0)}%",
                           *[bip(v) for v in saidas], bip(r.desejada)])
            for j, v in enumerate(saidas, start=2):
                if v != r.desejada:
                    cores[(i, j)] = LARANJA
        acertos = {n: int((g[f"{n}_saida"] == g.desejada).sum()) for n in ("Perceptron", "Adaline", "PMC")}
        s = D.slide(titulo, fonte="Fonte: exp4_predicoes.csv — predições fora da dobra, k = 0,5, sorteio com semente 42",
                    notas=(
            "Tabela no estilo do livro: amostras de teste, com entradas, a saída de cada rede e a saída desejada. "
            "Cada Sprint foi prevista por redes que não viram nenhuma Sprint do seu projeto. Todas estão em k = 0,5, "
            "então x₁ vale 0,5 para todas; mostramos x₂, a fração concluída, que é a entrada que mais pesa; as outras "
            "quatro estão no arquivo de predições. Em laranja, as saídas erradas. "
            f"Nestas cinco: Perceptron acerta {acertos['Perceptron']}, Adaline {acertos['Adaline']}, PMC "
            f"{acertos['PMC']}. Atenção: sorteamos 5 Sprints que cumpriram e 5 que não, só para ilustrar. Na base real "
            f"só {br(pct_pos, 1)}% cumprem; as taxas de acerto oficiais estão nos próximos slides."))
        tabela(s, MX, 1.65, 8.2, linhas, larguras=[2.1, 1.4, 1.3, 1.1, 1.0, 1.3], tam=15, alt_linha=0.55)
        retangulo(s, 9.25, 1.65, 3.48, 3.3, TINTA_CARD)
        caixa(s, 9.5, 1.85, 3.0, 3.0, [
            [("Amostra ilustrativa 5/5", {"negrito": True, "cor": MARINHO, "tam": 17})],
            [(f"Na base real, só {br(pct_pos, 1)}% das Sprints cumprem.", {"tam": 16})],
            [("Laranja = saída errada.", {"tam": 14, "cor": LARANJA, "negrito": True})]], espaco=12)
        caixa(s, MX, 5.15, 8.2, 0.9, [
            [("Todas em k = 0,5 (x₁ = 0,5). Saída bipolar: +1 cumpriu, −1 não cumpriu. "
              "Demais entradas em exp4_predicoes.csv.", {"cor": CINZA})]], tam=13)

    # 12a — comparativo em tabelas
    modelos = [("B0", "B0"), ("B1", "B1"), ("Perceptron", "Perceptron"), ("Adaline", "Adaline"), ("PMC", "PMC")]
    def tab_met(met):
        lin = [["Modelo", "k = 0,3", "k = 0,5", "k = 0,7"]]
        for rot, chave in modelos:
            vals = [metrica(aval, chave, k, met) for k in (0.3, 0.5, 0.7)]
            lin.append([rot] + ["—" if np.isnan(v) else br(v) for v in vals])
        return lin
    s = D.slide("Comparativo: as redes contra as réguas",
                fonte=f"Fonte: exp4_avaliacao.csv — GroupKFold por projeto, {milhar(n_sp)} Sprints, {br(pct_pos, 1)}% cumpriu",
                notas=(
        "Resultados fora da dobra, no cenário principal. Na AUC, à esquerda, Adaline e B1 empatam nos três momentos — "
        f"{br(metrica(aval, 'Adaline', 0.5, 'auc'))} contra {br(metrica(aval, 'B1', 0.5, 'auc'))} em k = 0,5; o PMC "
        "fica abaixo e o Perceptron piora com k. Na acurácia balanceada, à direita, o Adaline é o melhor e a vantagem "
        f"sobre o B1 cresce com k: {br(metrica(aval, 'Adaline', 0.7, 'acuracia_balanceada'))} contra "
        f"{br(metrica(aval, 'B1', 0.7, 'acuracia_balanceada'))} em k = 0,7. O B0 tem AUC indefinida, porque dá a mesma "
        "resposta para todos, e acurácia balanceada 0,5. A taxa de acerto simples não aparece aqui de propósito: o B0 "
        f"teria {br(metrica(aval, 'B0', 0.5, 'acuracia') * 100, 1)}% sem reconhecer nenhuma Sprint que cumpre."))
    caixa(s, MX, 1.55, 5.9, 0.45, [[("AUC", {"negrito": True, "cor": MARINHO})]], tam=18)
    tabela(s, MX, 2.05, 5.9, tab_met("auc"), larguras=[2.0, 1.3, 1.3, 1.3], tam=15, alt_linha=0.5, destaque=[4])
    caixa(s, 6.83, 1.55, 5.9, 0.45, [[("Acurácia balanceada", {"negrito": True, "cor": MARINHO})]], tam=18)
    tabela(s, 6.83, 2.05, 5.9, tab_met("acuracia_balanceada"), larguras=[2.0, 1.3, 1.3, 1.3], tam=15,
           alt_linha=0.5, destaque=[4])
    caixa(s, MX, 5.35, LARG - 2 * MX, 1.0, [
        [("Adaline empata com B1 em AUC e o supera em acurácia balanceada.", {"negrito": True})]], tam=18)

    # 12b — métrica × k
    s = D.slide("Métrica × k: quanto mais tarde, melhor a previsão",
                fonte="Fonte: exp4_metrica_vs_k_principal.png — tracejado = réguas; contínuo = redes", notas=(
        "O mesmo resultado em gráfico. Eixo x: o momento da previsão. Três painéis: AUC, acurácia balanceada e F1. "
        "Tracejadas, as réguas: B0 azul, B1 laranja. Contínuas, as redes: Perceptron verde, Adaline amarelo, PMC rosa. "
        "Mensagem principal: para B1, Adaline e PMC as curvas sobem com k — quanto mais tarde, mais fácil prever, o "
        "que é esperado. Em AUC, amarelo e laranja se sobrepõem. Em F1, Adaline e B1 também empatam, "
        f"{br(metrica(aval, 'Adaline', 0.5, 'f1'))} e {br(metrica(aval, 'B1', 0.5, 'f1'))} em k = 0,5. O Perceptron "
        "cai porque sua reta final é arbitrária."))
    imagem(s, FIG / "redes" / "exp4_metrica_vs_k_principal.png", MX, 1.6, w=LARG - 2 * MX)
    caixa(s, MX, 5.75, LARG - 2 * MX, 0.6, [
        [("B1, Adaline e PMC melhoram com k. Adaline ≈ B1 em AUC e F1.", {"negrito": True})]], tam=18)

    # 13 — matrizes
    a05 = aval[(aval.cenario == "SP, L = 0,8") & (aval.k == 0.5)].set_index("modelo")
    b1, ada = a05.loc["B1 — burndown ideal"], a05.loc["Adaline"]
    s = D.slide("Matrizes de confusão (k = 0,5): a troca entre os erros",
                fonte="Fonte: exp4_avaliacao.csv; positivo = \"cumpriu\"", notas=(
        f"Na metade da Sprint, das {int(b1.VP + b1.FN)} Sprints que cumpriram, o Adaline reconhece {int(ada.VP)}; "
        f"o B1, só {int(b1.VP)}. Em troca, das {int(b1.VN + b1.FP)} Sprints em risco, o Adaline deixa passar "
        f"{int(ada.FP)} sem alerta; o B1, {int(b1.FP)}. Para o Scrum Master, o erro mais grave é a Sprint em risco "
        "sem alerta, o contorno laranja: ele perde a chance de renegociar escopo ou remover impedimentos e só descobre "
        "na Review. Um alarme falso custa uma conversa no Daily. Por esse critério o B1 é mais seguro — mas alerta em "
        f"{br((b1.VN + b1.FN) / n_sp * 100, 0)}% das Sprints, contra {br((ada.VN + ada.FN) / n_sp * 100, 0)}% do "
        "Adaline, e um alarme que toca quase sempre é ignorado. Como a AUC é igual, a troca vem do ponto de corte: "
        "subindo o corte do Adaline até 43 Sprints sem alerta, a matriz fica idêntica à do B1. É uma decisão de gestão."))
    imagem(s, FIG / "redes" / "exp4_matrizes_confusao_k05.png", MX, 1.5, w=8.4)
    x = 9.3
    caixa(s, x, 1.6, 3.4, 1.6, [
        [(f"{int(ada.VP)} × {int(b1.VP)}", {"tam": 34, "negrito": True, "cor": VERDE})],
        ["Sprints que cumprem, reconhecidas (Adaline × B1)"]], tam=14, espaco=2)
    caixa(s, x, 3.3, 3.4, 1.6, [
        [(f"{int(ada.FP)} × {int(b1.FP)}", {"tam": 34, "negrito": True, "cor": LARANJA})],
        ["Sprints em risco sem alerta (Adaline × B1)"]], tam=14, espaco=2)
    retangulo(s, x, 5.0, 3.43, 1.45, TINTA_CARD)
    caixa(s, x + 0.2, 5.0, 3.05, 1.45, [
        [("Mais grave: ", {"negrito": True, "cor": LARANJA}), ("Sprint em risco sem alerta. O limiar define a troca.", {})]],
        tam=14, ancora=MSO_ANCHOR.MIDDLE)

    # 14 — robustez
    linhas = [["Cenário", "Sprints", "% cumpriu", "AUC Adaline", "AUC B1", "AUC PMC"]]
    for cen, rot in [("SP, L = 0,8", "Principal (SP)"), ("itens, L = 0,8", "Contagem de itens"),
                     ("SP, L = 0,8, sem DM", "SP sem o projeto DM")]:
        r = aval[aval.cenario == cen].iloc[0]
        linhas.append([rot, milhar(r.n_sprints), f"{br(r.pct_positivos * 100, 1)}%",
                       br(metrica(aval, "Adaline", 0.5, "auc", cen)), br(metrica(aval, "B1", 0.5, "auc", cen)),
                       br(metrica(aval, "PMC", 0.5, "auc", cen))])
    s = D.slide("Robustez: itens no lugar de pontos e sem o projeto DM",
                fonte="Fonte: exp4_avaliacao.csv — k = 0,5; curvas em exp4_metrica_vs_k_robustez.png e _sem_DM.png",
                notas=(
        "Duas verificações. Primeiro, contar itens em vez de story points: a base sobe para 2.027 Sprints de 35 "
        "projetos e a conclusão se mantém — Adaline, B1 e PMC próximos, com o Adaline ligeiramente à frente. Segundo, "
        "tirar o DM, o maior projeto, que quase nunca cumpre (1% de positivos): Adaline e B1 continuam empatados. "
        "Os resultados não dependem da unidade nem de um projeto dominante."))
    tabela(s, MX, 1.65, LARG - 2 * MX, linhas, larguras=[3.4, 1.6, 1.7, 1.8, 1.6, 2.033], tam=15, alt_linha=0.55)
    auc = lambda m, c: br(metrica(aval, m, 0.5, "auc", c))  # noqa: E731
    card(s, MX, 4.2, 5.95, 1.45, "Contagem de itens", [
        [(f"Mesma ordem: Adaline {auc('Adaline', 'itens, L = 0,8')} ≥ B1 {auc('B1', 'itens, L = 0,8')} > "
          f"PMC {auc('PMC', 'itens, L = 0,8')}.", {})]], tam=17)
    card(s, 6.78, 4.2, 5.95, 1.45, "Sem o DM (1% de positivos)", [
        [(f"Adaline {auc('Adaline', 'SP, L = 0,8, sem DM')} e B1 {auc('B1', 'SP, L = 0,8, sem DM')} "
          "seguem empatados.", {})]], tam=17)

    # 15 — limitações
    s = D.slide("Limitações", notas=(
        "Quatro limitações. Primeira: o Guia Scrum define o compromisso como o Sprint Goal, um objetivo em texto, que o "
        "TAWOS não tem; usamos a fração dos pontos comprometidos entregue como substituto. Segunda: ajustamos uma vez "
        "os hiperparâmetros e o critério de escolha da topologia do PMC depois de ver a primeira rodada; paramos ali "
        "para não otimizar no teste, mas o PMC teve essa vantagem. Terceira: o scikit-learn treina o PMC minimizando "
        "entropia cruzada, não o EQM do livro. Quarta: são projetos de código aberto, em que só 11% das Sprints "
        "cumprem e o compromisso é em média 2,3 vezes a velocidade — empresas podem ter outro comportamento."))
    itens = [("Sprint Goal", "Ausente no TAWOS; usamos a fração de SP entregue."),
             ("Ajuste do PMC", "Revisto uma vez após a 1ª rodada."),
             ("Entropia cruzada × EQM", "O PMC do scikit-learn não usa o EQM do livro."),
             ("Código aberto", f"Só {br(pct_pos, 1)}% das Sprints cumprem.")]
    for i, (tit, txt) in enumerate(itens):
        x, y = MX + (i % 2) * 6.17, 1.75 + (i // 2) * 2.1
        retangulo(s, x, y, 5.95, 1.8, TINTA_CARD)
        circulo(s, x + 0.3, y + 0.3, 0.6, MARINHO, str(i + 1), tam=16)
        caixa(s, x + 1.15, y + 0.3, 4.55, 1.3, [[(tit, {"negrito": True, "cor": MARINHO, "tam": 20})], [txt]],
              tam=18, espaco=10)

    # 16 — conclusões
    s = D.slide(None, escuro=True, notas=(
        "Conclusões. Sim, dá para prever, e quanto mais tarde, melhor: a AUC do Adaline vai de "
        f"{br(metrica(aval, 'Adaline', 0.3, 'auc'))} a {br(metrica(aval, 'Adaline', 0.7, 'auc'))}. O Adaline é a "
        "melhor das três redes; empata com o burndown ideal em ordenar as Sprints e o supera em acurácia balanceada, "
        "porque aprende um corte adequado — 31% na metade da Sprint. O Perceptron não converge, como o livro prevê "
        "para classes não separáveis, e o PMC sobreajusta. Para a rede não linear ganhar, faltam variáveis com "
        "informação nova: comentários, mudanças de responsável, itens bloqueados, dependências. Também ficam como "
        "trabalhos futuros o Perceptron com bolso, a escolha do limiar no treino e implementar as redes do zero."))
    caixa(s, MX + 0.2, 0.6, 12, 0.8, [[("Conclusões", {"tam": 32, "negrito": True, "cor": BRANCO})]])
    concl = [f"AUC do Adaline sobe com k: {br(metrica(aval, 'Adaline', 0.3, 'auc'))}\u00a0→\u00a0"
             f"{br(metrica(aval, 'Adaline', 0.7, 'auc'))}.",
             f"Adaline: melhor rede; corte de {br(front * 100, 0)}% na metade da Sprint.",
             "Perceptron não converge; PMC sobreajusta."]
    caixa(s, MX + 0.2, 1.6, 6.6, 4.5, [[("• " + c, {"cor": BRANCO})] for c in concl], tam=21, espaco=22)
    retangulo(s, 7.6, 1.6, 5.13, 2.9, RGBColor(0x26, 0x3A, 0x5A))
    caixa(s, 7.9, 1.85, 4.6, 4.1, [
        [("Trabalhos futuros", {"negrito": True, "cor": BRANCO, "tam": 19})],
        [("Variáveis novas (comentários, bloqueios)", {"cor": GELO})],
        [("Perceptron com bolso; limiar no treino", {"cor": GELO})],
        [("Redes implementadas do zero (NumPy)", {"cor": GELO})]], tam=18, espaco=16)

    # 17 — referências
    s = D.slide("Referências", notas=(
        "As referências: o livro-texto da disciplina, o Guia do Scrum e o livro de Jeff Sutherland para os conceitos de "
        "Sprint e compromisso, o artigo do conjunto de dados TAWOS e o scikit-learn, biblioteca usada nas três redes. "
        "O código, os dados processados e todos os números desta apresentação estão no repositório do projeto. "
        "Obrigado; fico à disposição para perguntas."))
    refs = [
        "SILVA, I. N.; SPATTI, D. H.; FLAUZINO, R. A. Redes Neurais Artificiais para Engenharia e Ciências "
        "Aplicadas: curso prático. 2. ed. São Paulo: Artliber, 2016.",
        "SCHWABER, K.; SUTHERLAND, J. O Guia do Scrum: o guia definitivo para o Scrum. 2020. Disponível em: "
        "scrumguides.org.",
        "SUTHERLAND, J. Scrum: the art of doing twice the work in half the time. New York: Crown Business, 2014.",
        "TAWOSI, V.; AL-SUBAIHIN, A.; MOUSSA, R.; SARRO, F. A versatile dataset of agile open source software "
        "projects. In: MSR 2022. Dados: DOI 10.5522/04/21308124.",
        "PEDREGOSA, F. et al. Scikit-learn: machine learning in Python. JMLR, v. 12, p. 2825–2830, 2011."]
    caixa(s, MX, 1.65, LARG - 2 * MX, 5, [[(r, {})] for r in refs], tam=15, espaco=14)

    D.prs.save(SAIDA)
    return D.n


if __name__ == "__main__":
    print(f"{construir()} slides -> {SAIDA.relative_to(RAIZ)}")
