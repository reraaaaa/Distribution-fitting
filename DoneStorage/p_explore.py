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

from pars_functions import (dis_button_names,
                            parameters_dictionaries)

def p_explore():
parameters_dictionaries = parameters_dictionaries()


    def make_expanders(expander_name, sidebar=True):
        """ Расширители, которые содержат набор опций. """
        if sidebar:
            try:
                return st.sidebar.expander(expander_name)
            except:
                return st.sidebar.beta_expander(expander_name)

    st.sidebar.subheader("Исследовать:")
    with make_expanders("Выбрать распределение"):

        # Распределения
        display = dis_button_names()

        # Виджет поля выбора, содержащий все функции SciPy
        select_distribution = st.selectbox(
            'Нажмите ниже (или введите), чтобы выбрать распределение',
            display)

        st.markdown("**Параметры**")

        def obtain_functional_data():
            """
            Эта функция создаст ползунки (или поля ввода) для каждого
            доступного параметра выбранного распределения. Ползунки будут запускаться
            со значением параметра по умолчанию, полученным из библиотеки SciPy.
            Дополнительные параметры включают ползунки с меньшим интервалом шага или
            поля ввода, если пользователи хотят вручную указать значения параметров.
            """

            # all_dist_params_dict: = 'alpha': {'a': '3.57', 'loc': '0.00', 'scale': '1.00'}

            # Расширенный режим будет содержать несколько дополнительных опций
            advanced_mode = st.checkbox("Нажмите, чтобы настроить параметры",
                                        value=False)

            if advanced_mode:
                vary_parameters_mode = st.radio("Доступные Варианты:",
                                                ('Интервал шага ползунка: 0,10',
                                                 'Интервал шага ползунка: 0,01',
                                                 'Ручной ввод значений параметров')
                                                )

            # "выберите дистрибутив" определяется поле выбора с подсветкой"
            if select_distribution in parameters_dictionaries.keys():
                sliders_params = []
                # Создайте ползунок для каждого параметра
                for i, param in enumerate(parameters_dictionaries[f'{select_distribution}']):
                    parameter_value = float(parameters_dictionaries.get(f'{select_distribution}').get(param))

                    # Поскольку большинство параметров не определены для значений ниже 0; Я ограничу минимальное значение до 0,01.
                    # Если пользователь знает, что он может опуститься ниже,
                    # можно ввести эти значения вручную.
                    # Масштаб не может быть 0 или меньше

                    min_param_value = 0.01

                    def sliders():
                        """
                        Функция, определяющая ползунок. Он будет запущен со значением по умолчанию,
                        определенным в SciPy. Минимальное значение ползунка 0,01;
                        максимальное значение 10 - добавляются произвольно.
                        """

                        slider_i = st.slider('Значение по умолчанию: ' + '{}'.format(param) + ' = ' + f'{parameter_value}',
                                             min_value=min_param_value,
                                             value=float("{:.2f}".format(parameter_value)),
                                             max_value=10.00,
                                             step=step_value)

                        return slider_i

                    # Выполнение попыток и исключений, которые позволят изменить
                    # интервал шага ползунка в расширенном режиме.

                    try:
                        if vary_parameters_mode == 'Интервал шага ползунка: 0,10':
                            step_value = 0.10
                            slider_i = sliders()
                            sliders_params.append(slider_i)

                        if vary_parameters_mode == 'Интервал шага ползунка: 0,01':
                            step_value = 0.01
                            slider_i = sliders()
                            sliders_params.append(slider_i)

                        if vary_parameters_mode == 'Ручной ввод значений параметров':
                            manual = float(
                                st.text_input('Значение по умолчанию: ' + '{}'.format(param) + ' = ' + f'{parameter_value}',
                                              float("{:.2f}".format(parameter_value))))
                            sliders_params.append(manual)
                    except:
                        step_value = 0.10
                        slider_i = sliders()
                        sliders_params.append(slider_i)

                # Добавьте примечание для пользователя, чтобы он знал, что делать,
                # если выберет недопустимое значение параметра.
                # st.markdown("**Примечания**")

                # st.info(
                #        """
                # Для смещения и/или масштабирования распределения
                # используйте параметры **loc** и **scale**. В случае **Ошибки значения**:
                # возможно, вы выбрали значение параметра формы, для которого не определено
                # распределение (чаще всего они не могут быть $$\leq$$0), в этом случае просто
                # выберите другое значение.
                #        """
                #        )

                # Для каждого выбранного дистрибутива создайте ссылку на официальную
                # страницу документации SciPy об этой функции.

                st.markdown("**Официальная документация SciPy:**")
                st.info(f"""
                        Подробнее о: 
                        [**{name_url_dict[select_distribution][1]}**]\
                            ({name_url_dict[select_distribution][0]})
                        """)

                return sliders_params

        sliders_params = obtain_functional_data()

    # Генерировать заголовок на основе выбранного дистрибутива
    if select_distribution:
    st.markdown(f"<h1 style='text-align: center;'>{name_proper_dict[select_distribution]}</h1>", unsafe_allow_html=True)