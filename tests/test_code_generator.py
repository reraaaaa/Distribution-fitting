import matplotlib.pyplot as plt
import pytest

from UtilitySt import CodeGenerator


@pytest.mark.parametrize('select_distribution, a, name', [
    ('norm', '', ''),
    ('alpha', 'a=3.57', 'a,'),
    ('beta', 'a=2.31\nb=0.63', 'a, b,'),
])
def test_generated_script_runs(monkeypatch, select_distribution, a, name):
    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)
    code = CodeGenerator(select_distribution=select_distribution, scale='scale=1.0', loc='loc=0.0',
                         a=a, name=name).get_generated_code()

    assert not code.startswith((' ', '\n')), 'script must not be indented'
    namespace = {}
    exec(compile(code, f'<generated {select_distribution}>', 'exec'), namespace)
    plt.close('all')

    assert namespace['r'].shape == (400,)
    assert namespace['x'].shape == (400,)
