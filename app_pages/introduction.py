"""
Created on 21/12/2021
Aauthor: D-one
"""

import numpy as np
import pandas as pd
import scipy
import streamlit as st
from scipy import stats

from .explore import load_distributions
from .navigation import page_link

# Распределения для графика на главной: подпись -> замороженное распределение
PREVIEW = {
    'Нормальное': stats.norm(loc=2, scale=1),
    'Гамма, a = 2': stats.gamma(a=2),
    'Логнормальное, s = 0.6': stats.lognorm(s=0.6),
    'Экспоненциальное': stats.expon(),
}


def preview_chart():
    """
    Плотности нескольких знакомых распределений на одном графике.
    """
    x = np.linspace(0, 6, 301)
    densities = pd.DataFrame({label: rv.pdf(x) for label, rv in PREVIEW.items()}, index=pd.Index(x, name='x'))
    st.line_chart(densities, height=320, x_label='x', y_label='Плотность')


def distribution_count():
    """
    :return: число распределений в базе или None, если документация SciPy недоступна
    """
    try:
        return len(load_distributions('continuous'))
    except Exception:
        return None


def p_introduction():
    st.title('Distribution Fitting')
    st.markdown('#### Справочник непрерывных распределений и подбор распределения по данным')
    st.write('Изучайте распределения: двигайте параметры и смотрите, как меняются плотность, функция '
             'распределения и случайная выборка. Или загрузите свои данные и подберите распределение, '
             'которое описывает их лучше всего. Все расчёты выполняет SciPy.')
    page_link('explore', 'Открыть базу распределений', icon=':material/arrow_forward:')

    preview_chart()

    count = distribution_count()
    distributions, plots, engine = st.columns(3)
    distributions.metric('Распределений', count if count is not None else '—')
    plots.metric('Функций на графике', 'PDF · CDF · SF')
    engine.metric('Расчёты', f'SciPy {scipy.__version__}')

    st.subheader('Разделы')
    explore, fitting = st.columns(2)
    with explore.container(border=True):
        st.markdown('##### :material/monitoring: База распределений')
        st.markdown(
            '- Параметры меняются ползунками в границах области определения\n'
            '- Формула плотности и ссылка на документацию SciPy\n'
            '- Квартили и области среднее ± σ с реальной вероятностью\n'
            '- Таблица: теория рядом с оценками по выборке\n'
            '- Экспорт готового скрипта Python'
        )
        page_link('explore', 'Перейти', icon=':material/arrow_forward:')
    with fitting.container(border=True):
        st.markdown('##### :material/query_stats: Подбор закона распределения')
        st.markdown(
            '- Свои данные из CSV или TXT либо встроенный пример\n'
            '- Оценка параметров методом максимального правдоподобия\n'
            '- Сравнение распределений по AIC, BIC и критерию Колмогорова - Смирнова\n'
            '- График подгонки и Q-Q график\n'
            '- Экспорт таблицы, данных и скрипта Python'
        )
        page_link('fitting', 'Перейти', icon=':material/arrow_forward:')

    st.subheader('Как пользоваться')
    first, second, third = st.columns(3)
    with first.container(border=True):
        st.markdown('**1. Выберите распределение**')
        st.caption('В боковой панели раздела «База распределений»: выпадающий список с поиском по имени.')
    with second.container(border=True):
        st.markdown('**2. Настройте параметры**')
        st.caption('Ползунки или ручной ввод. Недопустимое сочетание параметров даёт предупреждение.')
    with third.container(border=True):
        st.markdown('**3. Изучите и сохраните**')
        st.caption('Включайте линии и статистику в «Настройке отображения», скачивайте скрипт в «Экспорте».')

    with st.expander('Сокращения и обозначения'):
        st.markdown(
            '- **PDF** — функция плотности вероятности (Probability Density Function)\n'
            '- **CDF** — функция распределения (Cumulative Distribution Function)\n'
            '- **SF** — функция выживания (Survival Function), SF(x) = 1 − CDF(x)\n'
            '- **P(X ≤ x)** — вероятность получить значение не больше x\n'
            '- **Q1, Q2, Q3** — квартили распределения: значения, ниже которых лежит 25%, 50% и 75% вероятности\n'
            '- **σ** — стандартное отклонение распределения. На графике закрашивается область среднее ± kσ, '
            'в легенде указана вероятность попадания в неё. Доли 68%, 95% и 99.7% верны только '
            'для нормального распределения\n'
            '- **Выборка** — 400 случайных чисел из распределения; по ней строятся гистограмма '
            'и блочная диаграмма'
        )
