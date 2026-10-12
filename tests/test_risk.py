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


def test_interval_probability():
    rv = stats.norm()
    assert risk.interval_probability(rv, -1.96, 1.96) == pytest.approx(0.95, abs=1e-3)
    assert risk.interval_probability(rv, 1, 1) == 0.0
    assert risk.interval_probability(rv, 2, 1) == 0.0
