"""Прогон приложения без браузера через streamlit.testing."""
import matplotlib.pyplot as plt
import numpy as np
import pytest
from streamlit.testing.v1 import AppTest

from tests.conftest import ROOT

SELECT_LABEL = 'Нажмите ниже (или введите), чтобы выбрать распределение'


def explore_page():
    from app_pages import p_explore
    p_explore()


def fitting_page():
    from app_pages import p_fitting
    p_fitting()


def widget(collection, label):
    found = [w for w in collection if w.label == label]
    assert len(found) == 1, (label, [w.label for w in collection])
    return found[0]


def assert_no_errors(at):
    assert not at.exception, [str(e.value) for e in at.exception]
    # Главная использует st.error как цветной заголовок, настоящая ошибка только у парсера
    assert not [e.value for e in at.error if str(e.value).startswith('Не удалось')]


def new_explore_app():
    return AppTest.from_function(explore_page, default_timeout=300).run()


@pytest.fixture(scope='module')
def explore_app():
    return new_explore_app()


def test_entry_point_opens_the_home_page():
    at = AppTest.from_file(str(ROOT / 'streamlit_app.py'), default_timeout=300).run()
    assert_no_errors(at)
    assert [title.value for title in at.title] == ['Distribution Fitting']
    # число распределений берется из той же базы, что и на странице распределений
    assert int(at.metric[0].value) > 80
    assert any('GitHub' in caption.value for caption in at.sidebar.caption)


def test_fitting_page_opens():
    at = AppTest.from_function(fitting_page, default_timeout=300).run()
    assert_no_errors(at)
    assert len(at.info) == 1


def test_distribution_renders_and_exports_runnable_code(explore_app, monkeypatch, distribution):
    at = explore_app
    widget(at.selectbox, SELECT_LABEL).select(distribution).run()
    assert_no_errors(at)

    assert [tab.label for tab in at.tabs] == ['График', 'Калькулятор', 'Статистика', 'Код']
    assert len(at.code) == 1
    assert len(at.download_button) == 1

    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)
    exec(compile(at.code[0].value, f'<generated {distribution}>', 'exec'), {})
    plt.close('all')


def first_slider(at, text):
    return [s for s in at.slider if text in s.label][0]


TOGGLE_STEPS = [
    ('CDF on', lambda at: widget(at.checkbox, 'CDF').check()),
    ('CDF shine off', lambda at: at.checkbox(key='cdf_shine').uncheck()),
    ('P(X<=x) on', lambda at: widget(at.checkbox, 'P(X<=x)').check()),
    ('move x', lambda at: first_slider(at, 'Установите').set_value(first_slider(at, 'Установите').min)),
    ('SF on', lambda at: widget(at.checkbox, 'SF').check()),
    ('SF shine off', lambda at: at.checkbox(key='sf_shine').uncheck()),
    ('Q1', lambda at: widget(at.checkbox, 'Q1').check()),
    ('Q2', lambda at: widget(at.checkbox, 'Q2').check()),
    ('Q3', lambda at: widget(at.checkbox, 'Q3').check()),
    ('1 sigma', lambda at: widget(at.checkbox, '1σ').check()),
    ('2 sigma', lambda at: widget(at.checkbox, '2σ').check()),
    ('3 sigma', lambda at: widget(at.checkbox, '3σ').check()),
    ('light mode', lambda at: widget(at.radio, 'Опции').set_value('Light Mode')),
    ('dark mode', lambda at: widget(at.radio, 'Опции').set_value('Dark Mode')),
    ('PDF shine off', lambda at: at.checkbox(key='pdf_shine').uncheck()),
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
    at = new_explore_app()
    widget(at.selectbox, SELECT_LABEL).select(name).run()
    for label, action in TOGGLE_STEPS:
        action(at)
        at.run()
        assert not at.exception, (label, [str(e.value) for e in at.exception])


def select(at, name):
    widget(at.selectbox, SELECT_LABEL).select(name).run()
    return at


def test_invalid_parameters_show_a_warning_instead_of_crashing():
    at = select(new_explore_app(), 'truncnorm')
    # a должен быть меньше b
    first_slider(at, ': a =').set_value(first_slider(at, ': a =').max).run()
    assert not at.exception
    assert any('построить нельзя' in w.value for w in at.warning)
    # настройки отображения остаются на месте
    assert widget(at.checkbox, 'PDF').value is True


def test_integer_parameter_slider_moves_without_crashing():
    at = select(new_explore_app(), 'ksone')
    slider = first_slider(at, ': n =')
    assert isinstance(slider.value, int)
    slider.set_value(20).run()
    assert not at.exception and not at.warning


def test_statistics_show_theory_next_to_the_sample():
    at = select(new_explore_app(), 'cauchy')
    assert_no_errors(at)
    table = at.dataframe[0].value
    assert list(table.columns) == ['Распределение', 'Выборка, n=400']
    # у распределения Коши среднее не определено, а по выборке число всегда получится
    assert not np.isfinite(table.loc['Среднее', 'Распределение'])
    assert np.isfinite(table.loc['Среднее', 'Выборка, n=400'])
    assert table.loc['Медиана (50%)', 'Распределение'] == pytest.approx(0.0)


def test_sample_is_stable_until_a_new_one_is_requested():
    at = select(new_explore_app(), 'norm')
    column = 'Выборка, n=400'
    first = at.dataframe[0].value[column].copy()

    widget(at.checkbox, 'CDF').check().run()
    assert at.dataframe[0].value[column].equals(first)

    widget(at.button, 'Новая выборка').click().run()
    assert not at.dataframe[0].value[column].equals(first)


def test_sigma_warning_for_undefined_variance():
    at = select(new_explore_app(), 'cauchy')
    widget(at.checkbox, '1σ').check().run()
    assert not at.exception
    assert any('не определены' in w.value for w in at.warning)


def set_step(at, label):
    widget(at.checkbox, 'Нажмите, чтобы настроить параметры').check().run()
    widget(at.radio, 'Доступные параметры:').set_value(label).run()


def test_density_that_scipy_cannot_evaluate_shows_a_warning(monkeypatch):
    # какие именно параметры SciPy не осиливает, зависит от его версии, поэтому отказ имитируем
    def overflow(self):
        raise OverflowError('Error in function boost::math::gamma_p_derivative')

    monkeypatch.setattr('UtilitySt.visual.Figure.figure_display_control', overflow)
    at = select(new_explore_app(), 'norm')
    assert not at.exception
    assert any('SciPy не смог' in w.value for w in at.warning)


def test_probability_marker_works_on_a_very_narrow_distribution():
    at = select(new_explore_app(), 'norm')
    set_step(at, 'Ручной ввод значений параметров')
    [n for n in at.number_input if 'scale' in n.label][0].set_value(0.0001).run()
    widget(at.checkbox, 'CDF').check().run()
    widget(at.checkbox, 'P(X<=x)').check().run()
    assert not at.exception
    slider = first_slider(at, 'Установите')
    assert slider.min < slider.value < slider.max


def test_normal_distribution_shows_the_familiar_formula():
    at = select(new_explore_app(), 'norm')
    formulas = [latex.value for latex in at.latex]
    assert len(formulas) == 3
    assert any('sigma' in formula and 'mu' in formula for formula in formulas)
    assert any('loc' in formula and 'scale' in formula for formula in formulas)


def metric(at, label):
    return widget(at.metric, label).value


def test_shared_link_restores_distribution_and_parameters():
    at = AppTest.from_function(explore_page, default_timeout=300)
    at.query_params['dist'] = 'gamma'
    at.query_params['a'] = '4.5'
    at.query_params['scale'] = '25'
    at.run()
    assert_no_errors(at)
    assert widget(at.selectbox, SELECT_LABEL).value == 'gamma'
    assert first_slider(at, ': a =').value == 4.5
    # значение из ссылки вне обычного диапазона ползунка: диапазон расширяется, а не падает
    assert first_slider(at, 'scale').value == 25.0
    assert first_slider(at, 'loc').value == 0.0


def test_page_address_follows_the_parameters():
    at = select(new_explore_app(), 'norm')
    first_slider(at, 'loc').set_value(-2.5).run()
    assert at.query_params['dist'] == 'norm'
    assert at.query_params['loc'] == '-2.5'
    # параметры из ссылки на другое распределение не подставляются
    select(at, 'gamma')
    assert at.query_params['dist'] == 'gamma' and first_slider(at, 'loc').value == 0.0


def test_broken_link_falls_back_to_defaults():
    at = AppTest.from_function(explore_page, default_timeout=300)
    at.query_params['dist'] = 'no_such_distribution'
    at.query_params['a'] = 'abc'
    at.run()
    assert_no_errors(at)
    at2 = AppTest.from_function(explore_page, default_timeout=300)
    at2.query_params['dist'] = 'gamma'
    at2.query_params['a'] = 'abc'
    at2.run()
    assert_no_errors(at2)
    assert first_slider(at2, ': a =').value == 1.99


def test_calculator_matches_scipy():
    from scipy import stats

    at = select(new_explore_app(), 'norm')
    rv = stats.norm()
    assert float(metric(at, 'P(от < X ≤ до)')) == pytest.approx(0.5, abs=1e-4)
    assert float(metric(at, 'Квантиль: x, при котором P(X ≤ x) = p')) == pytest.approx(rv.ppf(0.95), rel=1e-5)
    # доходность: потери слева, VaR и ES - положительные размеры потери
    assert float(metric(at, 'VaR 99.0%')) == pytest.approx(-rv.ppf(0.01), rel=1e-5)
    assert float(metric(at, 'Expected Shortfall 99.0%')) == pytest.approx(rv.pdf(rv.ppf(0.01)) / 0.01, rel=1e-5)

    widget(at.select_slider, 'Уровень доверия').set_value(0.975).run()
    assert float(metric(at, 'VaR 97.5%')) == pytest.approx(-rv.ppf(0.025), rel=1e-5)


def test_expected_shortfall_is_undefined_without_a_tail_mean():
    at = select(new_explore_app(), 'cauchy')
    assert not at.exception
    assert metric(at, 'Expected Shortfall 99.0%') == 'бесконечно'
    assert float(metric(at, 'VaR 99.0%')) > 0
