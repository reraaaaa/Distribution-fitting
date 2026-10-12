"""
Created on 21/12/2021
Aauthor: D-one
"""

import scipy
import streamlit as st

image1 = ""
image2 = ""
image3 = ""
image4 = ""
image5 = ""
image6 = ""

def show_image(image):
    # Пока скриншоты не добавлены, пустые заглушки не показываем
    if image:
        st.image(image, width='stretch')


def p_introduction():
    st.markdown("<h2 style='text-align: center;'> Добро пожаловать в </h2>",
                unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'> Distribution Fitting </h1>",
                unsafe_allow_html=True)

    st.info("""
             Приложение включает в себя следующие разделы: \n
             - База распределений - раздел для исследования и изучения законов распределения
             - Подбор закона распределения - раздел для поиска подходящего закона на основе пользовательских данных
             $ ←$ Чтобы начать работу с приложением, выберите параметр на левой боковой панели.
             """)
    st.info("""
             - Дополнительная инструкция
             """)

    def make_line():
    # Линия-разделитель
        line = st.markdown('<hr style="border:1px solid gray"> </hr>',
                           unsafe_allow_html=True)
        return line

    # Описание
    st.error('База распределений')
    feature1, feature2 = st.columns([0.5, 0.4])
    with feature1:
        show_image(image1)
    with feature2:
        st.warning('Выбор распределения')
        st.info("""
                - Выберите распределение в выпадающем списке (или введите его имя).
                - Меняйте параметры распределения ползунками и смотрите, как меняется график.
                - Ссылка на официальную документацию **SciPy** находится под параметрами.
                """)

    make_line()

    feature3, feature4 = st.columns([0.6, 0.4])
    with feature3:
        show_image(image2)
    with feature4:
        st.warning('Настройка отображения')
        st.info("""
                - Выберите *тёмную или светлую тему*.
                - Включайте и выключайте: гистограмму, PDF, CDF, SF,
                блочную диаграмму, квартили, области среднее ± 1/2/3 $\\sigma$.
                - Получите таблицу описательной статистики.
                """)
    make_line()

    feature5, feature6 = st.columns([0.6, 0.4])
    with feature5:
        show_image(image3)
    with feature6:
        st.warning('Экспорт')
        st.info("""
                - Сгенерируйте код Python с выбранным распределением и параметрами.
                - Скачайте файл .py или скопируйте код.
                """)

    make_line()

    st.error('Подбор закона распределения')
    st.info('Раздел в разработке.')

    make_line()

    st.info(f'Доступны непрерывные распределения из **SciPy v{scipy.__version__}**.')

    st.markdown("""

                - Сокращения и обозначения:

                    - PDF - функция плотности вероятности (Probability Density Function)

                    - CDF - функция распределения (Cumulative Distribution Function)

                    - SF - функция выживания (Survival Function), SF(x) = 1 - CDF(x)

                    - P(X<=x) - вероятность получить значение не больше x
                                для выбранного x

                    - Q1, Q2, Q3 - квартили распределения: значения, ниже которых лежит
                                25%, 50% и 75% вероятности

                    - $\\sigma$ - стандартное отклонение распределения. На графике закрашивается
                                область среднее $\\pm k\\sigma$, в легенде указана вероятность попадания в неё.
                                Доли 68%, 95% и 99.7% верны только для нормального распределения

                    - Выборка - 400 случайных чисел из распределения; по ней строятся гистограмма
                                и блочная диаграмма

                """)
