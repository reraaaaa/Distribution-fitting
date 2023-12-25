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

from ParsDistributions.parser import DistributionParser


def p_explore():

    doc_dic, functions_dic, fullname_dic, parameters_dic, url_dic = DistributionParser.get_dictionaries

    def make_expanders(expander_name, sidebar=True):
        # Настройка расширителей, которые содержат набор опций.
        # Аргументы:
        #   expander_name: вложение
        # вернет:
        #   Расширение
        if sidebar:
            try:
                return st.sidebar.expander(expander_name)
            except:
                return st.sidebar.beta_expander(expander_name)

    st.sidebar.subheader("Исследовать")
    with make_expanders("Выбрать распределение"):
        # функция имен
        display = DistributionParser.get_distribution_names()

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

            # Расширенный режим будет содержать несколько дополнительных опций
            advanced_mode = st.checkbox("Нажмите, чтобы настроить параметры", value=False)

            if advanced_mode:
                vary_parameters_mode = st.radio("Доступные параметры:",
                                                ('Интервал шага ползунка: 0.10',
                                                 'Интервал шага ползунка: 0.01',
                                                 'Ручной ввод значений параметров')
                                                )

            # "select_distribution" определяется полем выбора с подсветкой
            # Создать ползунок для каждого параметра
            if select_distribution in parameters_dic.keys():
                sliders_params = []
                for i, param in enumerate(parameters_dic[f'{select_distribution}']):
                    parameter_value = float(parameters_dic.get(f'{select_distribution}').get(param))

                    # Поскольку большинство параметров не определены для значений ниже 0;
                    # Я ограничу минимальное значение до 0,01. Если пользователь знает,
                    # что он может опуститься ниже, можно ввести эти значения вручную.
                    # Масштаб не может быть 0 или меньше
                    min_param_value = 0.01

                    def sliders():
                        # Функция, определяющая ползунок. Он будет запущен со значением по умолчанию,
                        # определенным в SciPy. Минимальное значение ползунка 0,01;
                        # максимальное значение 10 - добавляются произвольно.

                        slider_i = st.slider('Значение по умолчанию: '+'{}'.format(param)+' = '+f'{parameter_value}',
                                             min_value=min_param_value,
                                             value=float("{:.2f}".format(parameter_value)),
                                             max_value=10.00,
                                             step=step_value)
                        return slider_i

                    # Выполнение попыток и исключений позволит изменить
                    # интервал шага ползунка в расширенном режиме.
                    try:
                        if vary_parameters_mode == 'Интервал шага ползунка: 0.10':
                            step_value = 0.10
                            slider_i = sliders()
                            sliders_params.append(slider_i)

                        if vary_parameters_mode == 'Интервал шага ползунка: 0.01':
                            step_value = 0.01
                            slider_i = sliders()
                            sliders_params.append(slider_i)

                        if vary_parameters_mode == 'Ручной ввод значений параметров':
                            manual = float(st.text_input('Значение по умолчанию: '+'{}'.format(param)+' = '+f'{parameter_value}', float("{:.2f}".format(parameter_value))))
                            sliders_params.append(manual)
                    except:
                        step_value = 0.10
                        slider_i = sliders()
                        sliders_params.append(slider_i)

                # Добавим примечание для пользователя, чтобы он знал, что делать,
                # если выберет недопустимое значение параметра.
                # st.markdown("**Notes**")
                # st.info(
                #        """
                #        Для смещения и/или масштабирования распределения используйте
                #        параметры **loc** и **scale**. В случае **Ошибки значения**:
                #        возможно, вы выбрали значение параметра формы, для которого не
                #        определено распределение (чаще всего они не могут быть $$\leq$$0),
                #        в этом случае просто выберите другое значение.
                #        """
                #        )

                # Для каждого выбранного распределения создадим ссылку на
                # официальную страницу документации SciPy об этой функции.
                st.markdown("**SciPy официальная документация:**")
                st.info(f"""
                        Подробнее о: 
                        [**{url_dic[select_distribution][1]}**]\
                            ({url_dic[select_distribution][0]})
                        """)
                return sliders_params

        sliders_params = obtain_functional_data()

    # Создать заголовок на основе выбранного распределения
    if select_distribution:
        st.markdown(f"<h1 style='text-align: center;'>{fullname_dic[select_distribution]}</h1>", unsafe_allow_html=True)

    def get_multi_parameters(*c_params):
        # Эта функция принимает несколько аргументов, которые будут значениями
        # параметров функции. Каждая функция имеет от 2 до 6 параметров, два из которых
        # всегда одинаковы: loc и scale.
        # Аргументы:
        #   *c_params : список параметров функции распределения
        # вернет:
        #   x: массив float64 - Генерируются равномерно расположенные числа
        #   r: массив float64 - Сгенерированные случайные числа с использованием выбранного распределения.
        #   rv: frozen распределение

        # Размер выборки
        size = 400

        # Текущие scipy-функции имеют от 2 до 6 параметров (считая loc и scale),
        # которые будут в *c_params - как получено из ползунков/поля ввода.
        # Чтобы иметь возможность использовать параметры формы и значения loc/scale,
        # я просто говорю, какие есть какие, поскольку loc/scale всегда предпоследние и последние.
        for j, param in enumerate(c_params):
            # Возвращает значение именованного атрибута объекта
            dist = getattr(stats, select_distribution)
            # Генерирация равномерно распределенных чисел в заданном интервале
            x = np.linspace(dist.ppf(0.001, *c_params[j][0:(len(*c_params) - 2)],
                                     loc=c_params[0][-2], scale=c_params[0][-1]),
                            dist.ppf(0.999, *c_params[j][0:(len(*c_params) - 2)],
                                     loc=c_params[0][-2], scale=c_params[0][-1]), size)

            # Создайте замороженную случайную величину «RV», используя параметры функции
            # Она будет использоваться для отображения PDF
            rv = dist(*c_params[j][0:(len(*c_params) - 2)], loc=c_params[0][-2], scale=c_params[0][-1])

            # Генерация случайных чисел, используя выбранное распределение
            # Они будут использоваться для построения гистограммы
            r = dist.rvs(*c_params[j][0:(len(*c_params) - 2)], loc=c_params[0][-2], scale=c_params[0][-1], size=size)

        return x, r, rv

    x1, r1, rv1 = get_multi_parameters(sliders_params)

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
    class Figure:

        """ Figure class: used to display and manipulate Figure props. """

        xlabel = 'X значение'
        ylabel = 'Плотность'

        global_rc_params = {
            'legend.fontsize': 12,
            'legend.markerscale': 1.0,
            'axes.labelsize': 14,
            'axes.spines.top': False,
            'axes.spines.right': False,
            'xtick.labelsize': 12,
            'ytick.labelsize': 12,
            'xtick.top': False,
            'xtick.labeltop': False,
            'ytick.right': False,
            'ytick.labelright': False,
        }

        lines = {'solid': '-',
                 'dashed': '--',
                 'dashes': [5, 10, 5, 10],
                 'dashes_r': (0, (5, 10))
                 }

        if plot_mode == 'Dark Mode':
            colors = {
                'pdf_line_color': '#fec44f',
                'hist_color': '#bdbdbd',
                'hist_edge_color': 'grey',
                'cdf_line_color': 'white',
                'frame_edge_color': '#525252',
                'boxplot_lines_color': 'white',
                'boxplot_face_color': 'black',
                'quant1_color': '#c7e9b4',
                'quant2_color': '#7fcdbb',
                'quant3_color': '#41b6c4',
            }

        if plot_mode == 'Light Mode':
            colors = {
                'pdf_line_color': '#08519c',
                'hist_color': '#525252',
                'hist_edge_color': 'grey',
                'cdf_line_color': 'black',
                'frame_edge_color': '#525252',
                'boxplot_lines_color': 'black',
                'boxplot_face_color': 'white',
                'quant1_color': '#b2182b',
                'quant2_color': '#35978f',
                'quant3_color': '#b35806',
            }

        def __init__(self, x, r, rv, xlabel, ylabel, plot_mode, global_rc_params, lines, colors):
            """ Set properties """

            self.x = x
            self.r = r
            self.rv = rv
            self.xlabel = xlabel
            self.ylabel = ylabel
            self.plot_mode = plot_mode
            self.global_rc_params = global_rc_params
            self.lines = lines
            self.colors = colors

        def display_mode(self):
            """ rcParameters for light and dark mode """

            plot_mode = self.plot_mode

            if plot_mode == 'Dark Mode':
                plt.style.use('dark_background')
                plt.rcParams['figure.facecolor'] = 'black'

            if plot_mode == 'Light Mode':
                plt.style.use('classic')
                plt.rcParams['figure.facecolor'] = 'white'

        def pdf_cdf_lines(self, ax):
            """ How to plot the PDF/CDF lines and setup of the "Shine" """

            # Make the line shine
            n_lines = 5
            diff_linewidth = 3
            alpha_value = 0.1

            # Plot the frozen PDF if checkbox is active
            if select_pdf:
                ax.plot(self.x, self.rv.pdf(self.x), linestyle='-',
                        color=self.colors['pdf_line_color'],
                        lw=1, label='PDF')
                # Set the shine-on if the checkbox is active
                if select_pdf_shine:
                    for n in range(1, n_lines):
                        ax.plot(self.x, self.rv.pdf(self.x), '-',
                                color=self.colors['pdf_line_color'],
                                alpha=alpha_value,
                                linewidth=(diff_linewidth * n)
                                )

            # Same as above, only for the CDF properties
            if select_cdf:
                ax.plot(self.x, self.rv.cdf(self.x), linestyle='-',
                        color=self.colors['cdf_line_color'],
                        lw=1, label='CDF')

                if select_cdf_shine:
                    for n in range(1, n_lines):
                        ax.plot(self.x, self.rv.cdf(self.x), '-',
                                color=self.colors['cdf_line_color'],
                                alpha=alpha_value,
                                linewidth=(diff_linewidth * n))
                        # Mark a point on the CDF
                if select_mark_P:
                    xmin, xmax = ax.get_xlim()
                    ax.vlines(x_cdf, ymin=0, ymax=self.rv.cdf(x_cdf),
                              color=self.colors['cdf_line_color'],
                              linestyle=':', linewidth=1)
                    ax.hlines(self.rv.cdf(x_cdf), xmin=xmin,
                              xmax=x_cdf, color=self.colors['cdf_line_color'],
                              linestyle=':', linewidth=1)
                    ax.annotate(f'({x_cdf:.2f}, {self.rv.cdf(x_cdf):.2f})',
                                xy=(x_cdf, self.rv.cdf(x_cdf)),
                                color=self.colors['cdf_line_color'])
            if select_sf:
                ax.plot(self.x, self.rv.sf(self.x), linestyle='-',
                        color='plum',
                        lw=1, label='SF')

                if select_sf_shine:
                    for n in range(1, n_lines):
                        ax.plot(self.x, self.rv.sf(self.x), '-',
                                color='plum',
                                alpha=alpha_value,
                                linewidth=(diff_linewidth * n))

        def boxplot(self, ax):
            """ Define the boxplot properties. """

            bp = ax.boxplot(self.r, patch_artist=True,
                            vert=False,
                            notch=False,
                            showfliers=False
                            )

            for element in ['boxes', 'whiskers', 'fliers', 'means', \
                            'medians', 'caps']:
                plt.setp(bp[element], color=self.colors['boxplot_lines_color'])
            for patch in bp['boxes']:
                patch.set(facecolor=self.colors['boxplot_face_color'])

                # Move x label below - this will be active if boxplot is shown
            ax.set_xlabel(self.xlabel)

            # In addition to the global rcParams, set plot options:
            ax.spines['left'].set_visible(False)
            ax.set_yticklabels([])
            ax.set_yticks([])
            ax.set_ylim(0.9, 1.1)

        def quantiles(self, ax):
            """ Quantiles and their plot properties. """

            def get_line(self, q):
                """ Compute the quantiles and set them as vertical lines. """

                # Compute
                quant = mquantiles(self.r)

                # Plot
                ax.vlines(quant[q - 1], ymin=0, ymax=self.rv.pdf(quant[q - 1]),
                          color=self.colors[f'quant{q}_color'],
                          dashes=self.lines['dashes_r'],
                          linewidth=2, label=f'Q{q} = {quant[q - 1]:.2f}',
                          zorder=0, clip_on=False)

                # Label midway
                ax.text(quant[q - 1], self.rv.pdf(quant[q - 1]) * 0.5, f'Q{q}',
                        ha='center', fontsize=10,
                        color=self.colors[f'quant{q}_color'])

            # Streamlit control - checkboxes for Q1/2/3: on/off
            if q1:
                q = 1
                get_line(self, q)

            if q2:
                q = 2
                get_line(self, q)
            if q3:
                q = 3
                get_line(self, q)

        def sigmas(self, ax):
            """ Sigmas and their plot properties. """

            # Need to calculate above with the function!
            def which_s(self, s):
                """
                Compute standard deviation and the mean.
                Shade between: mean-std and mean+std which shows sigma.
                """

                x01 = s * self.r.std()
                # Select only x values in between sigma range
                x1 = self.x[(self.x > (self.r.mean() - x01)) & \
                            (self.x < (x01 + self.r.mean()))]
                # This will shade 1/2/3 sigma, limiting y on the PDF border
                ax.fill_between(x1, self.rv.pdf(x1), 0,
                                color=self.colors['pdf_line_color'],
                                alpha=0.2)

            # Streamlit control - checkboxes for sigma1/2/3: on/off
            if s1:
                s=1
                which_s(self, s)

            if s2:
                s=2
                which_s(self, s)
            if s3:
                s=3
                which_s(self, s)

        def histogram(self, ax):
            """ Histogram properties """

            ax.hist(self.r, density=True, bins=20,
                    edgecolor=self.colors['hist_edge_color'],
                    fill=False,  # hatch='x',
                    linewidth=1, alpha=1, label='Sample distribution')

        def get_figure(self, fig_type):
            """
            Figure layout: single figure, or two as a subplot.
            I want this, because boxplot (which is placed as subplot)
            can be set to: on/off.
            """

            if fig_type == 'dual':
                fig, ax = plt.subplots(2, 1,
                                       gridspec_kw={'height_ratios': [9, 0.7]})

                return fig, ax

            else:
                fig, ax = plt.subplots(1, 1)
                return fig, ax

        def figure_display_control(self):
            """
            Set dual figure: this will have distribution and boxplot.
            In this case we have distributions and its properties on the
            ax[0], while if boxplot is 'on' it will be set to ax[1].
            """

            plt.rcParams.update(self.global_rc_params)

            # Streamlit control - if boxplot is true
            if select_boxplot:
                fig, ax = Figure.get_figure(self, 'dual')

                Figure.pdf_cdf_lines(self, ax=ax[0])

                if q1 or q2 or q3:
                    Figure.quantiles(self, ax=ax[0])

                if s1 or s2 or s3:
                    Figure.sigmas(self, ax=ax[0])

                if select_hist:
                    Figure.histogram(self, ax=ax[0])

                legend = ax[0].legend(bbox_to_anchor=(0, 1.02, 1, 0.2),
                                      loc="lower left", mode="expand",
                                      borderaxespad=0, ncol=3)
                legend.get_frame().set_edgecolor("#525252")

                # In case all distribution prop. from ax[0] are off set the
                # boxplot on the ax[0] if the boxplot is on.
                if (select_cdf == False and select_pdf == False \
                        and select_hist == False and select_sf == False):

                    fig, ax = Figure.get_figure(self, 'single')

                    Figure.boxplot(self, ax=ax)

                else:

                    Figure.boxplot(self, ax=ax[1])

                    # Get xlim from the upper image and port it to the lower
                    # as we want to have x axis of the distributions and
                    # boxplot aligned.
                    ax[1].set_xlim(ax[0].get_xlim())

                    # Move y label to apropriate ax.
                    ax[0].set_ylabel(self.ylabel)


            else:
                # Single fig. mode
                fig, ax = Figure.get_figure(self, 'single')

                Figure.pdf_cdf_lines(self, ax=ax)

                if select_hist:
                    Figure.histogram(self, ax=ax)

                if q1 or q2 or q3:
                    Figure.quantiles(self, ax=ax)

                if s1 or s2 or s3:
                    Figure.sigmas(self, ax=ax)

                ax.set_xlabel(self.xlabel)
                ax.set_ylabel(self.ylabel)

                legend = ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2),
                                   loc="lower left", mode="expand",
                                   borderaxespad=0, ncol=3)
                legend.get_frame().set_edgecolor("#525252")

            # If nothing is selected from the 'What to show on the Figure'
            if (select_cdf == False and select_pdf == False \
                    and select_hist == False and select_boxplot == False \
                    and select_sf == False):
                fig, ax = Figure.get_figure(self, 'single')

                ax.text(0.1, 0.5, 'Tabula rasa',
                        va='center', fontsize=20)
                ax.spines['left'].set_visible(False)
                ax.spines['bottom'].set_visible(False)
                ax.set_yticklabels([])
                ax.set_yticks([])
                ax.set_xticklabels([])
                ax.set_xticks([])

            return fig

    def port_to_streamlit():
        # Используем класс Figure, чтобы получить то, что будет отображаться на графике.
        # Показать рисунок с помощью виджета Streamlit: pyplot

        p = Figure(
            x1,
            r1,
            rv1,
            Figure.xlabel,
            Figure.ylabel,
            plot_mode,
            Figure.global_rc_params,
            Figure.lines,
            Figure.colors,
        )

        # Чтобы получить светлый/темный режим
        Figure.display_mode(p)

        # Разобрать в Streamlit
        st.pyplot(p.figure_display_control())

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

    def how_many_params():
        # Извлечь значения параметров, выбранные пользователем. Для
        # распределения, содержащего только масштаб / локацию.
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
                param_name = DistributionParser.get_dictionaries_stats.get(f'{select_distribution}').shapes.split(', ')
                name = f'{param_name[i]}'
                p = f'{param_name[i]}={param}'

                names.append(name)
                ps.append(p)

        return scale, loc, names, ps

    # Получить вывод
    scale, loc, name, p = how_many_params()

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

    # Для генерации кода я передаю: {loc} и {scale}, которые будут иметь свое имя и значения,
    # и {a}, которые будут параметрами формы - их может быть много, и каждый будет напечатан в
    # новой строке {select_distribution} - передается из ползунка {имя} содержит только название
    # параметров формы, без значений. Должен размещаться без отступа, иначе код py будет с отступом
    generate_code = f"""
# -*- coding: utf-8 -*-
# {time.strftime("%Y%m%d_%H%M%S")}
# ---

import matplotlib.pyplot as plt #v3.2.2
import numpy as np #v1.18.5
from scipy.stats import {select_distribution} #v1.6.1

# Set random seed
np.random.seed(1)

# Function parameters
{scale}
{loc}
{a}              
     
# Generate evenly spaced numbers over a specified interval
size = 400
x = np.linspace({select_distribution}.ppf(0.001, {name} loc=loc, scale=scale ), 
                {select_distribution}.ppf(0.999, {name} loc=loc, scale=scale ),
                size)

# Freeze the distribution
rv = {select_distribution}({name} loc=loc, scale=scale)

# Generate random numbers
r = {select_distribution}.rvs({name} loc=loc, scale=scale, size=size)

# Make a plot
fig, ax = plt.subplots(2, 1,
                       gridspec_kw={{'height_ratios': [9, 0.7]}})

# Plot PDF, CDF and SF
ax[0].plot(x, rv.pdf(x), linestyle='-', color='#3182bd', lw=3, label='PDF')
ax[0].plot(x, rv.cdf(x), linestyle='-', color='k', lw=3, label='CDF')
ax[0].plot(x, rv.sf(x), linestyle='-', color='#df65b0', lw=3, label='SF')

# Plot Histogram
ax[0].hist(r, density=True, bins=20, color='lightgrey',
           edgecolor='k', label='Sample')

# Plot Boxplot
bp = ax[1].boxplot(r, patch_artist=True,
           vert=False,
           notch=False,
           showfliers=False,
           ) 
# Boxplot aestetic
for median in bp['medians']: median.set(color ='red', linewidth = 2) 
for patch in bp['boxes']: patch.set(facecolor='white') 

# Set legend
ax[0].legend(bbox_to_anchor=(0,1.1,1,0.2), 
             loc="center", 
             borderaxespad=0, ncol=2)

# Set Figure aestetics
ax[0].spines['top'].set_visible(False)
ax[0].spines['right'].set_visible(False)
ax[0].set_title('Distribution: {select_distribution}')

ax[1].set_xlim(ax[0].get_xlim())
ax[1].set_ylim(0.9, 1.1)
ax[1].spines['left'].set_visible(False)
ax[1].spines['top'].set_visible(False)
ax[1].spines['right'].set_visible(False)
ax[1].set_yticklabels([])
ax[1].set_yticks([])

ax[1].set_xlabel('X value')
ax[0].set_ylabel('Density')

plt.show()

"""
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