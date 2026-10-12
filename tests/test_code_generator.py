import matplotlib.pyplot as plt
import numpy as np
import pytest

from UtilitySt import CodeGenerator, sample_distribution


@pytest.mark.parametrize('name, parameters', [
    ('norm', {'loc': 0.0, 'scale': 1.0}),
    ('alpha', {'a': 3.57, 'loc': 0.0, 'scale': 1.0}),
    ('beta', {'a': 2.31, 'b': 0.63, 'loc': -1.5, 'scale': 2.0}),
])
def test_generated_script_runs(monkeypatch, name, parameters):
    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)
    code = CodeGenerator(distribution=name, parameters=parameters, seed=7).get_generated_code()

    assert not code.startswith((' ', '\n')), 'script must not be indented'
    namespace = {}
    exec(compile(code, f'<generated {name}>', 'exec'), namespace)
    plt.close('all')

    # скрипт воспроизводит выборку и сетку, показанные в приложении
    sample = sample_distribution(name, parameters, seed=7)
    assert np.array_equal(namespace['r'], sample.r)
    assert np.array_equal(namespace['x'], sample.x)
    for param, value in parameters.items():
        assert namespace[param] == value
