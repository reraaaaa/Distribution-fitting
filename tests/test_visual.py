import matplotlib.pyplot as plt
import pytest

from UtilitySt import DisplaySettings, Figure, sample_distribution


def draw(name, parameters, **settings):
    sample = sample_distribution(name, parameters)
    figure = Figure(DisplaySettings(**settings), x=sample.x, r=sample.r, rv=sample.rv)
    fig = figure.figure_display_control()
    labels = fig.axes[0].get_legend_handles_labels()[1]
    ylabel = fig.axes[0].get_ylabel()
    plt.close('all')
    return figure, labels, ylabel


NORM = {'loc': 0.0, 'scale': 1.0}


def test_sigma_bands_report_the_real_probability():
    _, labels, _ = draw('norm', NORM, sigmas=(True, True, True))
    assert {'1σ: P = 0.683', '2σ: P = 0.954', '3σ: P = 0.997'} <= set(labels)

    # у экспоненциального распределения в ±1σ лежит не 68%
    _, labels, _ = draw('expon', NORM, sigmas=(True, False, False))
    assert '1σ: P = 0.865' in labels


def test_sigma_bands_are_skipped_when_variance_is_undefined():
    figure, labels, _ = draw('cauchy', NORM, sigmas=(True, True, True))
    assert not figure.sigma_is_defined()
    assert not [label for label in labels if 'σ' in label]


def test_quartiles_are_those_of_the_distribution():
    _, labels, _ = draw('norm', NORM, quantiles=(True, True, True))
    assert {'Q1 = -0.67', 'Q2 = 0.00', 'Q3 = 0.67'} <= set(labels)


@pytest.mark.parametrize('settings, expected', [
    ({}, 'Плотность'),
    ({'pdf': False, 'histogram': False, 'cdf': True}, 'Вероятность'),
    ({'cdf': True}, 'Плотность / вероятность'),
])
def test_y_axis_label_matches_what_is_drawn(settings, expected):
    _, _, ylabel = draw('norm', NORM, **settings)
    assert ylabel == expected


def test_nothing_selected_draws_placeholder():
    sample = sample_distribution('norm', NORM)
    settings = DisplaySettings(pdf=False, histogram=False, boxplot=False)
    fig = Figure(settings, x=sample.x, r=sample.r, rv=sample.rv).figure_display_control()
    assert [text.get_text() for text in fig.axes[0].texts] == ['Tabula rasa']
    plt.close('all')
