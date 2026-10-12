"""Вероятности, квантили и меры риска распределения. Чистые функции, без Streamlit."""
import math
import warnings

import numpy as np
from scipy import integrate, stats

# В каком хвосте распределения лежат потери
LEFT = 'left'    # величина - доходность или прибыль: потери - это малые значения
RIGHT = 'right'  # величина - убыток: потери - это большие значения

RISK_LEVELS = (0.95, 0.975, 0.99)

# длина куска интегрирования по u = -ln p при расчете Expected Shortfall
CHUNK = 30.0
# дальше стольких значений от квантиля хвост дискретного распределения не суммируем
MAX_DISCRETE_TERMS = 2_000_000


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


def _tail_quantile(rv, tail):
    """
    Квантильная функция в хвосте потерь как функция малой вероятности p, со знаком потери:
    для левого хвоста -ppf(p), для правого isf(p). isf точнее, чем ppf(1 - p), при p порядка 1e-30.
    """
    if tail == LEFT:
        return lambda p: -rv.ppf(p)
    return rv.isf


def expected_shortfall(rv, level, tail=LEFT):
    """
    Expected Shortfall (CVaR) уровня level: средняя потеря в худших 1 - level случаях, то есть среднее
    квантильной функции по хвосту. Возвращается как размер потери.
    :return: число; inf, если среднее в хвосте бесконечно (Коши, Парето с индексом хвоста не больше 1);
             nan, если значение не удалось вычислить
    """
    alpha = 1 - level
    try:
        with warnings.catch_warnings(), np.errstate(all='ignore'):
            warnings.simplefilter('ignore')
            if isinstance(rv.dist, stats.rv_discrete):
                return _discrete_expected_shortfall(rv, alpha, tail)
            return _continuous_expected_shortfall(_tail_quantile(rv, tail), alpha)
    except (ArithmeticError, ValueError, RuntimeError, MemoryError):
        return math.nan


def _continuous_expected_shortfall(quantile, alpha):
    """
    (1 / alpha) * интеграл quantile(p) dp по p от 0 до alpha. Замена p = exp(-u) растягивает хвост:
    интегрируем по u тремя кусками равной длины. У степенного хвоста куски убывают как геометрическая
    прогрессия со знаменателем exp(-длина * (1 - 1 / a)), где a - индекс хвоста. По трем кускам оцениваем знаменатель
    и досуммируем остаток; знаменатель не меньше единицы означает, что интеграл расходится и среднего
    в хвосте нет. Это решается по самому хвосту, а не по среднему распределения, которое SciPy
    для части распределений считает неверно и которое может быть бесконечным из-за другого хвоста.
    """
    start = -math.log(alpha)

    def integrand(u):
        p = math.exp(-u)
        return quantile(p) * p

    # часть распределений считает квантиль в далеком хвосте как ppf(1 - p) и при p меньше 1e-16 теряет
    # точность: тогда интегрируем только до p = 1e-15, более короткими кусками
    width = CHUNK
    if not math.isfinite(quantile(math.exp(-(start + 3 * CHUNK)))):
        width = (-math.log(1e-15) - start) / 3
        if width < 1:
            return math.nan
    chunks = []
    for i in range(3):
        value, _ = integrate.quad(integrand, start + i * width, start + (i + 1) * width, limit=200)
        chunks.append(value)
    if not all(math.isfinite(value) for value in chunks):
        return math.nan
    first, second, third = chunks
    remainder = 0.0
    if abs(third) > 1e-12 * abs(first):
        ratio = abs(third) / abs(second) if second else math.inf
        if ratio >= 0.999:
            return math.inf
        remainder = third * ratio / (1 - ratio)
    return (first + second + third + remainder) / alpha


def _discrete_expected_shortfall(rv, alpha, tail):
    """
    То же среднее квантильной функции для дискретного распределения, точной суммой: значения за квантилем
    входят целиком, сам квантиль - с остатком вероятности до alpha. Сумма идет до значения, за которым
    осталась пренебрежимая вероятность; если до него дальше MAX_DISCRETE_TERMS значений (очень тяжелый
    хвост), возвращается nan: память и время на такую сумму не тратим.
    """
    sign = -1 if tail == LEFT else 1
    quantile = float(rv.ppf(alpha) if tail == LEFT else rv.ppf(1 - alpha))
    beyond = rv.cdf if tail == LEFT else rv.sf   # вероятность значений дальше в хвост, чем аргумент
    span = 64
    while beyond(quantile + sign * span) > 1e-13 * alpha:
        span *= 2
        if span > MAX_DISCRETE_TERMS:
            return math.nan
    values = quantile + sign * np.arange(1, span + 1)
    tail_sum = float(np.sum(values * rv.pmf(values)))
    # вероятность значений строго за квантилем
    mass_beyond = float(rv.cdf(quantile - 1)) if tail == LEFT else float(rv.sf(quantile))
    return sign * (tail_sum + quantile * (alpha - mass_beyond)) / alpha
