import pytest
from scipy import stats

from ParsDistributions import DistributionParser


@pytest.fixture(scope='module')
def distributions():
    return DistributionParser('continuous').distributions


def test_finds_the_continuous_distributions(distributions):
    assert len(distributions) > 80
    assert {'norm', 'beta', 'alpha', 'cauchy'} <= set(distributions)


def test_every_name_exists_in_installed_scipy(distributions):
    for name, info in distributions.items():
        assert info.name == name
        assert isinstance(getattr(stats, name), stats.rv_continuous), name


def test_url_and_docstring_belong_to_the_distribution(distributions):
    for name, info in distributions.items():
        assert info.url.endswith(f'continuous_{name}.html'), (name, info.url)
        assert info.docstring == getattr(stats, name).__doc__
        assert info.fullname


def test_parameters_are_shapes_then_loc_scale(distributions):
    for name, info in distributions.items():
        dist = getattr(stats, name)
        shapes = [sh.strip() for sh in dist.shapes.split(',')] if dist.shapes else []
        assert list(info.parameters) == shapes + ['loc', 'scale'], name
        assert info.parameters['loc'] == 0.0 and info.parameters['scale'] == 1.0


def test_default_parameters_are_valid(distributions):
    for name, info in distributions.items():
        *shapes, loc, scale = info.parameters.values()
        assert getattr(stats, name)._argcheck(*shapes), name


def test_discrete_distributions_have_no_scale():
    distributions = DistributionParser('discrete').distributions
    assert list(distributions['binom'].parameters) == ['n', 'p', 'loc']
    for name in distributions:
        assert isinstance(getattr(stats, name), stats.rv_discrete), name


def test_network_failure_is_reported(monkeypatch):
    import requests

    def broken_get(url, **kwargs):
        raise requests.ConnectionError('offline')

    monkeypatch.setattr('ParsDistributions.parser.requests.get', broken_get)
    with pytest.raises(ConnectionError, match='Failed to get URL'):
        DistributionParser('continuous')


def test_equation_is_the_whole_density_formula(distributions):
    # у t раньше показывалась только нормирующая константа
    assert r'(1+x^2/\nu)^{-(\nu+1)/2}' in distributions['t'].equation
    # у genextreme есть частный случай c = 0 и общий; нужен общий
    assert distributions['genextreme'].equation.startswith('f(x, c)')
    # определение статистики D_n - не плотность
    assert distributions['ksone'].equation == ''
    assert sum(bool(info.equation) for info in distributions.values()) >= 80


def test_equations_are_balanced_latex(distributions):
    for name, info in distributions.items():
        equation = info.equation
        assert equation.count('{') == equation.count('}'), name
        assert equation.count(r'\left') == equation.count(r'\right'), name
        assert equation.count(r'\begin') == equation.count(r'\end'), name
        assert ':math:' not in equation, name


def test_multiline_equation_is_wrapped_for_rendering(distributions):
    equation = distributions['laplace_asymmetric'].equation
    assert equation.startswith(r'\begin{aligned}') and equation.endswith(r'\end{aligned}')
    assert not equation.removesuffix(r'\end{aligned}').rstrip().endswith('\\\\')
    # формулы без выравнивания не трогаем
    assert distributions['norm'].equation.startswith('f(x)')
