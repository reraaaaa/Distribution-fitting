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
        """ Set up expanders which contains a set of options. """
        if sidebar:
            try:
                return st.sidebar.expander(expander_name)
            except:
                return st.sidebar.beta_expander(expander_name)

    st.sidebar.subheader("To explore:")
    with make_expanders("Select distribution"):

        # Distribution names
        display = s.get_distribution_names()

        # Create select box widget containing all SciPy function
        select_distribution = st.selectbox(
            'Click below (or type) to choose a distribution',
            display)

        st.markdown("**Parameters**")

        def obtain_functional_data():
            """
            This function will create sliders (or input boxes) for
            each available parameter of the selected distribution.
            Sliders will initiate with the parameter default value, as
            obtained from the SciPy library.
            Advanced options include sliders with smaller step interval, or
            input boxes if Users want to manually specify parameter values.
            """

            # all_dist_params_dict:
            # See helper function for details; output example:
            # 'alpha': {'a': '3.57', 'loc': '0.00', 'scale': '1.00'},

            # Advance mode will contain few more options
            advanced_mode = st.checkbox("Click to fine-tune parameters",
                                        value=False)

            if advanced_mode:
                vary_parameters_mode = st.radio("Available options:",
                                                ('Slider stepping interval: 0.10',
                                                 'Slider stepping interval: 0.01',
                                                 'Manually input parameter values')
                                                )

            # "select_distribution" is defined streamlit selectbox
            if select_distribution in parameters_dic.keys():
                sliders_params = []
                # Create slider for each parameter
                for i, param in enumerate(parameters_dic[f'{select_distribution}']):
                    parameter_value = float(parameters_dic.get(f'{select_distribution}').get(param))

                    # As the majority of the parameters are not defined for
                    # values below 0; I will limit minimum value to 0.01.
                    # If user know that they can go below, it's possible to
                    # enter those values manually.
                    # Scale can not be 0 or less than
                    min_param_value = 0.01

                    def sliders():
                        """
                        Function that defines a slider. It's going to be
                        initiated with the default value as defined in SciPy.
                        Slider min value of 0.01; max value of 10 - are added
                        arbitrary.
                        """

                        slider_i = st.slider('Default value: ' + '{}'.format(param) + ' = ' + f'{parameter_value}',
                                             min_value=min_param_value,
                                             value=float("{:.2f}".format(parameter_value)),
                                             max_value=10.00,
                                             step=step_value)

                        return slider_i

                    # Doing try and except which will allow slider stepping
                    # interval to be changed in the advanced mode.
                    try:
                        if vary_parameters_mode == 'Slider stepping interval: 0.10':
                            step_value = 0.10
                            slider_i = sliders()
                            sliders_params.append(slider_i)

                        if vary_parameters_mode == 'Slider stepping interval: 0.01':
                            step_value = 0.01
                            slider_i = sliders()
                            sliders_params.append(slider_i)

                        if vary_parameters_mode == 'Manually input parameter values':
                            manual = float(
                                st.text_input('Default value: ' + '{}'.format(param) + ' = ' + f'{parameter_value}',
                                              float("{:.2f}".format(parameter_value))))
                            sliders_params.append(manual)
                    except:
                        step_value = 0.10
                        slider_i = sliders()
                        sliders_params.append(slider_i)

                # Add a note to user so that they know what to do in case
                # they select a parameter value which is not valid.
                # st.markdown("**Notes**")

                # st.info(
                #        """
                #        To shift and/or scale the distribution use
                #        the **loc** and **scale** parameters. In case of
                #        **Value Error**: you probably selected a shape
                #        parameter value for which a distribution is not defined
                #        (most often they can't be $$\leq$$0), in that case just
                #         select a different value.
                #        """
                #        )

                # For each selected distribution create a link to the
                # official SciPy documentation page about that function.
                st.markdown("**SciPy official documentation:**")
                scipy_link = f'[{url_dic[select_distribution][1]}]({url_dic[select_distribution][0]})'

                # st.info(f"""
                #        Read more about:
                #        [**{name_url_dict[select_distribution][1]}**]\
                #            ({name_url_dict[select_distribution][0]})
                #        """)

                st.info(f""" 
                        Read more about:
                        {scipy_link}
                        """)

                return sliders_params

        sliders_params = obtain_functional_data()

    # Generate title based on the selected distribution
    if select_distribution:
        st.markdown(f"<h1 style='text-align: center;'>{fullname_dic[select_distribution]}</h1>",
                    unsafe_allow_html=True)

    def get_multi_parameters(*c_params):
        """
        This function accepts multiple arguments which will be function
        parameter values. Each function have 2-6 parameters, two being always
        the same: loc and scale.

        Parameters
        ----------
        *c_params : a list of parameters of the distribution function.

        Returns
        -------
        x : array of float64
            Generated evenly spaced numbers.
        r : array of float64
            Generated random numbers using the selected distribution.
        rv : frozen distribution

        """

        # Sample size
        size = 400
        # Current scipy functions have from 2 to 6 parameters (counting loc &
        # scale) which will be in *c_params - as obtained from sliders/input box

        # To be able to use shape parameters and loc/scale values
        # I just tell which are which, as loc/scale are always second to last and last
        for j, param in enumerate(c_params):
            # Returns the value of the named attribute of an object
            dist = getattr(stats, select_distribution)

            # Generate evenly spaced numbers over a specified interval
            x = np.linspace(dist.ppf(0.001, *c_params[j][0:(len(*c_params) - 2)],
                                     loc=c_params[0][-2], scale=c_params[0][-1]),
                            dist.ppf(0.999, *c_params[j][0:(len(*c_params) - 2)],
                                     loc=c_params[0][-2], scale=c_params[0][-1]), size)

            # Create a frozen random variable "RV" using function parameters
            # It will be used to show the PDF
            rv = dist(*c_params[j][0:(len(*c_params) - 2)], loc=c_params[0][-2],
                      scale=c_params[0][-1])

            # Generate random numbers using the selected distribution
            # These will be used for making histogram
            r = dist.rvs(*c_params[j][0:(len(*c_params) - 2)], loc=c_params[0][-2],
                         scale=c_params[0][-1], size=size)

        return x, r, rv

    x1, r1, rv1 = get_multi_parameters(sliders_params)

    # Getting equations to display
    # Due to several different formatting of the equations, in order for them
    # to properly display in latex mode, I am using markdown for a few:
    if select_distribution in functions_dic.keys():

        if select_distribution == 'crystalball' \
                or select_distribution == 'f' \
                or select_distribution == 'genextreme' \
                or select_distribution == 'loglaplace':
            st.markdown(f'{functions_dic[select_distribution]}')
        else:
            st.latex(f'{functions_dic[select_distribution]}')

    # Additional as I noticed that it takes long to compute levy_stable
    if select_distribution == 'levy_stable':
        st.write('*Note: it take longer to compute.')

    # Figure display properties expander
    with make_expanders("Tweak display"):

        st.markdown("**Select Figure Mode:**")
        plot_mode = st.radio("Options", ('Dark Mode', 'Light Mode'))

        st.markdown("**What to show on the Figure?**")

        select_hist = st.checkbox('Histogram', value=True)

        # Put checkboxes for PDF and Shine in a column
        # If PDF is True (on): Shine can be True/False (on/off)
        # If PDF checkbox is False, remove Shine checkbox
        select_pdf, select_pdf_shine = st.columns(2)
        with select_pdf:
            select_pdf = st.checkbox('PDF', value=True)
            if select_pdf == False:
                select_pdf_shine = st.empty()
            else:
                with select_pdf_shine:
                    select_pdf_shine = st.checkbox('Shine', value=True)

        # Same functionality as for the PDF above
        select_cdf, select_cdf_shine = st.columns(2)
        with select_cdf:
            select_cdf = st.checkbox('CDF', value=False)
            if select_cdf == False:
                select_cdf_shine = st.empty()
            else:
                with select_cdf_shine:
                    select_cdf_shine = st.checkbox('Shine ', value=True)

                    # Show/Hide and explore
        if select_cdf == False:
            select_mark_P = st.empty()
            x_cdf = st.empty()
        else:
            select_mark_P = st.checkbox('P(X<=x)', value=False)
            if select_mark_P:
                x_cdf = st.slider('Set x value to get: (x, P(X<=x))',
                                  min_value=round(min(r1), 2),
                                  value=0.5,
                                  max_value=round(max(r1), 2),
                                  step=0.10)

        # Same functionality as for the PDF/CDF above
        select_sf, select_sf_shine = st.columns(2)
        with select_sf:
            select_sf = st.checkbox('SF', value=False)
            if select_sf == False:
                select_sf_shine = st.empty()
            else:
                with select_sf_shine:
                    select_sf_shine = st.checkbox('Shine   ', value=True)

                    # Show/hide boxplot
        select_boxplot = st.checkbox('Boxplot', value=True)

        # Show/hide quantile lines
        st.markdown("**Show quantile(s):**")
        left, middle, right = st.columns(3)
        with left:
            q1 = st.checkbox('Q1', value=False)  # , [0.25,0.5,0.75]
        with middle:
            q2 = st.checkbox('Q2', value=False)
        with right:
            q3 = st.checkbox('Q3', value=False)

        # Show/hide shaded sigma region(s)
        # Since widgets don't support latex yet, this is hacky way to add
        # sigma next to each checkbox using columns
        st.markdown("**Shade region(s) of**")
        left_std, sig1, middle_std, sig2, right_std, sig3 = \
            st.columns([0.012, 0.044,
                        0.02, 0.038,
                        0.02, 0.038])
        with sig1:
            st.markdown("1$\sigma$")
        with left_std:
            # Need to leave name empty,as we want sigma
            s1 = st.checkbox('', value=False)
        with sig2:
            st.markdown("2$\sigma$")
        with middle_std:
            # Need empty, with space so that generate key doesn't overlap
            s2 = st.checkbox(' ', value=False)
        with sig3:
            st.markdown("3$\sigma$")
        with right_std:
            s3 = st.checkbox('   ', value=False)

        # Show/hide a column with statistical information of the distribution
        st.markdown("**Generate descriptive statistics**")
        df_stat = st.checkbox('Yes', value=False)

    # Export options
    with make_expanders("Export:"):
        st.info("""
                Want **python script?** (It will contain: pdf, cdf, sf, 
                                        histogram and boxplot)
                """)
        export_code = st.button('Generate Python code')
        if export_code:
            st.write('*Code is below the Figure')

        # st.write('**Generated code will contain: pdf, cdf, sf, histogram and\
        #         boxplot*.')

    # A little of breathing room before I display 'About'
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
            names = []
            ps = []
            scale = f'scale={sliders_params[-1]}'
            loc = f'loc={sliders_params[-2]}'
        else:
            scale = f'scale={sliders_params[-1]}'
            loc = f'loc={sliders_params[-2]}'

            names = []
            ps = []
            distribution_dict = s.get_dictionaries_stat().get(select_distribution)
            if distribution_dict is None:
                raise KeyError(f"{select_distribution} not found in the returned dictionary.")

            param_names = distribution_dict.get('shapes')
            if param_names is not None:
                param_names = param_names.split(', ')
                for i, param in enumerate(sliders_params[0:-2]):
                    name = f'{param_names[i]}'
                    p = f'{param_names[i]}={param}'

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