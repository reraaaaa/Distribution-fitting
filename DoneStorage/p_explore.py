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


class DistributionExplorer:
    def __init__(self):
        self.s = dps.DistributionParser(type_rv='continuous')
        self.dictionaries = self.s.get_dictionaries()
        (self.doc_dic, self.functions_dic, self.fullname_dic,
         self.parameters_dic, self.url_dic) = self.dictionaries.values()

    @staticmethod
    def make_expanders(expander_name, sidebar=True):
        return st.sidebar.expander(expander_name) if sidebar else st.sidebar.beta_expander(expander_name)

    @staticmethod
    def create_slider(param, parameter_value, step_value):
        slider_i = st.slider(f'Значение по умолчанию: {param} = {parameter_value}',
                             min_value=0.01,
                             value=float("{:.2f}".format(parameter_value)),
                             max_value=10.00,
                             step=step_value)
        return slider_i

    @staticmethod
    def create_manual_input(param, parameter_value):
        manual = float(st.text_input(f'Значение по умолчанию: {param} = {parameter_value}',
                                     float("{:.2f}".format(parameter_value))))
        return manual

    def obtain_functional_data(self, select_distribution, parameters_dic, create_slider, create_manual_input, url_dic):
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
        *dist_params, loc, scale = c_params
        x = np.linspace(dist.ppf(0.001, *dist_params, loc=loc, scale=scale),
                        dist.ppf(0.999, *dist_params, loc=loc, scale=scale), size)
        rv = dist(*dist_params, loc=loc, scale=scale)
        r = dist.rvs(*dist_params, loc=loc, scale=scale, size=size)

        return x, r, rv

    def explore(self):
        st.sidebar.subheader("Исследовать")

        with self.make_expanders("Выбрать распределение"):
            display = self.s.get_distribution_names()
            select_distribution = st.selectbox('Нажмите ниже (или введите), чтобы выбрать распределение', display)
            st.markdown("**Параметры**")
            sliders_params = self.obtain_functional_data(select_distribution)

        if select_distribution:
            st.markdown(f"<h1 style='text-align: center;'>{self.fullname_dic[select_distribution]}</h1>", unsafe_allow_html=True)

        x1, r1, rv1 = self.get_multi_parameters(select_distribution, *sliders_params)

        if select_distribution in self.functions_dic.keys():
            if select_distribution in ['crystalball', 'f', 'genextreme', 'loglaplace']:
                st.markdown(f'{self.functions_dic[select_distribution]}')
            else:
                st.latex(f'{self.functions_dic[select_distribution]}')

        if select_distribution == 'levy_stable':
            st.write('*Примечание: для вычисления требуется больше времени.')

        fig = self.create_figure(x1, r1, rv1)

        st.pyplot(fig.figure_display_control())

        if st.checkbox('Создать описательную статистику', value=False):
            self.df_generate_statistics(r1)

        if st.button('Сгенерировать код Python'):
            self.generate_code(sliders_params, select_distribution)

    # ... other methods ...

