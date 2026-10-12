"""Вкладка «Калькулятор»: вероятности, квантили и меры риска одного распределения."""
import math

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

from UtilitySt import NUMERIC_ERRORS, discrete_interval_figure, interval_figure, risk

TAILS = {
    'Доходность или прибыль: потери слева': risk.LEFT,
    'Убыток: потери справа': risk.RIGHT,
}


def number(value):
    if not math.isfinite(value):
        return 'не определено'
    return f'{value:.6g}'


def show_calculator(rv, x, plot_mode, key, discrete=False):
    """
    :param rv: frozen распределение
    :param x: точки для графика плотности
    :param key: префикс ключей виджетов; у каждого распределения свой, чтобы значения не переносились
    :param discrete: дискретное распределение: на графике вероятности значений, а не плотность
    """
    try:
        with np.errstate(all='ignore'):
            q1, median, q3 = (float(value) for value in rv.ppf([0.25, 0.50, 0.75]))
    except NUMERIC_ERRORS as e:
        st.warning(f'SciPy не смог вычислить квантили распределения: {e}.')
        return

    st.markdown('##### Вероятность попасть в интервал')
    low_column, high_column, result_column = st.columns(3)
    low = low_column.number_input('От', value=q1, format='%.6g', key=f'{key}:low')
    high = high_column.number_input('До', value=q3, format='%.6g', key=f'{key}:high')
    if high <= low:
        st.warning('Верхняя граница интервала должна быть больше нижней.')
    else:
        result_column.metric('P(от < X ≤ до)', f'{risk.interval_probability(rv, low, high):.4f}')
        st.pyplot((discrete_interval_figure if discrete else interval_figure)(rv, x, low, high, plot_mode))
        plt.close('all')

    st.markdown('##### Квантиль и вероятность')
    probability_column, quantile_column = st.columns(2)
    probability = probability_column.number_input('Вероятность p', min_value=0.0001, max_value=0.9999, value=0.95,
                                                  format='%.4f', key=f'{key}:p')
    probability_column.metric('Квантиль: x, при котором P(X ≤ x) = p', number(float(rv.ppf(probability))))
    value = quantile_column.number_input('Значение x', value=median, format='%.6g', key=f'{key}:x')
    quantile_column.metric('P(X ≤ x)', f'{float(rv.cdf(value)):.4f}')

    st.markdown('##### Меры риска')
    tail = TAILS[st.radio('Что описывает распределение', tuple(TAILS), key=f'{key}:tail', horizontal=True)]
    level = st.select_slider('Уровень доверия', options=risk.RISK_LEVELS, value=0.99,
                             format_func=lambda option: f'{option:.1%}', key=f'{key}:level')
    var_column, es_column = st.columns(2)
    try:
        var_column.metric(f'VaR {level:.1%}', number(risk.value_at_risk(rv, level, tail)))
        es_column.metric(f'Expected Shortfall {level:.1%}', number(risk.expected_shortfall(rv, level, tail)))
    except NUMERIC_ERRORS as e:
        st.warning(f'SciPy не смог вычислить меры риска: {e}.')
    st.caption(
        'VaR - потеря, которая не будет превышена с вероятностью, равной уровню доверия. '
        'Expected Shortfall - средняя потеря в остальных, худших случаях; он всегда не меньше VaR. '
        'Обе величины показаны как размер потери: отрицательное значение означает, что даже в худшем случае '
        'на этом уровне получается прибыль. «Не определено» - у распределения в хвосте потерь нет конечного '
        'среднего (как у распределения Коши), и средняя потеря не существует.'
    )
