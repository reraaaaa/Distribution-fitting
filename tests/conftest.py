"""Общие настройки тестов: документация SciPy подменяется сохраненными страницами, сеть не нужна."""
import os
import sys
from pathlib import Path

import pytest
import requests

os.environ.setdefault('MPLBACKEND', 'Agg')

ROOT = Path(__file__).resolve().parent.parent
FIXTURES = Path(__file__).resolve().parent / 'fixtures'
sys.path.insert(0, str(ROOT))


class FakeResponse:
    def __init__(self, text):
        self.text = text

    def raise_for_status(self):
        pass


def fake_get(url, **kwargs):
    path = FIXTURES / url.rsplit('/', 1)[-1]
    if not path.exists():
        raise requests.ConnectionError(f'No fixture for {url}')
    return FakeResponse(path.read_text(encoding='utf-8'))


def _patch_docs(monkeypatch):
    monkeypatch.setattr('ParsDistributions.parser.requests.get', fake_get)
    monkeypatch.chdir(ROOT)


@pytest.fixture(autouse=True, scope='session')
def offline_scipy_docs():
    monkeypatch = pytest.MonkeyPatch()
    _patch_docs(monkeypatch)
    yield
    monkeypatch.undo()


def continuous_names():
    from ParsDistributions import DistributionParser

    monkeypatch = pytest.MonkeyPatch()
    _patch_docs(monkeypatch)
    try:
        return DistributionParser('continuous').get_distribution_names()
    finally:
        monkeypatch.undo()


def pytest_generate_tests(metafunc):
    if 'distribution' in metafunc.fixturenames:
        metafunc.parametrize('distribution', continuous_names())
