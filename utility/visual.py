import streamlit as st
import matplotlib.pyplot as plt


class Figure:
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

    def get_color_scheme(self, mode):
        """
        Get color scheme based on mode
        :param mode: The mode ('Dark Mode' or 'Light Mode')
        :return: A dictionary with color scheme
        """
        if mode == 'Dark Mode':
            return {
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
        else:  # 'Light Mode'
            return {
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

    def __init__(self, x, r, rv, xlabel, ylabel,
                 plot_mode, global_rc_params, lines):
        """
        Установка Cвойств
        :param x:
        :param r:
        :param rv:
        :param xlabel:
        :param ylabel:
        :param plot_mode:
        :param global_rc_params:
        :param lines:
        """
        self.x = x
        self.r = r
        self.rv = rv
        self.xlabel = xlabel
        self.ylabel = ylabel
        self.plot_mode = plot_mode
        self.global_rc_params = global_rc_params
        self.lines = lines
        self.colors = self.get_color_scheme(plot_mode)

    def display_mode(self):
        """
        rc Параметры для светлого и темного режима
        :return:
        """

        plot_mode = self.plot_mode

        if plot_mode == 'Dark Mode':
            plt.style.use('dark_background')
            plt.rcParams['figure.facecolor'] = 'black'

        if plot_mode == 'Light Mode':
            plt.style.use('classic')
            plt.rcParams['figure.facecolor'] = 'white'

    def draw_line(self, ax, line_func, color_key, label, select_shine):
        """
        Рисуем линию с дополнительным эффектом блеска
        :param ax: Оси, на которых рис
        :param line_func: Функция для генерации значений y
        :param color_key: Ключ для получения цвета линии из self.colors
        :param label: Метка для линии
        :param select_shine: Добавлять ли эффект блеска
        """
        n_lines = 5
        diff_linewidth = 3
        alpha_value = 0.1

        ax.plot(self.x, line_func(self.x),
                linestyle='-',
                color=self.colors[color_key],
                lw=1,
                label=label)

        if select_shine:
            for n in range(1, n_lines):
                ax.plot(self.x, line_func(self.x), '-',
                        color=self.colors[color_key],
                        alpha=alpha_value,
                        linewidth=(diff_linewidth * n))

    def mark_point_on_cdf(self, ax, x_cdf):
        """
        Отметить точку на CDF
        :param ax: Оси, на которые можно опираться
        :param x_cdf: Значение x точки на CDF
        """
        xmin, xmax = ax.get_xlim()
        ax.vlines(x_cdf,
                  ymin=0,
                  ymax=self.rv.cdf(x_cdf),
                  color=self.colors['cdf_line_color'],
                  linestyle=':',
                  linewidth=1)
        ax.hlines(self.rv.cdf(x_cdf),
                  xmin=xmin,
                  xmax=x_cdf,
                  color=self.colors['cdf_line_color'],
                  linestyle=':',
                  linewidth=1)
        ax.annotate(f'({x_cdf:.2f},'f'{self.rv.cdf(x_cdf):.2f})',
                    xy=(x_cdf, self.rv.cdf(x_cdf)),
                    color=self.colors['cdf_line_color'])

    def pdf_cdf_lines(self, ax):
        """
        Как построить линии PDF/CDF и настроить «Сияние»
        :param ax:
        """
        options = {
            'pdf': {'select': select_pdf, 'func': self.rv.pdf, 'color_key': 'pdf_line_color', 'label': 'PDF',
                    'shine': select_pdf_shine},
            'cdf': {'select': select_cdf, 'func': self.rv.cdf, 'color_key': 'cdf_line_color', 'label': 'CDF',
                    'shine': select_cdf_shine},
            'sf': {'select': select_sf, 'func': self.rv.sf, 'color_key': 'plum', 'label': 'SF',
                   'shine': select_sf_shine}
        }

        for option in options.values():
            if option['select']:
                self.draw_line(ax, option['func'], option['color_key'], option['label'], option['shine'])

                if option['label'] == 'CDF' and select_mark_P:
                    self.mark_point_on_cdf(ax, x_cdf)

    def boxplot(self, ax):
        """
        Определите свойства коробчатой boxplot диаграммы.
        """
        bp = ax.boxplot(self.r,
                        patch_artist=True,
                        vert=False,
                        notch=False,
                        showfliers=False
                        )

        for element in ['boxes', 'whiskers', 'fliers', 'means', 'medians', 'caps']:
            plt.setp(bp[element], color=self.colors['boxplot_lines_color'])
        for patch in bp['boxes']:
            patch.set(facecolor=self.colors['boxplot_face_color'])
        # Переместить метку x ниже — она будет активна, если отображается boxplot диаграмма.
        ax.set_xlabel(self.xlabel)
        # В дополнение к глобальным rcParams установим параметры графика:
        ax.spines['left'].set_visible(False)
        ax.set_yticklabels([])
        ax.set_yticks([])
        ax.set_ylim(0.9, 1.1)

    def quantiles(self, ax):
        """
        Квантили и их свойства.
        :param ax:
        """
        def get_line(self, q):
            """
            Вычисление квантилей и расположение их в виде вертикальных линий.
            :param q:
            :return:
            """
            # Вычислить
            quant = mquantiles(self.r)
            # Plot
            ax.vlines(quant[ q -1],
                      ymin=0,
                      ymax=self.rv.pdf(quant[ q -1]),
                      color=self.colors[f'quant{q}_color'],
                      dashes = self.lines['dashes_r'],
                      linewidth=2,
                      label=f'Q{q} = {quant[ q -1]:.2f}',
                      zorder=0,
                      clip_on=False)
            # Ярлык посередине
            ax.text(quant[ q -1], self.rv.pdf(quant[ q -1] ) *0.5, f'Q{q}',
                    ha='center',
                    fontsize=10,
                    color=self.colors[f'quant{q}_color'])
        # Streamlit control - checkboxes for Q1/2/3: on/off
        for q in [1, 2, 3]:
            if globals()[f'q{q}']:
                get_line(self, q)

    def sigmas(self, ax):
        """
        Сигмы и их свойства.
        :param ax:
        """
        # Нужно посчитать дополнительно с помощью функции!
        def which_s(self, s):
            """
            Вычислите стандартное отклонение и среднее значение.
            Раст между: среднее-стандартное и среднее + стандартное, что показывает сигму.
            """
            x01 = s*self.r.std( )
            # Выберите только значения x в диапазоне сигм.
            x1 = self.x[ (self.x > (self.r.mean()-x01)) & (self.x < (x01+self.r.mean()))]
            # Это затенит 1/2/3 сигмы, ограничивая y на границе PDF.
            ax.fill_between(x1,
                            self.rv.pdf(x1),
                            0,
                            color=self.colors['pdf_line_color'],
                            alpha=0.2)
        # Streamlit control - checkboxes for sigma1/2/3: on/off
        if s1:
            s= 1
            which_s(self, s)
        if s2:
            s= 2
            which_s(self, s)
        if s3:
            s= 3
            which_s(self, s)

    def histogram(self, ax):
        """ Histogram properties """

        ax.hist(self.r, density=True, bins=20,
                edgecolor=self.colors['hist_edge_color'],
                fill =False,  # hatch='x',
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
            fig, ax = plt.subplots(1,1 )
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

            legend = ax[0].legend(bbox_to_anchor=(0,1 .02,1 ,0 .2),
                                  loc="lower left", mode="expand",
                                  borderaxespad=0, ncol=3)
            legend.get_frame().set_edgecolor("#525252")

            # In case all distribution prop. from ax[0] are off set the
            # boxplot on the ax[0] if the boxplot is on.
            if (select_cdf == False and select_pdf == False \ \
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

            legend = ax.legend(bbox_to_anchor=(0 ,1.02 ,1 ,0.2),
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
