import numpy as np
import pytest
from scipy import stats

from ParsDistributions import DistributionParser
from UtilitySt import InvalidParameters, parameter_range, sample_distribution

# плотность или выборка считаются десятки секунд
SLOW = {'studentized_range', 'gausshyper'}


@pytest.fixture(scope='module')
def distributions():
    return DistributionParser('continuous').distributions


def test_same_seed_gives_same_sample():
    parameters = {'loc': 0.0, 'scale': 1.0}
    first = sample_distribution('norm', parameters, seed=1)
    assert np.array_equal(first.r, sample_distribution('norm', parameters, seed=1).r)
    assert not np.array_equal(first.r, sample_distribution('norm', parameters, seed=2).r)
    assert first.r.shape == (400,)


@pytest.mark.parametrize('name, parameters', [
    ('norm', {'loc': 0.0, 'scale': 0.0}),
    ('truncnorm', {'a': 3.0, 'b': 1.0, 'loc': 0.0, 'scale': 1.0}),
    ('ksone', {'n': 1.5, 'loc': 0.0, 'scale': 1.0}),
    ('gamma', {'a': -1.0, 'loc': 0.0, 'scale': 1.0}),
    # квантили: SciPy переполняется на краю области определения
    ('ncf', {'dfn': 27.0, 'dfd': 0.01, 'nc': 0.42, 'loc': 0.0, 'scale': 1.0}),
])
def test_invalid_parameters_are_rejected(name, parameters):
    with pytest.raises(InvalidParameters):
        sample_distribution(name, parameters)


def test_curve_grid_reaches_the_density_peak(distributions):
    for name, info in distributions.items():
        if name in SLOW:
            continue
        sample = sample_distribution(name, info.parameters)
        rv = sample.rv
        dense = np.union1d(np.linspace(sample.x[0], sample.x[-1], 20001), rv.ppf(np.linspace(0.001, 0.999, 20001)))
        with np.errstate(all='ignore'):
            plotted, true = rv.pdf(sample.x), rv.pdf(dense)
        plotted, true = plotted[np.isfinite(plotted)], true[np.isfinite(true)]
        assert plotted.max() >= 0.95 * true.max(), (name, plotted.max(), true.max())


def test_slider_range_contains_the_default(distributions):
    for name, info in distributions.items():
        for param, default in info.parameters.items():
            for step in (0.10, 0.01):
                bounds = parameter_range(name, param, default, step)
                assert bounds.min_value <= default <= bounds.max_value, (name, param)
                assert bounds.min_value < bounds.max_value, (name, param)


def test_slider_range_follows_the_parameter_domain():
    # круглые значения достижимы: сетка начинается с 0.1, а не с 0.01
    assert parameter_range('gamma', 'a', 1.99, 0.10).min_value == 0.1
    # scale строго положителен
    assert parameter_range('norm', 'scale', 1.0, 0.10).min_value == 0.1
    assert parameter_range('norm', 'loc', 0.0, 0.10).min_value == -10.0
    # отрицательные значения допустимы
    assert parameter_range('genpareto', 'c', 0.1, 0.10).min_value < 0
    # ограниченная область: -1 < a < 1
    bounds = parameter_range('skewcauchy', 'a', 0.5, 0.10)
    assert (bounds.min_value, bounds.max_value) == (-0.9, 0.9)
    # целочисленный параметр
    bounds = parameter_range('ksone', 'n', 1000.0, 0.10)
    assert bounds.is_integer and bounds.min_value == 1 and isinstance(bounds.max_value, int)


def test_slider_extremes_never_crash(distributions):
    """На краях ползунка распределение либо строится, либо отклоняется как InvalidParameters."""
    for name, info in distributions.items():
        if name in SLOW:
            continue
        for param, default in info.parameters.items():
            bounds = parameter_range(name, param, default, 0.10)
            for value in (bounds.min_value, bounds.max_value):
                try:
                    sample = sample_distribution(name, {**info.parameters, param: value})
                except InvalidParameters:
                    continue
                assert np.all(np.isfinite(sample.x)) and np.all(np.isfinite(sample.r)), (name, param, value)


def test_sample_follows_the_distribution():
    sample = sample_distribution('norm', {'loc': 2.0, 'scale': 3.0})
    assert stats.kstest(sample.r, sample.rv.cdf).pvalue > 0.01
