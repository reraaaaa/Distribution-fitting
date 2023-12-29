# -*- coding: utf-8 -*-
"""
Created on 03/01/2022
Aauthor: D-one
"""

import streamlit as st
from scipy import stats
from scipy.stats.mstats import mquantiles
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import time
import base64
import ParsDistributions.parser as dps
import UtilitySt.visual as fg
import UtilitySt.code_generator as cg


def p_explore():
    s = dps.DistributionParser(type_rv='continuous')
    dictionaries = s.get_dictionaries()

    doc_dic, functions_dic, fullname_dic, parameters_dic, url_dic = dictionaries.values()

    def make_expanders(expander_name, sidebar=True):
        """
        Настройка расширителей, которые содержат набор опций
        :param sidebar:
        :param expander_name: вложение
        :return: Расширение
        """
        if sidebar:
            try:
                return st.sidebar.expander(expander_name)
            except:
                return st.sidebar.beta_expander(expander_name)

    def create_slider(param, parameter_value, step_value):
        """ Создает ползунок с заданным параметром и значением шага. """
        slider_i = st.slider('Значение по умолчанию: ' + '{}'.format(param) + ' = ' + f'{parameter_value}',
                             min_value=0.01,
                             value=float("{:.2f}".format(parameter_value)),
                             max_value=10.00,
                             step=step_value)
        return slider_i

    def create_manual_input(param, parameter_value):
        """ Создает поле ввода для ручного ввода значения параметра. """
        manual = float(st.text_input('Значение по умолчанию: ' + '{}'.format(param) + ' = ' + f'{parameter_value}',
                                     float("{:.2f}".format(parameter_value))))
        return manual

    st.sidebar.subheader("Исследовать")

    with make_expanders("Выбрать распределение"):
        # функция имен
        display = s.get_distribution_names()
        # Создать виджет окна выбора, содержащий все функции SciPy
        select_distribution = st.selectbox('Нажмите ниже (или введите), чтобы выбрать распределение', display)
        st.markdown("**Параметры**")

        def obtain_functional_data():
            """
            Эта функция создаст ползунки (или поля ввода) для каждого
            доступного параметра выбранного распределения. Ползунки будут запускаться
            со значением параметра по умолчанию, полученным из библиотеки SciPy.
            Дополнительные параметры включают ползунки с меньшим интервалом шага или поля ввода,
            если пользователи хотят вручную указать значения параметров.
            """
            # parameters_dic:
            # Подробности смотрите во вспомогательной функции; пример вывода:
            # 'alpha': {'a': '3.57', 'loc': '0.00', 'scale': '1.00'},
            advanced_mode = st.checkbox("Нажмите, чтобы настроить параметры", value=False)
            vary_parameters_mode = 'Интервал шага ползунка: 0.10'
            if advanced_mode:
                vary_parameters_mode = st.radio("Доступные параметры:",
                                                ('Интервал шага ползунка: 0.10',
                                                 'Интервал шага ползунка: 0.01',
                                                 'Ручной ввод значений параметров')
                                                )
            if select_distribution in parameters_dic.keys():
                sliders_params = []
                for i, param in enumerate(parameters_dic[f'{select_distribution}']):
                    parameter_value = float(parameters_dic.get(f'{select_distribution}').get(param))

                    try:
                        if vary_parameters_mode == 'Интервал шага ползунка: 0.10':
                            slider_i = create_slider(param, parameter_value, 0.10)
                            sliders_params.append(slider_i)
                        if vary_parameters_mode == 'Интервал шага ползунка: 0.01':
                            slider_i = create_slider(param, parameter_value, 0.01)
                            sliders_params.append(slider_i)
                        if vary_parameters_mode == 'Ручной ввод значений параметров':
                            manual = create_manual_input(param, parameter_value)
                            sliders_params.append(manual)
                    except:
                        slider_i = create_slider(param, parameter_value, 0.10)
                        sliders_params.append(slider_i)

                st.markdown("**SciPy официальная документация:**")
                scipy_link = f'[{url_dic[select_distribution][1]}]({url_dic[select_distribution][0]})'
                st.info(f"""
                        Подробнее о: 
                        {scipy_link}
                        """)

                return sliders_params

        sliders_params = obtain_functional_data()

    # Создать заголовок на основе выбранного распределения
    if select_distribution:
        st.markdown(f"<h1 style='text-align: center;'>{fullname_dic[select_distribution]}</h1>", unsafe_allow_html=True)

    def get_multi_parameters(select_distribution, *c_params):
        """
        Эта функция принимает несколько аргументов, которые будут значениями параметров функции.
        Текущие scipy-функции имеют от 2 до 6 параметров, два из которых всегда одинаковы: loc и scale.
        :param select_distribution: Name of the distribution
        :param c_params: Список параметров функции распределения
        :return x: массив float64 - Генерируются равномерно расположенные числа
        :return r: массив float64 - Сгенерированные случайные числа с использованием выбранного распределения.
        :return rv: Frozen распределение
        """
        size = 400
        dist = getattr(stats, select_distribution)

        if len(c_params) < 2:
            raise ValueError("At least two parameters are required")

        *dist_params, loc, scale = c_params
        x = np.linspace(dist.ppf(0.001, *dist_params, loc=loc, scale=scale),
                        dist.ppf(0.999, *dist_params, loc=loc, scale=scale), size)
        rv = dist(*dist_params, loc=loc, scale=scale)
        r = dist.rvs(*dist_params, loc=loc, scale=scale, size=size)

        return x, r, rv

    x1, r1, rv1 = get_multi_parameters(select_distribution, *sliders_params)

    # Получение уравнений для отображения. Из-за нескольких различных форматов
    # уравнений, чтобы они правильно отображались в латексном режиме, используем уценку:
    if select_distribution in functions_dic.keys():
        if select_distribution == 'crystalball' or select_distribution == 'f' or select_distribution == 'genextreme' or select_distribution == 'loglaplace':
            st.markdown(f'{functions_dic[select_distribution]}')
        else:
            st.latex(f'{functions_dic[select_distribution]}')

    # Дополнительно, поскольку я заметил, что вычисление levy_stable занимает много времени
    if select_distribution == 'levy_stable':
        st.write('*Примечание: для вычисления требуется больше времени.')

    # Расширитель свойств отображения рисунка
    with make_expanders("Настройка отображения"):
        st.markdown("**Выберите режим фигуры:**")
        plot_mode = st.radio("Опции", ('Dark Mode', 'Light Mode'))
        st.markdown("**Что показать на рисунке?**")
        select_hist = st.checkbox('Гистограмма', value=True)

        # Поставьте галочки для PDF и Shine в столбик. Если PDF имеет значение True (вкл.):
        # Shine может быть True/False (вкл./выкл.).
        # Если флажок PDF установлен False, снимите флажок Shine.
        select_pdf, select_pdf_shine = st.columns(2)
        with select_pdf:
            select_pdf = st.checkbox('PDF', value=True)
            if select_pdf == False:
                select_pdf_shine = st.empty()
            else:
                with select_pdf_shine:
                    select_pdf_shine = st.checkbox('Shine', value=True)

        # Та же функциональность, что и для PDF выше
        select_cdf, select_cdf_shine = st.columns(2)
        with select_cdf:
            select_cdf = st.checkbox('CDF', value=False)
            if select_cdf == False:
                select_cdf_shine = st.empty()
            else:
                with select_cdf_shine:
                    select_cdf_shine = st.checkbox('Shine ', value=True)

        # Показать/скрыть и исследовать
        if select_cdf == False:
            select_mark_P = st.empty()
            x_cdf = st.empty()
        else:
            select_mark_P = st.checkbox('P(X<=x)', value=False)
            if select_mark_P:
                x_cdf = st.slider('Установите значение x, чтобы получить: (x, P(X<=x))',
                                  min_value=round(min(r1), 2),
                                  value=0.5,
                                  max_value=round(max(r1), 2),
                                  step=0.10)

        # Та же функциональность, что и для PDF/CDF выше
        select_sf, select_sf_shine = st.columns(2)
        with select_sf:
            select_sf = st.checkbox('SF', value=False)
            if select_sf == False:
                select_sf_shine = st.empty()
            else:
                with select_sf_shine:
                    select_sf_shine = st.checkbox('Shine   ', value=True)

        # Показать/скрыть блочную диаграмму
        select_boxplot = st.checkbox('Блочная диаграмма', value=True)

        # Показать/скрыть строки квантилей
        st.markdown("**Показать квантили:**")
        left, middle, right = st.columns(3)
        with left:
            q1 = st.checkbox('Q1', value=False)  # , [0.25,0.5,0.75]
        with middle:
            q2 = st.checkbox('Q2', value=False)
        with right:
            q3 = st.checkbox('Q3', value=False)

        # Показать/скрыть заштрихованные сигма-области.
        # Поскольку виджеты еще не поддерживают латекс, это хакерский способ добавить сигму
        # рядом с каждым флажком, используя столбцы.
        st.markdown("**Область тени **")
        left_std, sig1, middle_std, sig2, right_std, sig3 = st.columns([0.012, 0.044,
                                                                        0.02, 0.038,
                                                                        0.02, 0.038])
        with sig1:
            st.markdown("1$\sigma$")
        with left_std:
            # Нужно оставить имя пустым, так как нам нужна сигма
            s1 = st.checkbox('', value=False)
        with sig2:
            st.markdown("2$\sigma$")
        with middle_std:
            # Нужен пустой, с пробелом, чтобы ключ генерации не перекрывался
            s2 = st.checkbox(' ', value=False)
        with sig3:
            st.markdown("3$\sigma$")
        with right_std:
            s3 = st.checkbox('   ', value=False)

        # Показать/скрыть столбец со статистической информацией о распределении
        st.markdown("**Создать описательную статистику**")
        df_stat = st.checkbox('Да', value=False)

    # Параметры экспорта
    with make_expanders("Экспорт:"):
        st.info("""
                Хотите **скрипт python?** (Он будет содержать: pdf, cdf, sf, гистограмму и диаграмму)
                """)
        export_code = st.button('Сгенерировать код Python')
        if export_code:
            st.write('*Код находится под графиком')

    # Немного передышки, прежде чем я покажу «О программе».
    st.sidebar.write("")
    st.sidebar.write("")
    st.sidebar.write("")

    # Здесь я определяю класс Figure
    #######  I define a Figure class here #######

    fig = fg.Figure(select_hist=select_hist,
                    select_pdf_shine=select_pdf_shine,
                    select_cdf_shine=select_cdf_shine,
                    select_sf_shine=select_sf_shine,
                    select_mark_p=select_mark_P,
                    x_cdf=x_cdf,
                    select_boxplot=select_boxplot,
                    q1=q1,
                    q2=q2,
                    q3=q3,
                    s1=s1,
                    s2=s2,
                    s3=s3,
                    x=x1,
                    r=r1,
                    rv=rv1,
                    plot_mode=plot_mode,
                    select_pdf=select_pdf,
                    select_cdf=select_cdf,
                    select_sf=select_sf)

    def port_to_streamlit():
        # Используем класс Figure, чтобы получить то, что будет отображаться на графике.
        # Показать рисунок с помощью виджета Streamlit: pyplot

        # Разобрать в Streamlit
        st.pyplot(fig.figure_display_control())

    # Output statistics into a Table
    def df_generate_statistics(r1):
        # Вычислите статистическую информацию о созданном распределении.
        # Разберите его в кадр данных Pandas.
        # Use r1: array of float64 — сгенерированные случайные числа с использованием выбранного распределения.

        df_data = pd.DataFrame(r1)
        stats = df_data.describe()
        stats.loc['var'] = df_data.var().tolist()
        stats.loc['skew'] = df_data.skew().tolist()
        stats.loc['kurt'] = df_data.kurtosis().tolist()

        # Разобрать в Streamlit
        st.dataframe(stats.rename(columns={0: 'Value'}))

    # Радиокнопки, управляющие темным/светлым режимом
    if plot_mode == 'Dark Mode':
        port_to_streamlit()

    if plot_mode == 'Light Mode':
        port_to_streamlit()

    # Streamlit вкл/выкл, чтобы показать/скрыть статистическую информацию
    if df_stat:
        df_generate_statistics(r1)

    # Generate Python code
    def how_many_params(sliders_params, s, select_distribution):
        if len(sliders_params) == 2:
            names = ""
            ps = ""
            scale = f'scale={sliders_params[-1]}'
            loc = f'loc={sliders_params[-2]}'
            return scale, loc, names, ps

        else:
            scale = f'scale={sliders_params[-1]}'
            loc = f'loc={sliders_params[-2]}'

            names = []
            ps = []
            for i, param in enumerate(sliders_params[0:-2]):
                param_name = s.get_dictionaries_stat().get(f'{select_distribution}').shapes.split(', ')
                name = f'{param_name[i]}'
                p = f'{param_name[i]}={param}'

                names.append(name)
                ps.append(p)

        return scale, loc, names, ps

    # Get output
    scale, loc, name, p = how_many_params(sliders_params, s, select_distribution)

    # Извлеченный p имеет вид: ['a=4.3', 'b=4.0'], поэтому нужно удалить [',']
    a = str([i for i in p]).strip(" [] ").strip("'").replace("'", '').replace(", ", '\n')

    # Нужно отформатировать вывод, чтобы я мог получить параметры формы без дополнительных символов.
    def get_n(name):
        # для распределений только с масштабом/местоположением
        if len(name) == 0:
            name = ''
        else:
            name = str([i for i in name]).strip(" [] ").strip("'").replace("'", '')+','
        return name

    name = get_n(name)
    # генерируем скрипт
    code_f = cg.CodeGenerator(select_distribution=select_distribution,
                              scale=scale,
                              loc=loc,
                              a=a,
                              name=name)
    generate_code = code_f.get_generated_code()

    def get_code():
        # Распечатывает код в формате python
        st.code(f"{generate_code}")

    def py_file_downloader(py_file_text):
        # Преобразование строк <-> байтов и создание ссылки, по которой будет
        # загружаться сгенерированный скрипт Python.
        # Добавить метку времени к имени сохраненного файла
        time_stamp = time.strftime("%Y%m%d_%H%M%S")
        # Base64 позаботится о переносе информации в данные.
        b64 = base64.b64encode(py_file_text.encode()).decode()
        # Сохраненный файл будет иметь имя дистрибутива и отметку времени
        code_file = f"{select_distribution}_{time_stamp}.py"
        st.markdown(f'** Скачать файл Python **: \
                    <a href="data:file/txt;base64,{b64}" \
                        download="{code_file}">Кликните сюда</a>',
                    unsafe_allow_html=True)
    # Нажмите кнопку, чтобы получить код Python и загрузить опцию гиперссылки.
    if export_code:
        get_code()
        py_file_downloader(f"{generate_code}")