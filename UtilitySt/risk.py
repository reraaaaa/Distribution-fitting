"""Вероятности, квантили и меры риска распределения. Чистые функции, без Streamlit."""
import math
import warnings

import numpy as np
from scipy import integrate

# В каком хвосте распределения лежат потери
LEFT = 'left'    # величина - доходность или прибыль: потери - это малые значения
RIGHT = 'right'  # величина - убыток: потери - это большие значения

RISK_LEVELS = (0.95, 0.975, 0.99)


def interval_probability(rv, low, high):
    """
    :return: P(low < X <= high)
    """
    if high <= low:
        return 0.0
    return float(rv.cdf(high) - rv.cdf(low))


def value_at_risk(rv, level, tail=LEFT):
    """
    VaR уровня level: потеря, которая не будет превышена с вероятностью level. Возвращается как размер потери:
    для доходностей (tail=LEFT) это -квантиль уровня 1 - level, для убытков (tail=RIGHT) - квантиль уровня level.
    """
    if tail == LEFT:
        return -float(rv.ppf(1 - level))
    return float(rv.ppf(level))


def tail_mean_is_finite(rv, tail):
    """
    Конечно ли среднее в хвосте потерь. Если носитель с этой стороны ограничен, оно конечно; иначе
    полагаемся на среднее распределения: у Коши и у Стьюдента с df <= 1 оно не определено.
    """
    low, high = rv.support()
    if math.isfinite(low if tail == LEFT else high):
        return True
    try:
        with np.errstate(all='ignore'):
            return bool(np.isfinite(rv.mean()))
    except (ArithmeticError, ValueError, RuntimeError):
        return False


def expected_shortfall(rv, level, tail=LEFT):
    """
    Expected Shortfall (CVaR) уровня level: средняя потеря в худших 1 - level случаях.
    Считается как среднее квантильной функции по хвосту. Если среднее в хвосте бесконечно
    или не определено, возвращается inf: числа, которому можно верить, тут нет.
    """
    alpha = 1 - level
    if not tail_mean_is_finite(rv, tail):
        return math.inf
    with warnings.catch_warnings(), np.errstate(all='ignore'):
        warnings.simplefilter('ignore', integrate.IntegrationWarning)
        if tail == LEFT:
            integral, _ = integrate.quad(rv.ppf, 0, alpha, limit=200)
            return -integral / alpha
        integral, _ = integrate.quad(rv.ppf, level, 1, limit=200)
        return integral / alpha
