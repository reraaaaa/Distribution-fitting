import math

import pytest
from scipy import stats

from UtilitySt import risk


@pytest.mark.parametrize('level', risk.RISK_LEVELS)
def test_normal_var_and_es_match_closed_form(level):
    mu, sigma = 0.001, 0.02
    rv = stats.norm(mu, sigma)
    z = stats.norm.ppf(1 - level)
    assert risk.value_at_risk(rv, level) == pytest.approx(-(mu + sigma * z))
    assert risk.expected_shortfall(rv, level) == pytest.approx(sigma * stats.norm.pdf(z) / (1 - level) - mu, rel=1e-6)
    # правый хвост: величина - убыток
    assert risk.value_at_risk(rv, level, risk.RIGHT) == pytest.approx(mu - sigma * z)
    assert risk.expected_shortfall(rv, level, risk.RIGHT) == pytest.approx(
        sigma * stats.norm.pdf(z) / (1 - level) + mu, rel=1e-6)


@pytest.mark.parametrize('df', [1.2, 3, 8])
def test_student_es_matches_closed_form(df):
    level = 0.99
    q = stats.t.ppf(1 - level, df)
    closed = stats.t.pdf(q, df) / (1 - level) * (df + q * q) / (df - 1)
    assert risk.expected_shortfall(stats.t(df), level) == pytest.approx(closed, rel=1e-5)


def test_es_is_not_below_var():
    for rv in (stats.norm(), stats.t(3), stats.lognorm(0.5), stats.gamma(2.0)):
        for tail in (risk.LEFT, risk.RIGHT):
            assert risk.expected_shortfall(rv, 0.975, tail) >= risk.value_at_risk(rv, 0.975, tail)


def test_es_is_infinite_when_the_tail_has_no_mean():
    assert math.isinf(risk.expected_shortfall(stats.cauchy(), 0.99))
    assert math.isinf(risk.expected_shortfall(stats.t(0.9), 0.99, risk.RIGHT))
    # носитель ограничен слева: левый хвост конечен, даже если среднего у распределения нет
    assert math.isfinite(risk.expected_shortfall(stats.levy(), 0.99, risk.LEFT))
    assert math.isinf(risk.expected_shortfall(stats.levy(), 0.99, risk.RIGHT))


def test_tail_is_judged_by_itself_not_by_the_mean_of_the_distribution():
    # SciPy возвращает для invweibull(0.9) среднее -9.7, хотя оно бесконечно: ES не должен стать меньше VaR
    assert math.isinf(risk.expected_shortfall(stats.invweibull(0.9), 0.99, risk.RIGHT))
    # у crystalball среднее бесконечно из-за левого хвоста, а правый хвост гауссов и конечен
    rv = stats.crystalball(1, 1.5)
    right = risk.expected_shortfall(rv, 0.99, risk.RIGHT)
    assert math.isfinite(right) and right >= risk.value_at_risk(rv, 0.99, risk.RIGHT)
    assert math.isinf(risk.expected_shortfall(rv, 0.99, risk.LEFT))


@pytest.mark.parametrize('sigma', [0.5, 2.0, 4.0, 6.0, 8.0])
def test_lognormal_right_tail_es_matches_closed_form(sigma):
    """При sigma от 4 значение раньше объявлялось неопределенным, а при 8 молча занижалось на 93%."""
    level = 0.99
    z = stats.norm.ppf(level)
    closed = math.exp(sigma ** 2 / 2) * stats.norm.cdf(sigma - z) / (1 - level)
    assert risk.expected_shortfall(stats.lognorm(sigma), level, risk.RIGHT) == pytest.approx(closed, rel=1e-4)


@pytest.mark.parametrize('b', [1.01, 1.2, 3.0])
def test_pareto_es_matches_closed_form(b):
    level = 0.99
    var = (1 - level) ** (-1 / b)
    assert risk.expected_shortfall(stats.pareto(b), level, risk.RIGHT) == pytest.approx(var * b / (b - 1), rel=1e-3)
    assert math.isinf(risk.expected_shortfall(stats.pareto(0.95), level, risk.RIGHT))


def test_discrete_es_with_a_heavy_tail_does_not_exhaust_memory():
    assert math.isnan(risk.expected_shortfall(stats.zipf(2.2), 0.99, risk.RIGHT))
    value = risk.expected_shortfall(stats.zipf(4.0), 0.99, risk.RIGHT)
    assert math.isfinite(value) and value >= risk.value_at_risk(stats.zipf(4.0), 0.99, risk.RIGHT)


def test_interval_probability():
    rv = stats.norm()
    assert risk.interval_probability(rv, -1.96, 1.96) == pytest.approx(0.95, abs=1e-3)
    assert risk.interval_probability(rv, 1, 1) == 0.0
    assert risk.interval_probability(rv, 2, 1) == 0.0
