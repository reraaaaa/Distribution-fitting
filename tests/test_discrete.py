"""Дискретные распределения: расчеты и страница."""
import matplotlib.pyplot as plt
import numpy as np
import pytest
from scipy import stats
from streamlit.testing.v1 import AppTest

from ParsDistributions import DistributionParser
from UtilitySt import CodeGenerator, InvalidParameters, parameter_range, risk, sample_distribution

SELECT_LABEL = 'Нажмите ниже (или введите), чтобы выбрать распределение'


def discrete_page():
    from app_pages import p_discrete
    p_discrete()


@pytest.fixture(scope='module')
def distributions():
    return DistributionParser('discrete').distributions


def widget(collection, label):
    found = [w for w in collection if w.label == label]
    assert len(found) == 1, (label, [w.label for w in collection])
    return found[0]


def test_every_discrete_distribution_samples_and_exports(monkeypatch, distributions):
    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)
    assert len(distributions) >= 15
    for name, info in distributions.items():
        sample = sample_distribution(name, info.parameters)
        assert np.all(sample.x == np.round(sample.x)) and np.all(sample.r == np.round(sample.r)), name
        namespace = {}
        exec(compile(CodeGenerator(name, info.parameters).get_generated_code(), f'<generated {name}>', 'exec'),
             namespace)
        plt.close('all')
        # скрипт воспроизводит выборку и сетку приложения
        assert np.array_equal(namespace['r'], sample.r) and np.array_equal(namespace['x'], sample.x), name


def test_slider_extremes_never_crash(distributions):
    for name, info in distributions.items():
        for param, default in info.parameters.items():
            bounds = parameter_range(name, param, default, 0.10)
            assert bounds.min_value <= default <= bounds.max_value, (name, param)
            for value in (bounds.min_value, bounds.max_value):
                try:
                    sample_distribution(name, {**info.parameters, param: value})
                except InvalidParameters:
                    pass


def test_integer_parameters():
    # сдвиг дискретного распределения целый
    assert parameter_range('binom', 'loc', 0.0, 0.10).is_integer
    assert parameter_range('binom', 'n', 5.0, 0.10).is_integer
    assert not parameter_range('binom', 'p', 0.4, 0.10).is_integer
    # SciPy называет n у nbinom целым, но значение по умолчанию дробное: принимаем любое
    assert not parameter_range('nbinom', 'n', 0.4, 0.10).is_integer
    with pytest.raises(InvalidParameters, match='целым'):
        sample_distribution('binom', {'n': 5.5, 'p': 0.4, 'loc': 0.0})
    with pytest.raises(InvalidParameters, match='целым'):
        sample_distribution('poisson', {'mu': 2.0, 'loc': 0.5})


def test_tail_too_heavy_to_compute_is_rejected_quickly():
    with pytest.raises(InvalidParameters, match='хвост'):
        sample_distribution('zipf', {'a': 1.1, 'loc': 0.0})


@pytest.mark.parametrize('rv', [stats.poisson(3.0), stats.binom(20, 0.3), stats.geom(0.2)])
def test_discrete_expected_shortfall_is_the_tail_average_of_quantiles(rv):
    u = (np.arange(400_000) + 0.5) / 400_000
    for level in risk.RISK_LEVELS:
        right = rv.ppf(u[u > level]).mean()
        left = -rv.ppf(u[u < 1 - level]).mean()
        assert risk.expected_shortfall(rv, level, risk.RIGHT) == pytest.approx(right, rel=2e-3, abs=2e-3)
        assert risk.expected_shortfall(rv, level, risk.LEFT) == pytest.approx(left, rel=2e-3, abs=2e-3)
        assert risk.expected_shortfall(rv, level, risk.RIGHT) >= risk.value_at_risk(rv, level, risk.RIGHT)


def test_page_renders_every_discrete_distribution(distributions):
    at = AppTest.from_function(discrete_page, default_timeout=300).run()
    assert not at.exception
    for name in distributions:
        widget(at.selectbox, SELECT_LABEL).select(name).run()
        assert not at.exception, (name, [str(e.value) for e in at.exception])
        assert [tab.label for tab in at.tabs] == ['График', 'Калькулятор', 'Статистика', 'Код'], name
        assert len(at.code) == 1 and len(at.dataframe) == 1, name


def test_page_controls_for_binomial():
    at = AppTest.from_function(discrete_page, default_timeout=300).run()
    widget(at.selectbox, SELECT_LABEL).select('binom').run()
    n = [s for s in at.slider if ': n =' in s.label][0]
    assert isinstance(n.value, int)
    n.set_value(8).run()
    assert not at.exception and at.query_params['n'] == '8'
    # вместо плотности - вероятности значений, блочной диаграммы и Shine нет
    labels = [checkbox.label for checkbox in at.checkbox]
    assert 'PMF' in labels and 'PDF' not in labels and 'Shine' not in labels
    for label in ('CDF', 'P(X<=x)', 'SF', 'Q1', '1σ'):
        widget(at.checkbox, label).check().run()
        assert not at.exception, label
    widget(at.checkbox, 'PMF').uncheck().run()
    widget(at.checkbox, 'Частоты в выборке').uncheck().run()
    assert not at.exception
    # квантиль биномиального распределения - целое число
    quantile = float(widget(at.metric, 'Квантиль: x, при котором P(X ≤ x) = p').value)
    assert quantile == stats.binom(8, 0.4).ppf(0.95)
