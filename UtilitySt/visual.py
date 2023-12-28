import numpy as np
from scipy.stats.mstats import mquantiles
import matplotlib.pyplot as plt


class Figure(object):
    """
    Класс фигуры: используется для отображения реквизитов фигуры и управления ими.
    """

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

    def __init__(self, select_hist,
                 select_pdf_shine, select_cdf_shine, select_sf_shine,
                 select_mark_p, x_cdf, select_boxplot,
                 q1, q2, q3, s1, s2, s3,
                 x, r, rv,
                 plot_mode, select_pdf, select_cdf, select_sf):
        """ Set properties """

        self.select_hist = select_hist
        self.select_pdf_shine = select_pdf_shine
        self.select_cdf_shine = select_cdf_shine
        self.select_sf_shine = select_sf_shine
        self.select_mark_p = select_mark_p
        self.x_cdf = x_cdf
        self.select_boxplot = select_boxplot
        self.q1 = q1
        self.q2 = q2
        self.q3 = q3
        self.s1 = s1
        self.s2 = s2
        self.s3 = s3
        self.x = x
        self.r = r
        self.rv = rv
        self.plot_mode = plot_mode
        self.select_pdf = select_pdf
        self.select_cdf = select_cdf
        self.select_sf = select_sf
        self.colors = self.get_color_scheme(plot_mode)
        self.plt = self.display_mode(plot_mode)

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
            plt.style.use('dark_background')
            plt.rcParams['figure.facecolor'] = 'black'

        elif plot_mode == 'Light Mode':
            plt.style.use('classic')
            plt.rcParams['figure.facecolor'] = 'white'
        else:
            raise ValueError("Invalid mode. Expected 'Dark Mode' or 'Light Mode'")
        return plt

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
                    ax.plot(self.x, func(self.x), '-',
                            color=color,
                            alpha=alpha_value,
                            linewidth=(diff_linewidth * n))

    def pdf_cdf_lines(self, ax):
        """
        Процедура построения линии PDF/CDF и настройка «Shine»
        :param ax:
        :return:
        """
        self.plot_with_shine(ax, self.select_pdf, self.select_pdf_shine, self.colors['pdf_line_color'], self.rv.pdf,
                             'PDF')
        self.plot_with_shine(ax, self.select_cdf, self.select_cdf_shine, self.colors['cdf_line_color'], self.rv.cdf,
                             'CDF')
        # Отметьте точку на CDF
        if self.select_mark_p:
            xmin, xmax = ax.get_xlim()
            ax.vlines(self.x_cdf, ymin=0, ymax=self.rv.cdf(self.x_cdf),
                      color=self.colors['cdf_line_color'],
                      linestyle=':', linewidth=1)
            ax.hlines(self.rv.cdf(self.x_cdf), xmin=xmin,
                      xmax=self.x_cdf, color=self.colors['cdf_line_color'],
                      linestyle=':', linewidth=1)
            ax.annotate(f'({self.x_cdf:.2f}, {self.rv.cdf(self.x_cdf):.2f})',
                        xy=(self.x_cdf, self.rv.cdf(self.x_cdf)),
                        color=self.colors['cdf_line_color'])

        self.plot_with_shine(ax, self.select_sf, self.select_sf_shine, 'plum', self.rv.sf, 'SF')

    def boxplot(self, ax):
        """
        Определите свойства коробчатой диаграммы.
        :param ax:
        :return:
        """
        # Check if self.r is defined and is an array-like object
        if 'r' not in self.__dict__ or not isinstance(self.r, (list, tuple, np.ndarray)):
            raise ValueError("self.r must be defined and be an array-like object")

        bp = ax.boxplot(self.r, patch_artist=True,
                        vert=False,
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
        """ Quantiles and their plot properties. """

        # Compute
        quant = mquantiles(self.r)

        for idx, q in enumerate([self.q1, self.q2, self.q3], start=1):
            if q:
                """ Compute the quantiles and set them as vertical lines. """
                # Plot
                ax.vlines(quant[idx - 1], ymin=0, ymax=self.rv.pdf(quant[idx - 1]),
                          color=self.colors[f'quant{idx}_color'],
                          dashes=self.lines['dashes_r'],
                          linewidth=2, label=f'Q{idx} = {quant[idx - 1]:.2f}',
                          zorder=0, clip_on=False)

                # Label midway
                ax.text(quant[idx - 1], self.rv.pdf(quant[idx - 1]) * 0.5, f'Q{idx}',
                        ha='center', fontsize=10,
                        color=self.colors[f'quant{idx}_color'])

    def sigmas(self, ax):
        """
        Сигмы и их сюжетные свойства.
        :param ax:
        :return:
        """
        for idx, s in enumerate([self.s1, self.s2, self.s3], start=1):
            if s:
                """
                Compute standard deviation and the mean.
                Shade between: mean-std and mean+std which shows sigma.
                """
                x01 = idx * self.r.std()
                # Выберите только значения x в диапазоне сигм.
                x1 = self.x[(self.x > (self.r.mean() - x01)) & (self.x < (x01 + self.r.mean()))]
                # Это затенит 1/2/3 сигмы, ограничивая y на границе PDF.
                ax.fill_between(x1, self.rv.pdf(x1), 0,
                                color=self.colors['pdf_line_color'],
                                alpha=0.2)

    def histogram(self, ax):
        """ Histogram properties """

        ax.hist(self.r, density=True, bins=20,
                edgecolor=self.colors['hist_edge_color'],
                fill=False,  # hatch='x',
                linewidth=1, alpha=1, label='Sample distribution')

    def setup_figure(self, fig_type):
        if fig_type == 'dual':
            fig, ax = plt.subplots(2, 1,
                                   gridspec_kw={'height_ratios': [9, 0.7]})
        else:
            fig, ax = plt.subplots(1, 1)
        return fig, ax

    def plot_lines(self, ax):
        self.pdf_cdf_lines(ax=ax)
        if any([self.q1, self.q2, self.q3]):
            self.quantiles(ax=ax)
        if any([self.s1, self.s2, self.s3]):
            self.sigmas(ax=ax)
        if self.select_hist:
            self.histogram(ax=ax)

    def set_legend(self, ax):
        legend = ax.legend(bbox_to_anchor=(0, 1.02, 1, 0.2),
                           loc="lower left", mode="expand",
                           borderaxespad=0, ncol=3)
        legend.get_frame().set_edgecolor("#525252")

    def figure_display_control(self):
        plt.rcParams.update(self.global_rc_params)

        if self.select_boxplot:
            fig, ax = self.setup_figure('dual')
            self.plot_lines(ax[0])
            self.set_legend(ax[0])

            if not any([self.select_cdf, self.select_pdf, self.select_hist, self.select_sf]):
                fig, ax = self.setup_figure('single')
                self.boxplot(ax=ax)
            else:
                self.boxplot(ax=ax[1])
                ax[1].set_xlim(ax[0].get_xlim())
                ax[0].set_ylabel(self.ylabel)
        else:
            fig, ax = self.setup_figure('single')
            self.plot_lines(ax)
            ax.set_xlabel(self.xlabel)
            ax.set_ylabel(self.ylabel)
            self.set_legend(ax)
        if not any([self.select_cdf, self.select_pdf, self.select_hist, self.select_boxplot, self.select_sf]):
            fig, ax = self.setup_figure('single')
            ax.text(0.1, 0.5, 'Tabula rasa',
                    va='center', fontsize=20)
            ax.spines['left'].set_visible(False)
            ax.spines['bottom'].set_visible(False)
            ax.set_yticklabels([])
            ax.set_yticks([])
            ax.set_xticklabels([])
            ax.set_xticks([])

        return fig
