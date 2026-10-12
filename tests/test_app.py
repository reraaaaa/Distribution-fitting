"""Прогон приложения без браузера через streamlit.testing."""
import matplotlib.pyplot as plt
import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import ROOT

EXPLORE = 'База распределений'
SELECT_LABEL = 'Нажмите ниже (или введите), чтобы выбрать распределение'


def widget(collection, label):
    found = [w for w in collection if w.label == label]
    assert len(found) == 1, (label, [w.label for w in collection])
    return found[0]


def assert_no_errors(at):
    assert not at.exception, [str(e.value) for e in at.exception]
    # Главная использует st.error как цветной заголовок, настоящая ошибка только у парсера
    assert not [e.value for e in at.error if str(e.value).startswith('Не удалось')]


def new_app(page=None):
    at = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=300).run()
    if page:
        at.sidebar.radio[0].set_value(page).run()
    return at


@pytest.fixture(scope='module')
def explore_app():
    return new_app(EXPLORE)


def test_every_page_opens():
    at = new_app()
    assert_no_errors(at)
    pages = at.sidebar.radio[0].options
    assert len(pages) == 3
    for page in pages:
        at.sidebar.radio[0].set_value(page).run()
        assert_no_errors(at)


def test_distribution_renders_and_exports_runnable_code(explore_app, monkeypatch, distribution):
    at = explore_app
    widget(at.selectbox, SELECT_LABEL).select(distribution).run()
    assert_no_errors(at)

    widget(at.button, 'Сгенерировать код Python').click().run()
    assert_no_errors(at)
    assert len(at.code) == 1

    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)
    exec(compile(at.code[0].value, f'<generated {distribution}>', 'exec'), {})
    plt.close('all')


def first_slider(at, text):
    return [s for s in at.slider if text in s.label][0]


TOGGLE_STEPS = [
    ('CDF on', lambda at: widget(at.checkbox, 'CDF').check()),
    ('P(X<=x) on', lambda at: widget(at.checkbox, 'P(X<=x)').check()),
    ('move x', lambda at: first_slider(at, 'Установите').set_value(first_slider(at, 'Установите').min)),
    ('SF on', lambda at: widget(at.checkbox, 'SF').check()),
    ('Q1', lambda at: widget(at.checkbox, 'Q1').check()),
    ('Q2', lambda at: widget(at.checkbox, 'Q2').check()),
    ('Q3', lambda at: widget(at.checkbox, 'Q3').check()),
    ('1 sigma', lambda at: widget(at.checkbox, '').check()),
    ('2 sigma', lambda at: widget(at.checkbox, ' ').check()),
    ('3 sigma', lambda at: widget(at.checkbox, '   ').check()),
    ('statistics', lambda at: widget(at.checkbox, 'Да').check()),
    ('light mode', lambda at: widget(at.radio, 'Опции').set_value('Light Mode')),
    ('dark mode', lambda at: widget(at.radio, 'Опции').set_value('Dark Mode')),
    ('PDF off', lambda at: widget(at.checkbox, 'PDF').uncheck()),
    ('histogram off', lambda at: widget(at.checkbox, 'Гистограмма').uncheck()),
    ('CDF off', lambda at: widget(at.checkbox, 'CDF').uncheck()),
    ('SF off', lambda at: widget(at.checkbox, 'SF').uncheck()),
    ('boxplot off', lambda at: widget(at.checkbox, 'Блочная диаграмма').uncheck()),
    ('PDF on', lambda at: widget(at.checkbox, 'PDF').check()),
    ('advanced', lambda at: widget(at.checkbox, 'Нажмите, чтобы настроить параметры').check()),
    ('step 0.01', lambda at: widget(at.radio, 'Доступные параметры:').set_value('Интервал шага ползунка: 0.01')),
    ('manual', lambda at: widget(at.radio, 'Доступные параметры:').set_value('Ручной ввод значений параметров')),
    ('step 0.10', lambda at: widget(at.radio, 'Доступные параметры:').set_value('Интервал шага ползунка: 0.10')),
    ('move loc', lambda at: first_slider(at, 'loc').set_value(-2.5)),
    ('move scale', lambda at: first_slider(at, 'scale').set_value(3.0)),
]


@pytest.mark.parametrize('name', ['norm', 'beta', 'genextreme', 'alpha'])
def test_display_toggles(name):
    at = new_app(EXPLORE)
    widget(at.selectbox, SELECT_LABEL).select(name).run()
    for label, action in TOGGLE_STEPS:
        action(at)
        at.run()
        assert not at.exception, (label, [str(e.value) for e in at.exception])
