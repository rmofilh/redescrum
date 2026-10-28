"""Perceptron, Adaline e PMC com interface comum: treinar(X, y) / prever(X) / escore(X).

Bibliotecas (permitidas pelo professor): scikit-learn.
- Perceptron: sklearn.linear_model.Perceptron, treinado época a época (partial_fit) para registrar
  erros por época e aplicar o critério de parada do livro (época sem erros).
- Adaline: sklearn.linear_model.SGDClassifier(loss="squared_error"), que com penalty=None e
  learning_rate="constant" é a regra Delta (Silva, Spatti & Flauzino, cap. 4):
      livro:   E(w) = 1/(2p) Σ (d(k) − u(k))²,   u = wᵀx (saída linear, antes do degrau)
               w ← w + η (d(k) − u(k)) x(k)       (ajuste amostra a amostra)
               parada: |EQM_atual − EQM_anterior| ≤ ε;  operação: y = sinal(u)
      sklearn: perda ½ (y − wᵀx)² com y ∈ {−1, +1}; o SGD "puro" faz exatamente
               w ← w + η (y − wᵀx) x para cada amostra; decision_function devolve u e predict usa sinal(u).
  O laço de épocas é feito aqui (partial_fit) para calcular o EQM do livro e aplicar o seu critério de parada.
  Pesos iniciais aleatórios pequenos, como no livro (o sklearn começaria em zero).
- PMC: sklearn.neural_network.MLPClassifier, com 1 camada oculta logística, retropropagação com momentum
  (solver="sgd") e saída logística. A perda do sklearn é a entropia cruzada (o livro usa o EQM).

Desequilíbrio: Perceptron e Adaline recebem sample_weight "balanced" (equivale a class_weight="balanced",
que o partial_fit não aceita); o PMC, que não tem class_weight, recebe sobreamostragem dos positivos só no treino.
"""
import warnings

import numpy as np
from joblib import Parallel, delayed
from sklearn.exceptions import ConvergenceWarning
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Perceptron, SGDClassifier
from sklearn.model_selection import GroupKFold
from sklearn.metrics import roc_auc_score
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import FunctionTransformer, StandardScaler
from sklearn.utils.class_weight import compute_sample_weight

from src.analise_sinal import _log_ratios, _sobreamostrar

warnings.filterwarnings("ignore", category=ConvergenceWarning)


def preprocessador():
    """O mesmo da análise de sinal: imputação (mediana + indicador), log1p das razões, z-score."""
    return make_pipeline(SimpleImputer(strategy="median", add_indicator=True),
                         FunctionTransformer(_log_ratios), StandardScaler())


class Rede:
    """Interface comum. Subclasses implementam _ajustar(X, y) e _escore(X)."""

    nome = "rede"

    def __init__(self, semente=0, padronizar=True):
        self.semente = semente
        self.pre = preprocessador() if padronizar else None

    def _x(self, X, ajustar=False):
        X = np.asarray(X, float)
        if self.pre is None:
            return X
        return self.pre.fit_transform(X) if ajustar else self.pre.transform(X)

    def treinar(self, X, y):
        self._ajustar(self._x(X, ajustar=True), np.asarray(y, int))
        return self

    def escore(self, X):
        """Saída contínua (para AUC): u = wᵀx (Perceptron/Adaline) ou P(cumpriu) (PMC)."""
        return self._escore(self._x(X))

    def prever(self, X):
        """Classe 1 = cumpriu."""
        return (self.escore(X) >= self.limiar).astype(int)


class _RedeLinear(Rede):
    """Laço de épocas comum ao Perceptron e ao Adaline (pesos iniciais aleatórios, parada do livro)."""

    limiar = 0.0

    def __init__(self, eta, max_epocas, semente=0, padronizar=True):
        super().__init__(semente, padronizar)
        self.eta, self.max_epocas = eta, max_epocas

    def _ajustar(self, X, y):
        rng = np.random.default_rng(self.semente)
        w0 = rng.uniform(-0.5, 0.5, size=(1, X.shape[1]))
        b0 = rng.uniform(-0.5, 0.5, size=1)
        sw = compute_sample_weight("balanced", y)
        self.modelo = self._estimador()
        self.modelo.set_params(max_iter=1, tol=None)
        self.modelo.fit(X, y, coef_init=w0.ravel(), intercept_init=b0, sample_weight=sw)  # 1ª época
        self.historico_ = [self._medida(X, y, sw)]
        self.convergiu_ = self._parou()
        while not self.convergiu_ and len(self.historico_) < self.max_epocas:
            self.modelo.partial_fit(X, y, sample_weight=sw)
            self.historico_.append(self._medida(X, y, sw))
            self.convergiu_ = self._parou()
        self.n_epocas_ = len(self.historico_)
        self.w_ = np.concatenate([self.modelo.intercept_, self.modelo.coef_[0]])  # [b, w1, ..., wn]

    def _escore(self, X):
        return self.modelo.decision_function(X)


class PerceptronRede(_RedeLinear):
    """Regra de Hebb do Perceptron: w ← w + η (d − y) x; para quando uma época termina sem erros."""

    nome = "Perceptron"

    def __init__(self, eta=1.0, max_epocas=100, semente=0, padronizar=True):
        super().__init__(eta, max_epocas, semente, padronizar)

    def _estimador(self):
        return Perceptron(eta0=self.eta, penalty=None, shuffle=True, random_state=self.semente)

    def _medida(self, X, y, sw):
        return int((self.modelo.predict(X) != y).sum())  # nº de amostras classificadas errado

    def _parou(self):
        return self.historico_[-1] == 0


class AdalineRede(_RedeLinear):
    """Regra Delta (ver docstring do módulo); para quando |ΔEQM| ≤ ε."""

    nome = "Adaline"

    def __init__(self, eta=1e-3, max_epocas=500, epsilon=1e-6, semente=0, padronizar=True):
        super().__init__(eta, max_epocas, semente, padronizar)
        self.epsilon = epsilon

    def _estimador(self):
        return SGDClassifier(loss="squared_error", penalty=None, learning_rate="constant", eta0=self.eta,
                             shuffle=True, random_state=self.semente)

    def _medida(self, X, y, sw):
        d = np.where(y == 1, 1.0, -1.0)
        u = self.modelo.decision_function(X)
        return float(np.average(0.5 * (d - u) ** 2, weights=sw))  # EQM ponderado pelas classes

    def _parou(self):
        h = self.historico_
        return len(h) > 1 and abs(h[-1] - h[-2]) <= self.epsilon


class PMCRede(Rede):
    """Perceptron multicamadas com 1 camada oculta."""

    nome = "PMC"
    limiar = 0.5

    def __init__(self, n_ocultos=10, semente=0, padronizar=True, eta=0.01, momentum=0.9, alfa=1e-2, max_epocas=2000):
        super().__init__(semente, padronizar)
        self.n_ocultos, self.eta, self.momentum, self.max_epocas = n_ocultos, eta, momentum, max_epocas
        self.alfa = alfa  # penalização L2 (a mesma da MLP da análise de sinal)

    def _ajustar(self, X, y):
        Xt, yt = _sobreamostrar(X, y, np.random.default_rng(self.semente))
        self.modelo = MLPClassifier(hidden_layer_sizes=(self.n_ocultos,), activation="logistic", solver="sgd",
                                    learning_rate_init=self.eta, momentum=self.momentum, alpha=self.alfa, max_iter=self.max_epocas,
                                    tol=1e-5, n_iter_no_change=20, random_state=self.semente)
        self.modelo.fit(Xt, yt)
        self.historico_ = list(self.modelo.loss_curve_)
        self.n_epocas_ = self.modelo.n_iter_
        self.convergiu_ = self.n_epocas_ < self.max_epocas
        self.erro_final_ = float(self.modelo.loss_)

    def _escore(self, X):
        return self.modelo.predict_proba(X)[:, 1]


def _escores_dobra(n, X, y, tr, va, semente):
    rede = PMCRede(n_ocultos=n, semente=semente).treinar(X[tr], y[tr])
    return n, va, rede.escore(X[va])


def escolher_topologia(X, y, grupos, candidatos=(5, 10, 15), n_dobras=3, semente=0, n_jobs=-1):
    """Validação cruzada só no treino (GroupKFold por projeto): nº de neurônios com maior AUC.

    A AUC é calculada sobre as predições fora da dobra agregadas (como na avaliação externa), e não pela média
    das AUCs por dobra: uma dobra com pouquíssimos positivos (ex.: só o DM, 0,8%) deixa a AUC da dobra instável.
    O desvio-padrão por dobra é registrado só como informação. Empate (até a 3ª casa) favorece a rede menor.
    """
    X, y, grupos = np.asarray(X, float), np.asarray(y, int), np.asarray(grupos)
    dobras = list(GroupKFold(n_splits=n_dobras).split(X, y, grupos))
    res = Parallel(n_jobs=n_jobs)(delayed(_escores_dobra)(n, X, y, tr, va, semente)
                                  for n in candidatos for tr, va in dobras)
    linhas = []
    for n in candidatos:
        oof = np.full(len(y), np.nan)
        por_dobra = []
        for m, va, s in res:
            if m == n:
                oof[va] = s
                if len(np.unique(y[va])) == 2:
                    por_dobra.append(roc_auc_score(y[va], s))
        linhas.append({"n_ocultos": n, "auc_fora_da_dobra": float(roc_auc_score(y, oof)),
                       "auc_media_por_dobra": float(np.mean(por_dobra)), "auc_dp_por_dobra": float(np.std(por_dobra))})
    melhor = max(linhas, key=lambda r: (round(r["auc_fora_da_dobra"], 3), -r["n_ocultos"]))["n_ocultos"]
    return melhor, linhas
