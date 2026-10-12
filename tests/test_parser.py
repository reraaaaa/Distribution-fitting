import pytest
from scipy import stats

from ParsDistributions import DistributionParser


@pytest.fixture(scope='module')
def parser():
    return DistributionParser('continuous')


def test_lists_are_aligned(parser):
    count = len(parser.get_distribution_names())
    assert count > 80
    assert len(parser.get_distributions()) == count
    assert len(parser.get_distribution_urls()) == count
    assert len(parser.get_distribution_docstrings()) == count
    assert len(parser.get_distribution_functions()) == count
    names, values = parser.get_distribution_parameters()
    assert len(names) == len(values) == count


def test_every_name_exists_in_installed_scipy(parser):
    for name in parser.get_distribution_names():
        assert isinstance(getattr(stats, name), stats.rv_continuous), name


def test_url_belongs_to_its_distribution(parser):
    url_dic = parser.get_dictionaries()['url_dic']
    for name, (url, fullname) in url_dic.items():
        assert url.endswith(f'continuous_{name}.html'), (name, url)
        assert fullname == parser.get_dictionaries()['fullname_dic'][name]


def test_parameters_are_shapes_then_loc_scale(parser):
    parameters_dic = parser.get_dictionaries()['parameters_dic']
    for name, params in parameters_dic.items():
        dist = getattr(stats, name)
        shapes = [sh.strip() for sh in dist.shapes.split(',')] if dist.shapes else []
        assert list(params) == shapes + ['loc', 'scale'], name
        assert params['loc'] == '0.00' and params['scale'] == '1.00'


def test_default_parameters_are_valid(parser):
    parameters_dic = parser.get_dictionaries()['parameters_dic']
    for name, params in parameters_dic.items():
        *shapes, loc, scale = [float(value) for value in params.values()]
        assert getattr(stats, name)._argcheck(*shapes), name


def test_discrete_parser_builds_dictionaries():
    parser = DistributionParser('discrete')
    parameters_dic = parser.get_dictionaries()['parameters_dic']
    assert 'binom' in parameters_dic
    assert list(parameters_dic['binom']) == ['n', 'p', 'loc']
    for name in parser.get_distribution_names():
        assert isinstance(getattr(stats, name), stats.rv_discrete), name


def test_network_failure_is_reported(monkeypatch):
    import requests

    def broken_get(url, **kwargs):
        raise requests.ConnectionError('offline')

    monkeypatch.setattr('ParsDistributions.parser.requests.get', broken_get)
    with pytest.raises(ConnectionError, match='Failed to get URL'):
        DistributionParser('continuous')
