# -*- coding: utf-8 -*-
"""
Created on 03/01/2022
Aauthor: D-one
"""
import time

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from ParsDistributions import DistributionParser
from UtilitySt import CodeGenerator, DisplaySettings, Figure, sample_distribution

# Режимы ввода параметров: подпись в интерфейсе -> шаг ползунка (None - ручной ввод)
PARAMETER_MODES = {
    'Интервал шага ползунка: 0.10': 0.10,
    'Интервал шага ползунка: 0.01': 0.01,
    'Ручной ввод значений параметров': None,
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


def parameter_slider(param, default, step):
    """
    Ползунок параметра. Границы считаются от значения по умолчанию из SciPy.
    """
    # loc и параметры с неположительным значением по умолчанию могут быть отрицательными
    if param != 'loc' and default >= 0.01:
        min_value = 0.01
    else:
        min_value = min(-10.00, 2 * default)
    return st.slider(parameter_label(param, default),
                     min_value=min_value,
                     value=default,
                     max_value=max(10.00, 2 * default),
                     step=step)


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
            parameters[param] = float(st.text_input(parameter_label(param, default), str(default)))
        else:
            parameters[param] = parameter_slider(param, default, step)
    return parameters


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
    if cdf:
        mark_p = st.checkbox('P(X<=x)', value=False)
        if mark_p:
            # Границы берем из x, а не из случайной выборки r: иначе ползунок
            # сбрасывался бы при каждом перезапуске скрипта
            x_min, x_max = round(float(sample.x[0]), 2), round(float(sample.x[-1]), 2)
            x_cdf = st.slider('Установите значение x, чтобы получить: (x, P(X<=x))',
                              min_value=x_min,
                              value=min(max(round(float(sample.rv.median()), 2), x_min), x_max),
                              max_value=x_max,
                              step=0.10)

    sf, sf_shine = curve_controls('SF', 'sf_shine', value=False)

    boxplot = st.checkbox('Блочная диаграмма', value=True)

    st.markdown("**Показать квантили:**")
    quantiles = tuple(column.checkbox(f'Q{i}', value=False)
                      for i, column in enumerate(st.columns(3), start=1))

    st.markdown("**Область тени**")
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


def statistics_table(r):
    """
    Описательная статистика случайной выборки r.
    """
    df_data = pd.DataFrame(r)
    statistics = df_data.describe()
    statistics.loc['var'] = df_data.var().tolist()
    statistics.loc['skew'] = df_data.skew().tolist()
    statistics.loc['kurt'] = df_data.kurtosis().tolist()
    st.dataframe(statistics.rename(columns={0: 'Value'}))


def export_code(name, parameters):
    """
    Показывает сгенерированный скрипт и кнопку, которая его скачивает.
    """
    code = CodeGenerator(distribution=name, parameters=parameters).get_generated_code()
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
        st.markdown("**SciPy официальная документация:**")
        st.info(f"Подробнее о: [{info.fullname}]({info.url})")

    st.markdown(f"<h1 style='text-align: center;'>{info.fullname}</h1>", unsafe_allow_html=True)

    sample = sample_distribution(name, parameters)

    if info.equation:
        st.latex(info.equation)

    with st.sidebar.expander("Настройка отображения"):
        settings, show_statistics = display_controls(sample)

    with st.sidebar.expander("Экспорт:"):
        st.info("Хотите **скрипт python?** (Он будет содержать: pdf, cdf, sf, гистограмму и диаграмму)")
        export_requested = st.button('Сгенерировать код Python')
        if export_requested:
            st.write('*Код находится под графиком')

    figure = Figure(settings=settings, x=sample.x, r=sample.r, rv=sample.rv)
    st.pyplot(figure.figure_display_control())
    # Иначе фигуры накапливаются в памяти при каждом перезапуске скрипта
    plt.close('all')

    if show_statistics:
        statistics_table(sample.r)

    if export_requested:
        export_code(name, parameters)
