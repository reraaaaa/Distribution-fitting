"""
Подбор закона распределения по данным пользователя.
"""
import hashlib
import io
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from UtilitySt import FitCodeGenerator, data_figure, fit_figure, fitting, qq_figure, risk

from .calculator import TAILS, show_calculator
from .explore import load_distributions

EXAMPLE_SOURCE = 'Пример данных'
FILE_SOURCE = 'Загрузить файл'


@st.cache_data(show_spinner=False, max_entries=2000)
def cached_fit(name, data, fix_loc):
    """
    Подгонка одного распределения. Кэш по данным и настройкам: повторный запуск и смена настроек
    отображения не пересчитывают уже подобранное.
    """
    return fitting.fit_distribution(name, data, fix_loc=fix_loc)


def load_values():
    """
    Источник данных в боковой панели.
    :return: значения для подбора или None, если файл еще не выбран
    :raises fitting.DataError: если файл не читается или в нем нет чисел
    """
    source = st.radio('Источник данных', (EXAMPLE_SOURCE, FILE_SOURCE))
    if source == EXAMPLE_SOURCE:
        parameters = ', '.join(f'{param} = {value}' for param, value in fitting.EXAMPLE_PARAMETERS.items())
        st.caption(f'Модельные дневные доходности: 750 случайных чисел из распределения Стьюдента ({parameters}). '
                   'Хвосты у него тяжелее, чем у нормального.')
        return fitting.example_data()

    uploaded = st.file_uploader('Файл CSV или TXT', type=['csv', 'txt'],
                                help='Один или несколько столбцов чисел. Разделитель столбцов определяется '
                                     'автоматически, десятичным разделителем может быть точка или запятая. '
                                     'Одиночная запятая считается десятичной: файл из двух столбцов целых чисел '
                                     'сохраняйте с точкой с запятой или табуляцией между столбцами.')
    if uploaded is None:
        return None
    table = fitting.read_table(uploaded.getvalue())
    columns = fitting.numeric_columns(table)
    if not columns:
        raise fitting.DataError(f'в файле нет столбца, где хотя бы {fitting.MIN_OBSERVATIONS} чисел')
    column = st.selectbox('Столбец с данными', columns)
    return table[column]


def run_fits(names, sample, fix_loc):
    """
    Подбирает распределения по очереди и показывает прогресс.
    """
    progress = st.progress(0.0, text='Подбор распределений...')
    results = []
    for i, name in enumerate(names):
        progress.progress(i / len(names), text=f'Подбор: {name} ({i + 1} из {len(names)})')
        results.append(cached_fit(name, sample, fix_loc))
    progress.empty()
    return results


def show_data(data, dropped, sample):
    """
    Сводка по данным и предупреждения о том, что влияет на подбор.
    """
    observations, removed, used = st.columns(3)
    observations.metric('Наблюдений', len(data))
    removed.metric('Отброшено значений', dropped, help='Пустые и нечисловые значения')
    used.metric('Используется для подбора', len(sample))
    if len(sample) < len(data):
        st.info(f'Данных больше {fitting.MAX_FIT_OBSERVATIONS}: параметры подбираются по случайной подвыборке '
                f'из {len(sample)} наблюдений.')
    if fitting.looks_discrete(data):
        st.warning('Все значения целые, и разных значений меньше 20. Похоже на дискретную величину: '
                   'непрерывные распределения описывают такие данные плохо, а показатели качества подгонки '
                   'будут вводить в заблуждение.')


def show_comparison(results):
    """
    Вкладка «Сравнение»: таблица подобранных распределений и список неподобранных.
    """
    st.dataframe(fitting.results_table(results), hide_index=True)
    st.caption(
        'Таблица отсортирована по AIC: чем меньше, тем лучше; критерий штрафует за лишние параметры. '
        'ΔAIC - отставание от лучшего: при ΔAIC меньше 2 модели практически неразличимы, больше 10 - явно хуже. '
        'KS и AD - статистики Колмогорова - Смирнова и Андерсона - Дарлинга: расхождение между данными '
        'и подобранным распределением, меньше - лучше; AD сильнее реагирует на хвосты. '
        'p-значения для них считаются на вкладке «Проверка согласия». '
        'SSE зависит от разбиения гистограммы и приведён для справки. '
        'На малых выборках (десятки наблюдений) разница в AIC в несколько единиц ненадёжна. '
        'Лучшее из подобранных - не обязательно верное: выбор модели остаётся за вами.'
    )
    skipped = [result for result in results if not result.ok]
    if skipped:
        with st.expander(f'Не подобрано: {len(skipped)}'):
            st.dataframe(pd.DataFrame({'Распределение': [result.name for result in skipped],
                                       'Причина': [result.skipped for result in skipped]}), hide_index=True)


def show_figures(best, chosen, sample, density, edges, top_n, plot_mode):
    """
    Вкладка «Графики»: гистограмма с лучшими плотностями и Q-Q график выбранного распределения.
    """
    st.markdown(f'##### Данные и {min(top_n, len(best))} лучших по AIC')
    st.pyplot(fit_figure(density, edges, best[:top_n], plot_mode))
    plt.close('all')

    st.markdown(f'##### Q-Q график: {chosen.name}')
    st.pyplot(qq_figure(sample, chosen, plot_mode))
    plt.close('all')
    st.caption('Точки на диагонали - распределение описывает данные и в центре, и в хвостах. '
               'Уход точек от диагонали по краям показывает, что хвосты у данных тяжелее или легче.')


@st.cache_data(show_spinner='Моделирование для проверки согласия...', max_entries=200)
def cached_goodness_of_fit(result, sample, fix_loc, n_simulations):
    return fitting.goodness_of_fit(result, sample, fix_loc=fix_loc, n_simulations=n_simulations)


@st.cache_data(show_spinner='Бутстреп параметров...', max_entries=200)
def cached_bootstrap(result, sample, fix_loc, n_resamples):
    return fitting.bootstrap_parameters(result, sample, fix_loc=fix_loc, n_resamples=n_resamples)


def requested(key, label):
    """
    Кнопка тяжелого расчета. Нажатие запоминается для этого набора данных и настроек, чтобы результат
    не исчезал при следующем действии на странице.
    """
    if st.button(label, key=f'{key}:button'):
        st.session_state[key] = True
    return st.session_state.get(key, False)


def show_goodness_of_fit(chosen, sample, fix_loc, signature):
    """
    Вкладка «Проверка согласия»: p-значения критериев KS и AD методом Монте-Карло.
    """
    st.markdown(f'##### Согласуются ли данные с распределением {chosen.name}?')
    st.caption(
        'Табличные p-значения здесь неприменимы: они предполагают, что параметры известны заранее, '
        'а мы оценили их по тем же данным, и таблицы дают завышенные значения. Поэтому распределение статистик '
        'получаем моделированием: из подобранного распределения генерируются выборки того же объёма, '
        'на каждой параметры оцениваются заново.'
    )
    n_simulations = st.select_slider('Число модельных выборок', options=(100, 200, 500), value=200,
                                     key='gof:simulations')
    if not requested(f'gof:{signature}:{chosen.name}:{n_simulations}', 'Рассчитать p-значения'):
        st.info('Расчёт занимает от секунд до минут: распределение подбирается на каждой модельной выборке.')
        return
    try:
        result = cached_goodness_of_fit(chosen, sample, fix_loc, n_simulations)
    except fitting.DataError as e:
        st.warning(f'Проверку выполнить не удалось: {e}.')
        return
    ks_column, ad_column = st.columns(2)
    ks_column.metric('Колмогоров - Смирнов: p-значение', f'{result.ks_pvalue:.3f}',
                     help=f'Статистика {result.ks_statistic:.4f}. Чувствителен к расхождению в середине.')
    ad_column.metric('Андерсон - Дарлинг: p-значение', f'{result.ad_pvalue:.3f}',
                     help=f'Статистика {result.ad_statistic:.4f}. Чувствителен к расхождению в хвостах.')
    # два критерия сразу: порог 0.025 на каждый дает общий уровень значимости около 0.05
    if min(result.ks_pvalue, result.ad_pvalue) < 0.025:
        st.warning('p-значение меньше 0.025 (порог 0.05 с поправкой на два критерия): данные плохо согласуются '
                   'с этим распределением. Для мер риска важнее критерий Андерсона - Дарлинга: он проверяет хвосты.')
    else:
        st.success('Оба p-значения не меньше 0.025 (порог 0.05 с поправкой на два критерия): данные '
                   'не противоречат этому распределению. '
                   'Это не доказательство того, что оно верное: на малых выборках критерии слабо '
                   'различают близкие модели.')
    st.caption(f'Использовано модельных выборок: {result.simulations}. Наименьшее возможное p-значение при '
               f'таком числе выборок - {1 / (result.simulations + 1):.3f}.')


def show_intervals(chosen, sample, fix_loc, signature):
    """
    Вкладка «Интервалы параметров»: бутстреп-интервалы для параметров и для VaR.
    """
    st.markdown(f'##### Насколько точны оценки для {chosen.name}?')
    st.caption(
        'Точечная оценка выглядит одинаково убедительно на 30 наблюдениях и на 30 000. Доверительный интервал '
        'показывает, насколько она изменилась бы на другой выборке того же объёма. Бутстреп: из данных '
        'многократно берётся выборка с возвращением, и распределение подбирается заново.'
    )
    if chosen.note:
        st.warning(f'У этой подгонки {chosen.note}. Интервалы для таких параметров огромны и мало что значат; '
                   'смотрите на интервал для VaR или выберите более простое распределение.')
    if not fix_loc and min(abs(chosen.parameters['loc'] - sample.min()),
                           abs(chosen.parameters['loc'] - sample.max())) < 1e-9 * np.ptp(sample):
        st.warning('Сдвиг loc оценён по крайнему наблюдению. Его бутстреп-интервал односторонний и истинное '
                   'значение не накрывает: настоящая граница может лежать дальше крайнего наблюдения.')
    tail = TAILS[st.radio('VaR считать для', tuple(TAILS), key='ci:tail', horizontal=True)]
    n_resamples = st.select_slider('Число повторных выборок', options=(100, 200, 500), value=200,
                                   key='ci:resamples')
    if not requested(f'ci:{signature}:{chosen.name}:{n_resamples}', 'Построить интервалы'):
        st.info('Расчёт занимает от секунд до минут: распределение подбирается на каждой повторной выборке.')
        return
    try:
        replicates = cached_bootstrap(chosen, sample, fix_loc, n_resamples)
    except fitting.DataError as e:
        st.warning(f'Интервалы построить не удалось: {e}.')
        return
    quantities = {f'VaR {level:.1%}': (lambda rv, level=level: risk.value_at_risk(rv, level, tail))
                  for level in risk.RISK_LEVELS}
    st.dataframe(fitting.interval_table(chosen, replicates, quantities))
    st.caption(f'Процентильные 95%-интервалы по {len(replicates)} повторным выборкам. Широкий интервал означает, '
               'что данных мало, чтобы надёжно оценить эту величину; для VaR высокого уровня это обычное дело.')


def show_export(results, best, sample, fix_loc):
    """
    Вкладка «Экспорт»: таблица, данные и скрипт, повторяющий подгонку лучшего распределения.
    """
    stamp = time.strftime("%Y%m%d_%H%M%S")
    table, data_file, script = st.columns(3)
    table.download_button('Таблица результатов (CSV)',
                          data=fitting.results_table(results).to_csv(index=False).encode('utf-8-sig'),
                          file_name=f'fit_results_{stamp}.csv', mime='text/csv', on_click='ignore')
    buffer = io.StringIO()
    np.savetxt(buffer, sample, fmt='%.10g')
    data_file.download_button('Данные (data.csv)', data=buffer.getvalue(), file_name='data.csv',
                              mime='text/csv', on_click='ignore')
    code = FitCodeGenerator(best[0], fix_loc=fix_loc).get_generated_code()
    script.download_button('Скрипт Python', data=code, file_name=f'fit_{best[0].name}_{stamp}.py',
                           mime='text/x-python', on_click='ignore')
    st.caption(f'Скрипт повторяет подгонку лучшего распределения ({best[0].name}): '
               'читает data.csv из той же папки.')
    st.code(code)


def show_results(results, sample, density, edges, top_n, plot_mode, fix_loc, distributions, signature):
    best = fitting.ranked(results)
    if not best:
        st.warning('Ни одно из выбранных распределений подобрать не удалось.')
        show_comparison(results)
        return

    name = st.selectbox('Распределение для подробного анализа', [result.name for result in best],
                        help='Используется на всех вкладках, кроме «Сравнения» и «Экспорта». '
                             'По умолчанию - лучшее по AIC.')
    chosen = next(result for result in best if result.name == name)
    info = distributions[name]
    parameters = ', '.join(f'{param} = {value:.4g}' for param, value in chosen.parameters.items())
    st.info(f'**{info.fullname}**: {parameters}. [Документация SciPy]({info.url})')

    comparison, figures, goodness, intervals, calculator, export = st.tabs(
        ['Сравнение', 'Графики', 'Проверка согласия', 'Интервалы параметров', 'Калькулятор', 'Экспорт'])
    with comparison:
        show_comparison(results)
    with figures:
        show_figures(best, chosen, sample, density, edges, top_n, plot_mode)
    with goodness:
        show_goodness_of_fit(chosen, sample, fix_loc, signature)
    with intervals:
        show_intervals(chosen, sample, fix_loc, signature)
    with calculator:
        st.caption(f'Расчёты для подобранного распределения {name}.')
        show_calculator(chosen.frozen(), np.linspace(edges[0], edges[-1], 800), plot_mode, key=f'fit:{name}')
    with export:
        show_export(results, best, sample, fix_loc)


def p_fitting():
    try:
        distributions = load_distributions('continuous')
    except Exception as e:
        st.error(f'Не удалось загрузить список распределений из документации SciPy: {e}')
        return

    st.title('Подбор закона распределения')
    st.write('Загрузите свои данные, выберите распределения, и приложение оценит их параметры методом '
             'максимального правдоподобия и сравнит качество подгонки.')

    st.sidebar.subheader("Подбор")
    values, data_error = None, None
    with st.sidebar.expander("Данные", expanded=True):
        try:
            values = load_values()
        except fitting.DataError as e:
            data_error = e

    with st.sidebar.expander("Распределения", expanded=True):
        available = list(distributions)
        if st.toggle('Все распределения', value=False,
                     help=f'Подобрать все {len(available)} распределений. Может занять несколько минут.'):
            names = available
        else:
            names = st.multiselect('Распределения', available,
                                   default=[name for name in fitting.DEFAULT_DISTRIBUTIONS if name in available])
        fix_loc = st.toggle('Зафиксировать loc = 0', value=False,
                            help='Не оценивать сдвиг. Имеет смысл для величин, которые по своей природе '
                                 'начинаются с нуля: длительности, размеры, суммы.')
        requested = st.button('Подобрать', type='primary')

    with st.sidebar.expander("Настройка отображения"):
        plot_mode = st.radio("Режим фигуры", ('Dark Mode', 'Light Mode'))
        top_n = st.slider('Сколько лучших распределений показать на графике', min_value=1, max_value=8, value=3)

    if data_error is not None:
        st.error(f'С этими данными работать нельзя: {data_error}.')
        return
    if values is None:
        st.info('Загрузите файл в боковой панели или выберите пример данных.')
        return
    try:
        data, dropped = fitting.clean_data(values)
    except fitting.DataError as e:
        st.error(f'С этими данными работать нельзя: {e}.')
        return

    sample = fitting.fitting_sample(data)
    density, edges = fitting.histogram(sample)
    show_data(data, dropped, sample)

    # результаты показываются только для тех данных и настроек, для которых нажата кнопка
    signature = (hashlib.sha1(sample.tobytes()).hexdigest(), tuple(names), fix_loc)
    if requested:
        st.session_state.fit_signature = signature
    if st.session_state.get('fit_signature') != signature or not names:
        fig, _ = data_figure(density, edges, plot_mode)
        st.pyplot(fig)
        plt.close('all')
        with st.expander('Описательная статистика данных'):
            st.dataframe(fitting.data_statistics(data))
        if names:
            st.info('Выберите распределения в боковой панели и нажмите «Подобрать».')
        else:
            st.warning('Не выбрано ни одного распределения.')
        return

    results = run_fits(names, sample, fix_loc)
    show_results(results, sample, density, edges, top_n, plot_mode, fix_loc, distributions, signature[0])
    with st.expander('Описательная статистика данных'):
        st.dataframe(fitting.data_statistics(data))
