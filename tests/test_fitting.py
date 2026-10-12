import io

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pytest
from scipy import stats
from streamlit.testing.v1 import AppTest

from UtilitySt import FitCodeGenerator, fit_figure, fitting, qq_figure


def fitting_page():
    from app_pages import p_fitting
    p_fitting()


def widget(collection, label):
    found = [w for w in collection if w.label == label]
    assert len(found) == 1, (label, [w.label for w in collection])
    return found[0]


# ---------------- подгонка

@pytest.mark.parametrize('name, true_parameters', [
    ('norm', {'loc': 3.0, 'scale': 2.0}),
    ('gamma', {'a': 2.5, 'loc': 1.0, 'scale': 2.0}),
    ('lognorm', {'s': 0.5, 'loc': 0.0, 'scale': 3.0}),
])
def test_true_distribution_is_recovered(name, true_parameters):
    data = getattr(stats, name)(*true_parameters.values()).rvs(size=3000, random_state=11)
    results = [fitting.fit_distribution(candidate, data) for candidate in fitting.DEFAULT_DISTRIBUTIONS]
    best = fitting.ranked(results)

    # истинное распределение либо лучшее, либо статистически неотличимо от лучшего
    truth = next(result for result in best if result.name == name)
    assert truth.aic - best[0].aic < 2
    assert name in [result.name for result in best[:3]]
    # оценки параметров близки к истинным
    rv = truth.frozen()
    true_rv = getattr(stats, name)(*true_parameters.values())
    assert rv.mean() == pytest.approx(true_rv.mean(), rel=0.05)
    assert rv.std() == pytest.approx(true_rv.std(), rel=0.10)


def test_quality_measures_are_consistent():
    data = stats.norm(3, 2).rvs(size=500, random_state=1)
    result = fitting.fit_distribution('norm', data)
    log_likelihood = np.sum(stats.norm.logpdf(data, *result.parameters.values()))
    assert result.log_likelihood == pytest.approx(log_likelihood)
    assert result.n_free == 2
    assert result.aic == pytest.approx(2 * 2 - 2 * log_likelihood)
    assert result.bic == pytest.approx(2 * np.log(500) - 2 * log_likelihood)
    assert 0 <= result.ks_statistic <= 1 and 0 <= result.ks_pvalue <= 1


def test_fixed_loc_is_not_counted_as_estimated():
    data = stats.gamma(2.5, scale=2.0).rvs(size=500, random_state=1)
    free = fitting.fit_distribution('gamma', data)
    fixed = fitting.fit_distribution('gamma', data, fix_loc=True)
    assert fixed.parameters['loc'] == 0.0
    assert (free.n_free, fixed.n_free) == (3, 2)


def test_density_that_does_not_integrate_to_one_is_rejected():
    """vonmises - круговое распределение: на данных шире периода его "плотность" интегрируется в несколько единиц
    и по AIC обгоняла бы честные модели."""
    result = fitting.fit_distribution('vonmises', fitting.example_data())
    assert not result.ok and 'не нормирована' in result.skipped


def test_data_outside_the_support_is_rejected():
    result = fitting.fit_distribution('anglit', fitting.example_data())
    assert not result.ok


def test_slow_distribution_is_skipped_instead_of_hanging():
    result = fitting.fit_distribution('studentized_range', fitting.example_data())
    assert not result.ok and 'медленно' in result.skipped


def test_fit_never_raises(monkeypatch):
    def broken(*args, **kwargs):
        raise RuntimeError('optimizer exploded')

    monkeypatch.setattr(stats.norm, 'fit', broken)
    result = fitting.fit_distribution('norm', fitting.example_data())
    assert not result.ok and 'optimizer exploded' in result.skipped


def test_results_table_is_sorted_by_aic():
    results = [fitting.fit_distribution(name, fitting.example_data()) for name in ('uniform', 'gamma', 'norm')]
    table = fitting.results_table(results)
    assert list(table['Распределение']) == ['gamma', 'norm', 'uniform']
    assert table['ΔAIC'].iloc[0] == 0 and table['AIC'].is_monotonic_increasing


# ---------------- данные

def test_clean_data_drops_what_is_not_a_number():
    data, dropped = fitting.clean_data(['1.5', '2,5', 'abc', None, np.inf, *range(10)])
    assert dropped == 3
    assert 2.5 in data and len(data) == 12


@pytest.mark.parametrize('values, message', [
    ([1, 2, 3], 'не меньше'),
    ([], 'не меньше'),
    (['a', 'b', 'c'] * 10, 'не меньше'),
    ([7.0] * 50, 'одинаковы'),
])
def test_unusable_data_is_reported(values, message):
    with pytest.raises(fitting.DataError, match=message):
        fitting.clean_data(values)


@pytest.mark.parametrize('content, columns', [
    (b'value\n' + b'\n'.join(str(i / 10).encode() for i in range(30)), ['value']),
    # без заголовка
    (b'\n'.join(str(i / 10).encode() for i in range(30)), ['Столбец 1']),
    # точка с запятой и десятичная запятая, как в русском Excel
    ('название;вес\n'.encode() + '\n'.join(f'x{i};{i},5' for i in range(30)).encode(), ['вес']),
    # один столбец с десятичной запятой, кодировка Windows-1251
    ('вес\n'.encode('cp1251') + '\n'.join(f'{i},25' for i in range(30)).encode(), ['вес']),
    # обычный CSV с запятой-разделителем: два столбца чисел
    (b'a,b\n' + b'\n'.join(f'{i}.5,{i * 2}'.encode() for i in range(30)), ['a', 'b']),
])
def test_read_table_understands_common_layouts(content, columns):
    table = fitting.read_table(content)
    assert fitting.numeric_columns(table) == columns
    data, _ = fitting.clean_data(table[columns[0]])
    assert len(data) == 30


def test_empty_file_is_reported():
    with pytest.raises(fitting.DataError):
        fitting.read_table(b'')


def test_large_data_is_subsampled_reproducibly():
    data = np.arange(50_000, dtype=float)
    sample = fitting.fitting_sample(data)
    assert len(sample) == fitting.MAX_FIT_OBSERVATIONS
    assert np.array_equal(sample, fitting.fitting_sample(data))
    assert fitting.fitting_sample(data[:100]) is not None and len(fitting.fitting_sample(data[:100])) == 100


def test_discrete_looking_data_is_detected():
    assert fitting.looks_discrete(np.array([1, 2, 3, 2, 1, 5] * 10, dtype=float))
    assert not fitting.looks_discrete(fitting.example_data())


# ---------------- графики и экспорт

def test_figures_draw_for_both_modes():
    data = fitting.example_data()
    density, edges = fitting.histogram(data)
    best = fitting.ranked([fitting.fit_distribution(name, data) for name in ('gamma', 'norm', 'expon')])
    for mode in ('Dark Mode', 'Light Mode'):
        fig = fit_figure(density, edges, best, mode)
        assert fig.axes[0].get_legend_handles_labels()[1] == ['Данные', *[result.name for result in best]]
        qq_figure(data, best[0], mode)
    plt.close('all')


@pytest.mark.parametrize('fix_loc', [False, True])
def test_exported_script_reproduces_the_fit(monkeypatch, tmp_path, capsys, fix_loc):
    data = fitting.example_data()
    result = fitting.fit_distribution('gamma', data, fix_loc=fix_loc)
    np.savetxt(tmp_path / 'data.csv', data, fmt='%.10g')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(plt, 'show', lambda *args, **kwargs: None)

    namespace = {}
    code = FitCodeGenerator(result, fix_loc=fix_loc).get_generated_code()
    exec(compile(code, '<generated fit>', 'exec'), namespace)
    plt.close('all')

    assert list(namespace['parameters']) == pytest.approx(list(result.parameters.values()), rel=1e-4)
    assert namespace['n_free'] == result.n_free
    assert f'AIC = {result.aic:.3f}'[:10] in capsys.readouterr().out


# ---------------- страница

def test_page_fits_the_example_data():
    at = AppTest.from_function(fitting_page, default_timeout=300).run()
    assert not at.exception
    assert not at.dataframe or 'Распределение' not in at.dataframe[0].value.columns

    widget(at.button, 'Подобрать').click().run()
    assert not at.exception
    table = at.dataframe[0].value
    assert table['Распределение'].iloc[0] == 'gamma'
    assert len(table) == len(fitting.DEFAULT_DISTRIBUTIONS)
    assert [button.label for button in at.download_button] == ['Таблица результатов (CSV)', 'Данные (data.csv)',
                                                               'Скрипт Python']
    assert 'stats.gamma.fit(data)' in at.code[0].value

    # смена отображения не сбрасывает результаты
    widget(at.radio, 'Режим фигуры').set_value('Light Mode').run()
    assert not at.exception and at.dataframe[0].value['Распределение'].iloc[0] == 'gamma'

    # смена набора распределений требует нового запуска
    widget(at.toggle, 'Зафиксировать loc = 0').set_value(True).run()
    assert not at.exception
    assert any('нажмите' in info.value for info in at.info)


def upload(at, content, name='data.csv'):
    widget(at.radio, 'Источник данных').set_value('Загрузить файл').run()
    at.file_uploader[0].upload(name, content, 'text/csv').run()
    return at


def test_page_fits_an_uploaded_file():
    data = stats.norm(10, 2).rvs(size=400, random_state=5)
    buffer = io.StringIO()
    pd.DataFrame({'id': [f'row{i}' for i in range(400)], 'value': data}).to_csv(buffer, index=False, sep=';')
    at = upload(AppTest.from_function(fitting_page, default_timeout=300).run(), buffer.getvalue().encode())
    assert not at.exception
    assert widget(at.selectbox, 'Столбец с данными').options == ['value']
    assert at.metric[0].value == '400'

    widget(at.button, 'Подобрать').click().run()
    assert not at.exception
    table = at.dataframe[0].value
    norm = table[table['Распределение'] == 'norm'].iloc[0]
    assert norm['ΔAIC'] < 2


@pytest.mark.parametrize('content', [
    b'',
    b'name\nalpha\nbeta\ngamma\n',
    b'value\n1\n2\n3\n',
    b'\xff\xfe\x00\x01garbage',
])
def test_page_reports_bad_files_without_crashing(content):
    at = upload(AppTest.from_function(fitting_page, default_timeout=300).run(), content)
    assert not at.exception
    assert any('работать нельзя' in error.value for error in at.error)


def test_page_handles_all_distributions_on_small_data():
    at = AppTest.from_function(fitting_page, default_timeout=600).run()
    widget(at.toggle, 'Все распределения').set_value(True).run()
    widget(at.button, 'Подобрать').click().run()
    assert not at.exception
    table = at.dataframe[0].value
    assert len(table) > 60
    # настоящая модель неотличима от лучшей, а ненормированные "победители" отброшены
    assert table[table['Распределение'] == 'gamma']['ΔAIC'].iloc[0] < 2
    assert 'vonmises' not in list(table['Распределение'])
