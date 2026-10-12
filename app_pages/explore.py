# -*- coding: utf-8 -*-
"""
Created on 03/01/2022
Aauthor: D-one
"""
import math
import time

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import streamlit as st

from ParsDistributions import DistributionParser
from UtilitySt import (
    DEFAULT_SEED,
    NUMERIC_ERRORS,
    CodeGenerator,
    DisplaySettings,
    Figure,
    InvalidParameters,
    discrete_figure,
    is_discrete,
    parameter_range,
    sample_distribution,
)

from .calculator import show_calculator

# Режимы ввода параметров: подпись в интерфейсе -> шаг ползунка (None - ручной ввод)
PARAMETER_MODES = {
    'Интервал шага ползунка: 0.10': 0.10,
    'Интервал шага ползунка: 0.01': 0.01,
    'Ручной ввод значений параметров': None,
}


# Как параметры loc и scale входят в плотность любого распределения SciPy
LOC_SCALE_FORM = (r'f(x;\ \mathrm{loc}, \mathrm{scale}) = '
                  r'\frac{1}{\mathrm{scale}}\, f\!\left(\frac{x - \mathrm{loc}}{\mathrm{scale}}\right)')

# Привычная запись плотности для распределений, которые принято параметризовать иначе, чем в SciPy
FAMILIAR_FORMS = {
    'norm': ('Для нормального распределения loc - это среднее μ, а scale - стандартное отклонение σ:',
             r'f(x;\ \mu, \sigma) = \frac{1}{\sigma\sqrt{2\pi}} '
             r'\exp\!\left(-\frac{(x - \mu)^2}{2\sigma^2}\right)'),
}


@st.cache_resource(show_spinner='Загрузка списка распределений из документации SciPy...')
def load_distributions(type_rv):
    """
    Парсер ходит в сеть, поэтому запускаем его один раз, а не при каждом перезапуске скрипта.
    :return: {имя в scipy.stats: DistributionInfo}
    """
    return DistributionParser(type_rv=type_rv).distributions


def parameter_label(param, default):
    return f'Значение по умолчанию: {param} = {default}'


@st.cache_resource(max_entries=64, show_spinner='Генерация выборки...')
def cached_sample(name, parameters, seed):
    """
    Выборка зависит только от распределения, параметров и зерна, поэтому не пересчитывается,
    когда пользователь меняет настройки отображения (у некоторых распределений генерация занимает десятки секунд).
    """
    return sample_distribution(name, parameters, seed=seed)


def shared_value(info, param):
    """
    Начальное значение параметра: из ссылки, если она открыта для этого распределения, иначе по умолчанию из SciPy.
    """
    if st.query_params.get('dist') == info.name:
        try:
            value = float(st.query_params.get(param, ''))
        except ValueError:
            value = math.nan
        if math.isfinite(value):
            return value
    return info.parameters[param]


def parameter_slider(info, param, step):
    """
    Ползунок параметра. Границы - область определения параметра из SciPy вокруг значения по умолчанию,
    расширенная так, чтобы значение из ссылки в нее попадало.
    """
    default = info.parameters[param]
    value = shared_value(info, param)
    bounds = parameter_range(info.name, param, default, step)
    low, high = min(bounds.min_value, value), max(bounds.max_value, value)
    key = f'{info.name}:{param}:{step}'
    if bounds.is_integer:
        return st.slider(parameter_label(param, default), min_value=int(low), value=int(round(value)),
                         max_value=int(high), step=1, key=key)
    return st.slider(parameter_label(param, default), min_value=low, value=value, max_value=high, step=step,
                     key=key)


def parameter_controls(info):
    """
    Создает ползунки (или поля ввода) для каждого параметра выбранного распределения.
    Начальные значения - параметры по умолчанию из SciPy или значения из открытой ссылки.
    :return: {'a': 3.57, 'loc': 0.0, 'scale': 1.0} - значения, выбранные пользователем
    """
    mode = next(iter(PARAMETER_MODES))
    if st.checkbox("Нажмите, чтобы настроить параметры", value=False):
        mode = st.radio("Доступные параметры:", tuple(PARAMETER_MODES))
    step = PARAMETER_MODES[mode]

    parameters = {}
    for param, default in info.parameters.items():
        if step is None:
            parameters[param] = st.number_input(parameter_label(param, default), value=shared_value(info, param),
                                                format='%.4f', key=f'{info.name}:{param}:manual')
        else:
            parameters[param] = parameter_slider(info, param, step)
    return parameters


def share_state(name, parameters):
    """
    Записывает распределение и параметры в адрес страницы: ссылка из адресной строки открывает тот же график.
    """
    st.query_params.from_dict({'dist': name, **{param: f'{value:g}' for param, value in parameters.items()}})


def show_equation(info):
    """
    SciPy записывает плотность в стандартной форме, без сдвига и масштаба. Показываем ее и то,
    как в нее входят loc и scale, а для нормального распределения - еще и привычную запись через μ и σ.
    """
    st.latex(info.equation)
    if is_discrete(info.name):
        st.caption('Это вероятность значения k в стандартной форме из документации SciPy: loc = 0. '
                   'Со сдвигом вероятность значения k равна f(k - loc).')
        return
    st.caption('Это стандартная форма из документации SciPy: loc = 0, scale = 1. '
               'Со сдвигом и масштабом плотность равна:')
    st.latex(LOC_SCALE_FORM)
    if info.name in FAMILIAR_FORMS:
        note, equation = FAMILIAR_FORMS[info.name]
        st.caption(note)
        st.latex(equation)


def sample_seed():
    """
    Зерно генератора выборки. Выборка не меняется при перезапусках скрипта, пока пользователь не попросит новую.
    """
    if 'sample_seed' not in st.session_state:
        st.session_state.sample_seed = DEFAULT_SEED
    if st.button('Новая выборка', help='Сгенерировать другую случайную выборку с теми же параметрами'):
        st.session_state.sample_seed += 1
    return st.session_state.sample_seed


def curve_controls(label, shine_key, value):
    """
    Галочка линии и, если линия включена, галочка эффекта Shine рядом с ней.
    :return: (показывать линию, показывать Shine)
    """
    line_column, shine_column = st.columns(2)
    with line_column:
        show = st.checkbox(label, value=value)
    shine = False
    if show:
        with shine_column:
            shine = st.checkbox('Shine', value=True, key=shine_key)
    return show, shine


def display_controls(sample, discrete=False):
    """
    Настройки отображения рисунка.
    :param sample: Sample или None, если с текущими параметрами распределение построить нельзя
    :param discrete: дискретное распределение: вместо плотности вероятности значений (PMF),
                     без эффекта Shine и блочной диаграммы
    :return: DisplaySettings
    """
    st.markdown("**Выберите режим фигуры:**")
    plot_mode = st.radio("Опции", ('Dark Mode', 'Light Mode'))
    st.markdown("**Что показать на рисунке?**")
    if discrete:
        histogram = st.checkbox('Частоты в выборке', value=True)
        pdf, pdf_shine = st.checkbox('PMF', value=True), False
        cdf, cdf_shine = st.checkbox('CDF', value=False), False
    else:
        histogram = st.checkbox('Гистограмма', value=True)
        pdf, pdf_shine = curve_controls('PDF', 'pdf_shine', value=True)
        cdf, cdf_shine = curve_controls('CDF', 'cdf_shine', value=False)

    mark_p = False
    x_cdf = None
    if cdf and sample is not None:
        mark_p = st.checkbox('P(X<=x)', value=False)
        if mark_p:
            # Границы и шаг - от диапазона графика: он бывает и 0.001, и 1e6
            x_min, x_max = float(sample.x[0]), float(sample.x[-1])
            if discrete and x_min < x_max:
                x_cdf = float(st.slider('Установите значение x, чтобы получить: (x, P(X<=x))',
                                        min_value=int(x_min), value=int(sample.rv.median()), max_value=int(x_max),
                                        step=1, key='discrete:x_cdf'))
            elif discrete:
                x_cdf = x_min
            else:
                x_cdf = st.slider('Установите значение x, чтобы получить: (x, P(X<=x))',
                                  min_value=x_min,
                                  value=min(max(float(sample.rv.median()), x_min), x_max),
                                  max_value=x_max,
                                  step=(x_max - x_min) / 200,
                                  format='%.4g')

    if discrete:
        sf, sf_shine, boxplot = st.checkbox('SF', value=False), False, False
    else:
        sf, sf_shine = curve_controls('SF', 'sf_shine', value=False)
        boxplot = st.checkbox('Блочная диаграмма', value=True)

    st.markdown("**Показать квартили распределения:**")
    quantiles = tuple(column.checkbox(f'Q{i}', value=False)
                      for i, column in enumerate(st.columns(3), start=1))

    st.markdown("**Закрасить среднее ± kσ распределения:**")
    sigmas = tuple(column.checkbox(f'{i}σ', value=False)
                   for i, column in enumerate(st.columns(3), start=1))

    settings = DisplaySettings(plot_mode=plot_mode, histogram=histogram,
                               pdf=pdf, pdf_shine=pdf_shine,
                               cdf=cdf, cdf_shine=cdf_shine,
                               sf=sf, sf_shine=sf_shine,
                               mark_p=mark_p, x_cdf=x_cdf,
                               boxplot=boxplot, quantiles=quantiles, sigmas=sigmas)
    return settings


@st.cache_data(max_entries=64, show_spinner='Расчёт статистики...')
def statistics_table(name, parameters, seed):
    """
    Описательная статистика: свойства распределения рядом со значениями по случайной выборке.
    Моменты части распределений SciPy считает численно за секунды, поэтому таблица кэшируется.
    """
    sample = cached_sample(name, parameters, seed)
    rv, r = sample.rv, pd.Series(sample.r)
    with np.errstate(all='ignore'):
        mean, variance, skewness, excess_kurtosis = (float(value) for value in rv.stats(moments='mvsk'))
        q1, median, q3 = rv.ppf([0.25, 0.50, 0.75])
        support_min, support_max = rv.support()
    return pd.DataFrame(
        {
            'Распределение': [mean, np.sqrt(variance), variance, skewness, excess_kurtosis,
                              support_min, q1, median, q3, support_max],
            f'Выборка, n={len(r)}': [r.mean(), r.std(), r.var(), r.skew(), r.kurtosis(),
                                     r.min(), r.quantile(0.25), r.median(), r.quantile(0.75), r.max()],
        },
        index=['Среднее', 'Стандартное отклонение', 'Дисперсия', 'Асимметрия', 'Эксцесс (избыточный)',
               'Минимум', 'Q1 (25%)', 'Медиана (50%)', 'Q3 (75%)', 'Максимум'])


def show_chart(settings, sample, discrete=False):
    figure = Figure(settings=settings, x=sample.x, r=sample.r, rv=sample.rv)
    try:
        if any(settings.sigmas) and not figure.sigma_is_defined():
            st.warning('У этого распределения с такими параметрами среднее или дисперсия не определены '
                       'либо бесконечны, поэтому область ±σ не показана.')
        if discrete:
            st.pyplot(discrete_figure(settings, sample.x, sample.r, sample.rv))
        else:
            st.pyplot(figure.figure_display_control())
    except NUMERIC_ERRORS as e:
        # выборка построилась, но плотность или моменты при таких параметрах SciPy вычислить не смог
        st.warning(f'SciPy не смог вычислить распределение с такими параметрами: {e}. '
                   'Измените значения параметров.')
    finally:
        # Иначе фигуры накапливаются в памяти при каждом перезапуске скрипта
        plt.close('all')


def show_statistics(name, parameters, seed):
    try:
        st.dataframe(statistics_table(name, parameters, seed))
    except NUMERIC_ERRORS as e:
        st.warning(f'SciPy не смог вычислить моменты распределения с такими параметрами: {e}.')
        return
    st.caption('«Распределение» - теоретические значения; nan или inf означает, что величина не определена '
               'или бесконечна. «Выборка» - оценки по случайной выборке, они меняются от выборки к выборке.')


def show_code(name, parameters, seed):
    """
    Показывает сгенерированный скрипт и кнопку, которая его скачивает.
    """
    st.caption('Скрипт строит распределение с выбранными параметрами и ту же выборку, что показана в приложении.')
    code = CodeGenerator(distribution=name, parameters=parameters, seed=seed).get_generated_code()
    st.download_button('Скачать файл Python', data=code,
                       file_name=f'{name}_{time.strftime("%Y%m%d_%H%M%S")}.py',
                       mime='text/x-python', on_click='ignore')
    st.code(code)


def explore_page(type_rv):
    """
    Страница распределений одного вида.
    :param type_rv: 'continuous' или 'discrete'
    """
    discrete = type_rv == 'discrete'
    try:
        distributions = load_distributions(type_rv)
    except Exception as e:
        st.error(f'Не удалось загрузить список распределений из документации SciPy: {e}')
        return

    st.sidebar.subheader("Исследовать")

    with st.sidebar.expander("Выбрать распределение", expanded=True):
        names = list(distributions)
        shared = st.query_params.get('dist')
        name = st.selectbox('Нажмите ниже (или введите), чтобы выбрать распределение', names,
                            index=names.index(shared) if shared in names else 0)
        info = distributions[name]
        st.markdown("**Параметры**")
        parameters = parameter_controls(info)
        seed = sample_seed()
        st.markdown("**SciPy официальная документация:**")
        st.info(f"Подробнее о: [{info.fullname}]({info.url})")
    share_state(name, parameters)

    st.markdown(f"<h1 style='text-align: center;'>{info.fullname}</h1>", unsafe_allow_html=True)

    if info.equation:
        show_equation(info)

    try:
        sample = cached_sample(name, parameters, seed)
    except InvalidParameters as e:
        sample = None
        st.warning(f'С такими параметрами распределение построить нельзя: {e}. Измените значения параметров.')

    with st.sidebar.expander("Настройка отображения"):
        settings = display_controls(sample, discrete)
    st.sidebar.caption('Адрес страницы содержит выбранное распределение и параметры: им можно поделиться.')

    if sample is None:
        return

    chart, calculator, statistics, code = st.tabs(['График', 'Калькулятор', 'Статистика', 'Код'])
    with chart:
        show_chart(settings, sample, discrete)
    with calculator:
        show_calculator(sample.rv, sample.x, settings.plot_mode, key=name, discrete=discrete)
    with statistics:
        show_statistics(name, parameters, seed)
    with code:
        show_code(name, parameters, seed)


def p_explore():
    explore_page('continuous')


def p_discrete():
    explore_page('discrete')
