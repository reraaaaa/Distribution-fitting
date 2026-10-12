# -*- coding: utf-8 -*-
"""
Created on 03/01/2022
Aauthor: D-one
"""
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
    parameter_range,
    sample_distribution,
)

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


def parameter_slider(name, param, default, step):
    """
    Ползунок параметра. Границы - область определения параметра из SciPy вокруг значения по умолчанию.
    """
    bounds = parameter_range(name, param, default, step)
    if bounds.is_integer:
        return st.slider(parameter_label(param, default),
                         min_value=bounds.min_value, value=int(default), max_value=bounds.max_value, step=1)
    return st.slider(parameter_label(param, default),
                     min_value=bounds.min_value, value=default, max_value=bounds.max_value, step=step)


def parameter_controls(info):
    """
    Создает ползунки (или поля ввода) для каждого параметра выбранного распределения.
    Начальные значения - параметры по умолчанию из SciPy.
    :return: {'a': 3.57, 'loc': 0.0, 'scale': 1.0} - значения, выбранные пользователем
    """
    mode = next(iter(PARAMETER_MODES))
    if st.checkbox("Нажмите, чтобы настроить параметры", value=False):
        mode = st.radio("Доступные параметры:", tuple(PARAMETER_MODES))
    step = PARAMETER_MODES[mode]

    parameters = {}
    for param, default in info.parameters.items():
        if step is None:
            parameters[param] = st.number_input(parameter_label(param, default), value=default, format='%.4f')
        else:
            parameters[param] = parameter_slider(info.name, param, default, step)
    return parameters


def show_equation(info):
    """
    SciPy записывает плотность в стандартной форме, без сдвига и масштаба. Показываем ее и то,
    как в нее входят loc и scale, а для нормального распределения - еще и привычную запись через μ и σ.
    """
    st.latex(info.equation)
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


def display_controls(sample):
    """
    Настройки отображения рисунка.
    :param sample: Sample или None, если с текущими параметрами распределение построить нельзя
    :return: (DisplaySettings, показывать ли таблицу описательной статистики)
    """
    st.markdown("**Выберите режим фигуры:**")
    plot_mode = st.radio("Опции", ('Dark Mode', 'Light Mode'))
    st.markdown("**Что показать на рисунке?**")
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
            x_cdf = st.slider('Установите значение x, чтобы получить: (x, P(X<=x))',
                              min_value=x_min,
                              value=min(max(float(sample.rv.median()), x_min), x_max),
                              max_value=x_max,
                              step=(x_max - x_min) / 200,
                              format='%.4g')

    sf, sf_shine = curve_controls('SF', 'sf_shine', value=False)

    boxplot = st.checkbox('Блочная диаграмма', value=True)

    st.markdown("**Показать квартили распределения:**")
    quantiles = tuple(column.checkbox(f'Q{i}', value=False)
                      for i, column in enumerate(st.columns(3), start=1))

    st.markdown("**Закрасить среднее ± kσ распределения:**")
    sigmas = tuple(column.checkbox(f'{i}σ', value=False)
                   for i, column in enumerate(st.columns(3), start=1))

    st.markdown("**Создать описательную статистику**")
    show_statistics = st.checkbox('Да', value=False)

    settings = DisplaySettings(plot_mode=plot_mode, histogram=histogram,
                               pdf=pdf, pdf_shine=pdf_shine,
                               cdf=cdf, cdf_shine=cdf_shine,
                               sf=sf, sf_shine=sf_shine,
                               mark_p=mark_p, x_cdf=x_cdf,
                               boxplot=boxplot, quantiles=quantiles, sigmas=sigmas)
    return settings, show_statistics


def statistics_table(sample):
    """
    Описательная статистика: свойства распределения рядом со значениями по случайной выборке.
    """
    rv, r = sample.rv, pd.Series(sample.r)
    with np.errstate(all='ignore'):
        mean, variance, skewness, excess_kurtosis = (float(value) for value in rv.stats(moments='mvsk'))
        q1, median, q3 = rv.ppf([0.25, 0.50, 0.75])
        support_min, support_max = rv.support()
    statistics = pd.DataFrame(
        {
            'Распределение': [mean, np.sqrt(variance), variance, skewness, excess_kurtosis,
                              support_min, q1, median, q3, support_max],
            f'Выборка, n={len(r)}': [r.mean(), r.std(), r.var(), r.skew(), r.kurtosis(),
                                     r.min(), r.quantile(0.25), r.median(), r.quantile(0.75), r.max()],
        },
        index=['Среднее', 'Стандартное отклонение', 'Дисперсия', 'Асимметрия', 'Эксцесс (избыточный)',
               'Минимум', 'Q1 (25%)', 'Медиана (50%)', 'Q3 (75%)', 'Максимум'])
    st.dataframe(statistics)
    st.caption('«Распределение» - теоретические значения; nan или inf означает, что величина не определена '
               'или бесконечна. «Выборка» - оценки по случайной выборке, они меняются от выборки к выборке.')


def export_code(name, parameters, seed):
    """
    Показывает сгенерированный скрипт и кнопку, которая его скачивает.
    """
    code = CodeGenerator(distribution=name, parameters=parameters, seed=seed).get_generated_code()
    st.code(code)
    st.download_button('Скачать файл Python', data=code,
                       file_name=f'{name}_{time.strftime("%Y%m%d_%H%M%S")}.py',
                       mime='text/x-python', on_click='ignore')


def p_explore():
    try:
        distributions = load_distributions('continuous')
    except Exception as e:
        st.error(f'Не удалось загрузить список распределений из документации SciPy: {e}')
        return

    st.sidebar.subheader("Исследовать")

    with st.sidebar.expander("Выбрать распределение"):
        name = st.selectbox('Нажмите ниже (или введите), чтобы выбрать распределение', list(distributions))
        info = distributions[name]
        st.markdown("**Параметры**")
        parameters = parameter_controls(info)
        seed = sample_seed()
        st.markdown("**SciPy официальная документация:**")
        st.info(f"Подробнее о: [{info.fullname}]({info.url})")

    st.markdown(f"<h1 style='text-align: center;'>{info.fullname}</h1>", unsafe_allow_html=True)

    if info.equation:
        show_equation(info)

    try:
        sample = cached_sample(name, parameters, seed)
    except InvalidParameters as e:
        sample = None
        st.warning(f'С такими параметрами распределение построить нельзя: {e}. Измените значения параметров.')

    with st.sidebar.expander("Настройка отображения"):
        settings, show_statistics = display_controls(sample)

    with st.sidebar.expander("Экспорт:"):
        st.info("Хотите **скрипт python?** (Он будет содержать: pdf, cdf, sf, гистограмму и диаграмму)")
        export_requested = st.button('Сгенерировать код Python')
        if export_requested:
            st.write('*Код находится под графиком')

    if sample is None:
        return

    figure = Figure(settings=settings, x=sample.x, r=sample.r, rv=sample.rv)
    try:
        if any(settings.sigmas) and not figure.sigma_is_defined():
            st.warning('У этого распределения с такими параметрами среднее или дисперсия не определены '
                       'либо бесконечны, поэтому область ±σ не показана.')
        st.pyplot(figure.figure_display_control())
        if show_statistics:
            statistics_table(sample)
    except NUMERIC_ERRORS as e:
        # выборка построилась, но плотность или моменты при таких параметрах SciPy вычислить не смог
        st.warning(f'SciPy не смог вычислить распределение с такими параметрами: {e}. '
                   'Измените значения параметров.')
        return
    finally:
        # Иначе фигуры накапливаются в памяти при каждом перезапуске скрипта
        plt.close('all')

    if export_requested:
        export_code(name, parameters, seed)
