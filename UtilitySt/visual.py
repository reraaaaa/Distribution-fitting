from dataclasses import dataclass

import matplotlib.pyplot as plt
import numpy as np


@dataclass(frozen=True)
class DisplaySettings:
    """
    Что показывать на рисунке. Значения по умолчанию совпадают с начальным состоянием виджетов.
    :param quantiles: показывать ли Q1, Q2, Q3
    :param sigmas: закрашивать ли области 1, 2, 3 сигма
    :param x_cdf: значение x для отметки (x, P(X<=x)); используется только при mark_p
    """
    plot_mode: str = 'Dark Mode'
    histogram: bool = True
    pdf: bool = True
    pdf_shine: bool = True
    cdf: bool = False
    cdf_shine: bool = False
    sf: bool = False
    sf_shine: bool = False
    mark_p: bool = False
    x_cdf: float | None = None
    boxplot: bool = True
    quantiles: tuple = (False, False, False)
    sigmas: tuple = (False, False, False)

    @property
    def has_curves(self):
        return any([self.pdf, self.cdf, self.sf, self.histogram])


class Figure(object):
    """
    Класс фигуры: используется для отображения реквизитов фигуры и управления ими.
    """

    xlabel = 'X значение'

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

    quantile_dashes = (0, (5, 10))

    DARK_MODE_COLORS = {
        'pdf_line_color': '#fec44f',
        'hist_color': '#bdbdbd',
        'hist_edge_color': 'grey',
        'cdf_line_color': 'white',
        'frame_edge_color': '#525252',
        'boxplot_lines_color': 'white',
        'boxplot_face_color': 'black',
        'quant1_color': '#c7e9b4',
        'quant2_color': '#7fcdbb',
        'quant3_color': '#41b6c4'
    }

    LIGHT_MODE_COLORS = {
        'pdf_line_color': '#08519c',
        'hist_color': '#525252',
        'hist_edge_color': 'grey',
        'cdf_line_color': 'black',
        'frame_edge_color': '#525252',
        'boxplot_lines_color': 'black',
        'boxplot_face_color': 'white',
        'quant1_color': '#b2182b',
        'quant2_color': '#35978f',
        'quant3_color': '#b35806'
    }

    def __init__(self, settings, x, r, rv):
        """
        :param settings: DisplaySettings - что и как показывать
        :param x: массив значений x для линий
        :param r: случайная выборка из распределения
        :param rv: frozen распределение
        """
        self.settings = settings
        self.x = x
        self.r = r
        self.rv = rv
        self._mean_std = None
        self.colors = self.get_color_scheme(settings.plot_mode)
        self.display_mode(settings.plot_mode)

    def get_color_scheme(self, plot_mode):
        """
        Получить цветовую схему в зависимости от режима
        :param plot_mode:
        :return: Словарь с цветовой схемой
        """
        if plot_mode == 'Dark Mode':
            colors = self.DARK_MODE_COLORS
        elif plot_mode == 'Light Mode':
            colors = self.LIGHT_MODE_COLORS
        else:
            raise ValueError("Invalid mode. Expected 'Dark Mode' or 'Light Mode'")
        return colors

    def display_mode(self, plot_mode):
        """ rcParameters for light and dark mode """

        if plot_mode == 'Dark Mode':
            plt.style.use(['default', 'dark_background'])
            plt.rcParams['figure.facecolor'] = 'black'

        elif plot_mode == 'Light Mode':
            plt.style.use(['default', 'classic'])
            plt.rcParams['figure.facecolor'] = 'white'
        else:
            raise ValueError("Invalid mode. Expected 'Dark Mode' or 'Light Mode'")

    def plot_with_shine(self, ax, select, select_shine, color, func, label):
        """
        Постройте линию с дополнительным эффектом блеска
        :param ax:
        :param select: тип селектора select_pdf или select_cdf или select_sf
        :param select_shine: тип селектора select_pdf_shine или select_cdf_shine или select_sf_shine
        :param color: цвет схема из get_color_scheme
        :param func: rv.pdf или rv.cdf или rv.sf
        :param label: PDF или CDF
        :return:
        """
        n_lines = 5
        diff_linewidth = 3
        alpha_value = 0.1

        if select:
            ax.plot(self.x, func(self.x), linestyle='-', color=color, lw=1, label=label)
            if select_shine:
                for n in range(1, n_lines):
                    ax.plot(self.x, func(self.x), linestyle='-',
                            color=color,
                            alpha=alpha_value,
                            linewidth=(diff_linewidth * n))

    def pdf_cdf_lines(self, ax):
        """
        Процедура построения линии PDF/CDF и настройка «Shine»
        :param ax:
        :return:
        """
        s = self.settings
        self.plot_with_shine(ax, s.pdf, s.pdf_shine, self.colors['pdf_line_color'], self.rv.pdf, 'PDF')
        self.plot_with_shine(ax, s.cdf, s.cdf_shine, self.colors['cdf_line_color'], self.rv.cdf, 'CDF')
        # Отметьте точку на CDF
        if s.mark_p:
            xmin, xmax = ax.get_xlim()
            p = self.rv.cdf(s.x_cdf)
            ax.vlines(s.x_cdf, ymin=0, ymax=p,
                      color=self.colors['cdf_line_color'],
                      linestyle=':', linewidth=1)
            ax.hlines(p, xmin=xmin,
                      xmax=s.x_cdf, color=self.colors['cdf_line_color'],
                      linestyle=':', linewidth=1)
            ax.annotate(f'({s.x_cdf:.2f}, {p:.2f})',
                        xy=(s.x_cdf, p),
                        color=self.colors['cdf_line_color'])

        self.plot_with_shine(ax, s.sf, s.sf_shine, 'plum', self.rv.sf, 'SF')

    def boxplot(self, ax):
        """
        Определите свойства коробчатой диаграммы.
        :param ax:
        :return:
        """
        bp = ax.boxplot(self.r, patch_artist=True,
                        orientation='horizontal',
                        notch=False,
                        showfliers=False
                        )

        for element in ['boxes', 'whiskers', 'fliers', 'means', 'medians', 'caps']:
            plt.setp(bp[element], color=self.colors['boxplot_lines_color'])
        for patch in bp['boxes']:
            patch.set(facecolor=self.colors['boxplot_face_color'])

        # Переместить метку x ниже — она будет активна, если отображается коробчатая диаграмма.
        ax.set_xlabel(self.xlabel)

        # В дополнение к глобальным rcParams установите параметры графика:
        ax.spines['left'].set_visible(False)
        ax.set_yticklabels([])
        ax.set_yticks([])
        ax.set_ylim(0.9, 1.1)

    def quantiles(self, ax):
        """
        Квартили распределения (не выборки): вертикальные линии до кривой PDF.
        """
        quant = self.rv.ppf([0.25, 0.50, 0.75])

        for idx, q in enumerate(self.settings.quantiles, start=1):
            if q:
                ax.vlines(quant[idx - 1], ymin=0, ymax=self.rv.pdf(quant[idx - 1]),
                          color=self.colors[f'quant{idx}_color'],
                          dashes=self.quantile_dashes,
                          linewidth=2, label=f'Q{idx} = {quant[idx - 1]:.2f}',
                          zorder=0, clip_on=False)

                # Label midway
                ax.text(quant[idx - 1], self.rv.pdf(quant[idx - 1]) * 0.5, f'Q{idx}',
                        ha='center', fontsize=10,
                        color=self.colors[f'quant{idx}_color'])

    def sigma_is_defined(self):
        """
        У распределений с тяжелыми хвостами (cauchy, levy) среднее или дисперсия не определены либо бесконечны.
        """
        return bool(np.all(np.isfinite(self.mean_std())))

    def mean_std(self):
        """
        Среднее и стандартное отклонение распределения. У части распределений SciPy считает их
        численным интегрированием за секунды, поэтому считаем один раз.
        """
        if self._mean_std is None:
            with np.errstate(all='ignore'):
                self._mean_std = (float(self.rv.mean()), float(self.rv.std()))
        return self._mean_std

    def sigmas(self, ax):
        """
        Закрашивает область среднее ± k·σ распределения и подписывает вероятность попадания в нее:
        68/95/99.7% верны только для нормального распределения.
        :param ax:
        :return:
        """
        if not self.sigma_is_defined():
            return
        mean, std = self.mean_std()
        for idx, s in enumerate(self.settings.sigmas, start=1):
            if s:
                low, high = mean - idx * std, mean + idx * std
                probability = self.rv.cdf(high) - self.rv.cdf(low)
                # Выберите только значения x в диапазоне сигм.
                x1 = self.x[(self.x > low) & (self.x < high)]
                # Это затенит 1/2/3 сигмы, ограничивая y на границе PDF.
                ax.fill_between(x1, self.rv.pdf(x1), 0,
                                color=self.colors['pdf_line_color'],
                                alpha=0.2, label=f'{idx}σ: P = {probability:.3f}')

    def histogram(self, ax):
        """ Histogram properties """

        ax.hist(self.r, density=True, bins=20,
                edgecolor=self.colors['hist_edge_color'],
                fill=False,  # hatch='x',
                linewidth=1, alpha=1, label='Выборка')

    def setup_figure(self, fig_type):
        if fig_type == 'dual':
            fig, ax = plt.subplots(2, 1,
                                   gridspec_kw={'height_ratios': [9, 0.7]})
        else:
            fig, ax = plt.subplots(1, 1)
        return fig, ax

    def plot_lines(self, ax):
        self.pdf_cdf_lines(ax=ax)
        if any(self.settings.quantiles):
            self.quantiles(ax=ax)
        if any(self.settings.sigmas):
            self.sigmas(ax=ax)
        if self.settings.histogram:
            self.histogram(ax=ax)

    def set_legend(self, ax):
        legend = ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2),
                           loc="lower left",
                           mode="expand",
                           borderaxespad=0,
                           ncol=3)
        legend.get_frame().set_edgecolor("#525252")

    def ylabel(self):
        """
        PDF и гистограмма - плотность, CDF и SF - вероятность.
        """
        s = self.settings
        density = s.pdf or s.histogram
        probability = s.cdf or s.sf
        if density and probability:
            return 'Плотность / вероятность'
        return 'Вероятность' if probability else 'Плотность'

    def empty_figure(self):
        fig, ax = self.setup_figure('single')
        ax.text(0.1, 0.5, 'Tabula rasa', va='center', fontsize=20)
        ax.spines['left'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.set_yticklabels([])
        ax.set_yticks([])
        ax.set_xticklabels([])
        ax.set_xticks([])
        return fig

    def figure_display_control(self):
        plt.rcParams.update(self.global_rc_params)
        s = self.settings

        if not s.has_curves and not s.boxplot:
            return self.empty_figure()

        if not s.has_curves:
            fig, ax = self.setup_figure('single')
            self.boxplot(ax=ax)
        elif s.boxplot:
            fig, ax = self.setup_figure('dual')
            self.plot_lines(ax[0])
            self.set_legend(ax[0])
            self.boxplot(ax=ax[1])
            ax[1].set_xlim(ax[0].get_xlim())
            ax[0].set_ylabel(self.ylabel())
        else:
            fig, ax = self.setup_figure('single')
            self.plot_lines(ax)
            ax.set_xlabel(self.xlabel)
            ax.set_ylabel(self.ylabel())
            self.set_legend(ax)
        return fig


FIT_LINE_COLORS = ['#fec44f', '#41b6c4', '#f768a1', '#7fcdbb', '#c994c7', '#fd8d3c', '#74a9cf', '#a1d99b']


def apply_plot_mode(plot_mode):
    """
    Стиль matplotlib для темного или светлого режима.
    :return: словарь цветов режима
    """
    if plot_mode == 'Dark Mode':
        plt.style.use(['default', 'dark_background'])
        plt.rcParams['figure.facecolor'] = 'black'
        colors = Figure.DARK_MODE_COLORS
    elif plot_mode == 'Light Mode':
        plt.style.use(['default', 'classic'])
        plt.rcParams['figure.facecolor'] = 'white'
        colors = Figure.LIGHT_MODE_COLORS
    else:
        raise ValueError("Invalid mode. Expected 'Dark Mode' or 'Light Mode'")
    plt.rcParams.update(Figure.global_rc_params)
    return colors


def data_figure(density, edges, plot_mode):
    """
    Гистограмма плотности данных.
    """
    colors = apply_plot_mode(plot_mode)
    fig, ax = plt.subplots(1, 1)
    ax.stairs(density, edges, color=colors['hist_edge_color'], linewidth=1, label='Данные')
    ax.set_xlabel('X значение')
    ax.set_ylabel('Плотность')
    return fig, ax


def fit_figure(density, edges, results, plot_mode):
    """
    Гистограмма данных и плотности подобранных распределений.
    :param results: подобранные FitResult, от лучшего к худшему
    """
    fig, ax = data_figure(density, edges, plot_mode)
    x = np.linspace(edges[0], edges[-1], 800)
    for result, color in zip(results, FIT_LINE_COLORS, strict=False):
        with np.errstate(all='ignore'):
            pdf = result.frozen().pdf(x)
        ax.plot(x, pdf, color=color, lw=1.5, label=result.name)
    # бесконечная плотность на краю носителя не должна сжимать остальной график
    ax.set_ylim(0, 1.6 * density.max())
    legend = ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left", mode="expand", borderaxespad=0, ncol=3)
    legend.get_frame().set_edgecolor("#525252")
    return fig


def qq_figure(data, result, plot_mode):
    """
    Q-Q график: квантили данных против квантилей подобранного распределения.
    Точки на диагонали означают, что распределение описывает данные и в хвостах.
    """
    colors = apply_plot_mode(plot_mode)
    observed = np.sort(data)
    probabilities = (np.arange(1, len(observed) + 1) - 0.5) / len(observed)
    with np.errstate(all='ignore'):
        theoretical = result.frozen().ppf(probabilities)
    finite = np.isfinite(theoretical)
    theoretical, observed = theoretical[finite], observed[finite]

    fig, ax = plt.subplots(1, 1)
    ax.plot(theoretical, observed, linestyle='none', marker='o', markersize=3,
            color=colors['pdf_line_color'], alpha=0.6, label='Данные')
    low, high = min(theoretical.min(), observed.min()), max(theoretical.max(), observed.max())
    ax.plot([low, high], [low, high], color=colors['cdf_line_color'], lw=1, linestyle='--',
            label='Идеальное совпадение')
    ax.set_xlabel(f'Квантили распределения {result.name}')
    ax.set_ylabel('Квантили данных')
    legend = ax.legend(loc='upper left')
    legend.get_frame().set_edgecolor("#525252")
    return fig


def interval_figure(rv, x, low, high, plot_mode):
    """
    Плотность с закрашенной областью low < X <= high.
    """
    colors = apply_plot_mode(plot_mode)
    fig, ax = plt.subplots(1, 1, figsize=(6.4, 3.2))
    with np.errstate(all='ignore'):
        density = rv.pdf(x)
    ax.plot(x, density, color=colors['pdf_line_color'], lw=1.5)
    inside = (x > low) & (x <= high)
    ax.fill_between(x[inside], density[inside], 0, color=colors['pdf_line_color'], alpha=0.35)
    finite = density[np.isfinite(density)]
    if len(finite):
        ax.set_ylim(0, 1.1 * finite.max())
    ax.set_xlabel('X значение')
    ax.set_ylabel('Плотность')
    return fig


def discrete_figure(settings, x, r, rv):
    """
    Рисунок дискретного распределения: вероятности значений столбиками, функция распределения ступеньками,
    частоты значений в выборке.
    """
    colors = apply_plot_mode(settings.plot_mode)
    fig, ax = plt.subplots(1, 1)
    if not (settings.has_curves or any(settings.quantiles) or any(settings.sigmas)):
        ax.text(0.1, 0.5, 'Tabula rasa', va='center', fontsize=20)
        ax.set_axis_off()
        return fig

    with np.errstate(all='ignore'):
        pmf = rv.pmf(x)
        if settings.histogram:
            values, counts = np.unique(r, return_counts=True)
            ax.bar(values, counts / len(r), width=0.8, fill=False, edgecolor=colors['hist_edge_color'],
                   linewidth=1, label='Выборка')
        if settings.pdf:
            ax.vlines(x, 0, pmf, color=colors['pdf_line_color'], lw=2, label='PMF')
            ax.plot(x, pmf, linestyle='none', marker='o', markersize=4, color=colors['pdf_line_color'])
        if settings.cdf:
            ax.step(x, rv.cdf(x), where='post', color=colors['cdf_line_color'], lw=1, label='CDF')
        if settings.sf:
            ax.step(x, rv.sf(x), where='post', color='plum', lw=1, label='SF')
        if settings.mark_p:
            probability = rv.cdf(settings.x_cdf)
            ax.plot([settings.x_cdf], [probability], marker='o', color=colors['cdf_line_color'])
            ax.annotate(f'({settings.x_cdf:.0f}, {probability:.2f})', xy=(settings.x_cdf, probability),
                        color=colors['cdf_line_color'])
        quartiles = rv.ppf([0.25, 0.50, 0.75])
        for idx, shown in enumerate(settings.quantiles, start=1):
            if shown:
                ax.axvline(quartiles[idx - 1], color=colors[f'quant{idx}_color'], linestyle=Figure.quantile_dashes,
                           linewidth=2, label=f'Q{idx} = {quartiles[idx - 1]:.0f}', zorder=0)
        mean, std = float(rv.mean()), float(rv.std())
        if np.isfinite(mean) and np.isfinite(std):
            for idx, shown in enumerate(settings.sigmas, start=1):
                if shown:
                    low, high = mean - idx * std, mean + idx * std
                    # вероятность целых значений внутри интервала
                    probability = rv.cdf(np.floor(high)) - rv.cdf(np.ceil(low) - 1)
                    ax.axvspan(low, high, color=colors['pdf_line_color'], alpha=0.12,
                               label=f'{idx}σ: P = {probability:.3f}')

    density = settings.pdf or settings.histogram
    probability = settings.cdf or settings.sf
    ax.set_ylabel('Вероятность значения / накопленная вероятность' if density and probability
                  else 'Накопленная вероятность' if probability else 'Вероятность значения')
    ax.set_xlabel('X значение')
    ax.set_ylim(bottom=0)
    if ax.get_legend_handles_labels()[1]:
        legend = ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2), loc="lower left", mode="expand", borderaxespad=0,
                           ncol=3)
        legend.get_frame().set_edgecolor("#525252")
    return fig


def discrete_interval_figure(rv, x, low, high, plot_mode):
    """
    Вероятности значений с выделенными значениями low < X <= high.
    """
    colors = apply_plot_mode(plot_mode)
    fig, ax = plt.subplots(1, 1, figsize=(6.4, 3.2))
    pmf = rv.pmf(x)
    inside = (x > low) & (x <= high)
    ax.vlines(x[~inside], 0, pmf[~inside], color=colors['hist_edge_color'], lw=2)
    ax.vlines(x[inside], 0, pmf[inside], color=colors['pdf_line_color'], lw=3)
    ax.set_ylim(bottom=0)
    ax.set_xlabel('X значение')
    ax.set_ylabel('Вероятность значения')
    return fig
