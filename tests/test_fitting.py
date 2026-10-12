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


def gamma_data():
    """Скошенные положительные данные из гамма-распределения с параметрами a = 2.5, loc = 1, scale = 2."""
    return stats.gamma(2.5, 1.0, 2.0).rvs(size=500, random_state=1)


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
    result = fitting.fit_distribution('vonmises', gamma_data())
    assert not result.ok and 'не нормирована' in result.skipped


def test_data_outside_the_support_is_rejected():
    result = fitting.fit_distribution('anglit', gamma_data())
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
    results = [fitting.fit_distribution(name, gamma_data()) for name in ('uniform', 'gamma', 'norm')]
    table = fitting.results_table(results)
    assert list(table['Распределение']) == ['gamma', 'norm', 'uniform']
    assert table['ΔAIC'].iloc[0] == 0 and table['AIC'].is_monotonic_increasing


# ---------------- ловушки, найденные проверкой на данных, типичных для риска

RISK_CANDIDATES = ['lognorm', 'genpareto', 'lomax', 'invgamma', 'expon', 'gamma', 'weibull_min', 'norm', 't',
                   'dweibull', 'dgamma', 'beta']


def best_of(data, **kwargs):
    return fitting.ranked([fitting.fit_distribution(name, data, **kwargs) for name in RISK_CANDIDATES])


def test_heavy_tailed_truth_is_not_rejected_by_the_normalisation_check():
    """На равномерной сетке интеграл крутой плотности завышался в разы: верная модель отбрасывалась,
    и побеждало экспоненциальное распределение с квантилем 99.9%, заниженным на порядок."""
    data = stats.lognorm(2.5, 0, 1e4).rvs(2000, random_state=7)
    best = best_of(data)
    assert best[0].name == 'lognorm'
    assert best[0].frozen().ppf(0.999) == pytest.approx(stats.lognorm(2.5, 0, 1e4).ppf(0.999), rel=0.5)


def test_shape_below_one_is_recovered_with_fixed_loc():
    best = best_of(stats.gamma(0.5).rvs(2000, random_state=7), fix_loc=True)
    assert best[0].name == 'gamma'
    assert best[0].parameters['a'] == pytest.approx(0.5, rel=0.1)


@pytest.mark.parametrize('scale', [1.0, 5e4, 1e-3])
def test_fit_does_not_depend_on_the_units_of_the_data(scale):
    """Оптимизатор SciPy на данных в рублях или в долях процента не сходился: подгонка идет по стандартизованным."""
    data = stats.gamma(2, 0, scale).rvs(2000, random_state=7)
    result = fitting.fit_distribution('gamma', data)
    assert result.ok
    assert result.frozen().mean() == pytest.approx(2 * scale, rel=0.1)
    assert best_of(data)[0].name == 'gamma'


def test_unbounded_likelihood_is_rejected():
    """Свободный сдвиг и параметр формы меньше единицы: оптимизатор ставит особенность плотности
    на одно наблюдение и получает сколь угодно большое "правдоподобие"."""
    data = stats.lognorm(1, 0, 1e5).rvs(30, random_state=31)
    results = {name: fitting.fit_distribution(name, data) for name in ('dgamma', 'dweibull', 'gamma', 'lognorm')}
    assert results['lognorm'].ok
    best = fitting.ranked(results.values())
    assert best[0].aic >= results['lognorm'].aic - 2
    assert not results['gamma'].ok and 'не ограничено' in results['gamma'].skipped


def test_one_outlier_does_not_knock_out_the_true_model():
    data = np.append(stats.t(4).rvs(1999, random_state=3) * 0.01, 442.6)
    assert best_of(data)[0].name == 't'


def test_boundary_distributions_survive_standardisation():
    data = stats.expon(3.0, 2.0).rvs(500, random_state=1)
    result = fitting.fit_distribution('expon', data)
    assert result.ok and result.parameters['loc'] == pytest.approx(data.min())


def test_degenerate_parameters_are_flagged():
    data = stats.gamma(2, 0, 5e4).rvs(2000, random_state=7)
    pareto = fitting.fit_distribution('pareto', data)
    assert pareto.ok and 'вырождается' in pareto.note
    assert fitting.fit_distribution('gamma', data).note == ''
    assert 'Замечание' in fitting.results_table([pareto]).columns


# ---------------- данные

@pytest.mark.parametrize('values, expected', [
    (['1,234.56', '983.10', '12,000.00'], [1234.56, 983.10, 12000.0]),
    (['1.234,56', '983,10', '12.000,00'], [1234.56, 983.10, 12000.0]),
    (['1 234,5', '2\u00a0000,25', '10,5'], [1234.5, 2000.25, 10.5]),
    (['(0.05)', '\u22120.02', '0.03'], [-0.05, -0.02, 0.03]),
    (['1,5', '2,25', '3'], [1.5, 2.25, 3.0]),
    (['1e-3', '-2.5E2', '+7'], [0.001, -250.0, 7.0]),
])
def test_number_formats_are_read_correctly(values, expected):
    assert fitting.to_numeric(pd.Series(values)).tolist() == pytest.approx(expected)


def test_many_unparsed_values_are_an_error_not_silent_loss():
    """Раньше из файла молча пропадали все значения, записанные в незнакомом формате."""
    with pytest.raises(fitting.DataError, match='не распознаны'):
        fitting.clean_data(['12', '3%', 'n/a'] * 10)
    # единичный мусор отбрасывается и считается
    data, dropped = fitting.clean_data([*range(100), 'n/a'])
    assert len(data) == 100 and dropped == 1


def test_clean_data_drops_what_is_not_a_number():
    data, dropped = fitting.clean_data(['1.5', '2,5', 'abc', None, '', np.inf, *range(30)])
    assert dropped == 4
    assert 2.5 in data and len(data) == 32


@pytest.mark.parametrize('values, message', [
    ([1, 2, 3], 'не меньше'),
    ([], 'не меньше'),
    (['a', 'b', 'c'] * 10, 'не распознаны'),
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
    data = gamma_data()
    density, edges = fitting.histogram(data)
    best = fitting.ranked([fitting.fit_distribution(name, data) for name in ('gamma', 'norm', 'expon')])
    for mode in ('Dark Mode', 'Light Mode'):
        fig = fit_figure(density, edges, best, mode)
        assert fig.axes[0].get_legend_handles_labels()[1] == ['Данные', *[result.name for result in best]]
        qq_figure(data, best[0], mode)
    plt.close('all')


@pytest.mark.parametrize('fix_loc', [False, True])
def test_exported_script_reproduces_the_fit(monkeypatch, tmp_path, capsys, fix_loc):
    data = gamma_data()
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
    # пример данных - доходности из распределения Стьюдента: оно и должно победить, а нормальное явно проиграть
    assert table['Распределение'].iloc[0] == fitting.EXAMPLE_DISTRIBUTION
    assert table[table['Распределение'] == 'norm']['ΔAIC'].iloc[0] > 10
    assert len(table) >= 8
    assert [tab.label for tab in at.tabs] == ['Сравнение', 'Графики', 'Калькулятор', 'Экспорт']
    assert [button.label for button in at.download_button] == ['Таблица результатов (CSV)', 'Данные (data.csv)',
                                                               'Скрипт Python']
    assert 'stats.t.fit(data)' in at.code[0].value
    # калькулятор считает меры риска подобранного распределения: дневной VaR 99% порядка нескольких процентов
    assert 0.01 < float(widget(at.metric, 'VaR 99.0%').value) < 0.10

    # смена отображения не сбрасывает результаты
    widget(at.radio, 'Режим фигуры').set_value('Light Mode').run()
    assert not at.exception and at.dataframe[0].value['Распределение'].iloc[0] == 't'

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
    # настоящая модель неотличима от лучшей: никакой "победитель" не обгоняет ее заметно
    assert table[table['Распределение'] == fitting.EXAMPLE_DISTRIBUTION]['ΔAIC'].iloc[0] < 2
