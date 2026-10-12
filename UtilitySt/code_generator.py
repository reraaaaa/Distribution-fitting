import time

import matplotlib
import numpy
import scipy

from .sampling import DEFAULT_SEED, SAMPLE_SIZE, integer_parameters, is_discrete

TEMPLATE = """\
# -*- coding: utf-8 -*-
# {timestamp}
# ---

import matplotlib.pyplot as plt  # v{matplotlib_version}
import numpy as np  # v{numpy_version}
from scipy.stats import {distribution}  # v{scipy_version}

# Параметры распределения
{assignments}

# Зерно генератора: с ним выборка совпадает с той, что показана в приложении
seed = {seed}
size = {size}

# Замороженное распределение
rv = {distribution}({arguments})

# Точки для линий между квантилями 0.001 и 0.999: равномерная сетка по x
# плюс сетка, равномерная по вероятности (она не пропускает узкий пик)
x = np.union1d(np.linspace(rv.ppf(0.001), rv.ppf(0.999), size),
               rv.ppf(np.linspace(0.001, 0.999, size)))

# Случайная выборка
r = rv.rvs(size=size, random_state=seed)

# Рисунок
fig, ax = plt.subplots(2, 1,
                       gridspec_kw={{'height_ratios': [9, 0.7]}})

# PDF, CDF и SF
ax[0].plot(x, rv.pdf(x), linestyle='-', color='#3182bd', lw=3, label='PDF')
ax[0].plot(x, rv.cdf(x), linestyle='-', color='k', lw=3, label='CDF')
ax[0].plot(x, rv.sf(x), linestyle='-', color='#df65b0', lw=3, label='SF')

# Гистограмма выборки
ax[0].hist(r, density=True, bins=20, color='lightgrey',
           edgecolor='k', label='Выборка')

# Блочная диаграмма выборки
bp = ax[1].boxplot(r, patch_artist=True,
           orientation='horizontal',
           notch=False,
           showfliers=False,
           )
# Оформление блочной диаграммы
for median in bp['medians']: median.set(color ='red', linewidth = 2)
for patch in bp['boxes']: patch.set(facecolor='white')

# Легенда
ax[0].legend(bbox_to_anchor=(0,1.1,1,0.2),
             loc="center",
             borderaxespad=0, ncol=2)

# Оформление рисунка
ax[0].spines['top'].set_visible(False)
ax[0].spines['right'].set_visible(False)
ax[0].set_title('Распределение: {distribution}')

ax[1].set_xlim(ax[0].get_xlim())
ax[1].set_ylim(0.9, 1.1)
ax[1].spines['left'].set_visible(False)
ax[1].spines['top'].set_visible(False)
ax[1].spines['right'].set_visible(False)
ax[1].set_yticklabels([])
ax[1].set_yticks([])

ax[1].set_xlabel('X значение')
ax[0].set_ylabel('Плотность / вероятность')

plt.show()
"""


DISCRETE_TEMPLATE = """\
# -*- coding: utf-8 -*-
# {timestamp}
# ---

import matplotlib.pyplot as plt  # v{matplotlib_version}
import numpy as np  # v{numpy_version}
from scipy.stats import {distribution}  # v{scipy_version}

# Параметры распределения
{assignments}

# Зерно генератора: с ним выборка совпадает с той, что показана в приложении
seed = {seed}
size = {size}

# Замороженное распределение
rv = {distribution}({arguments})

# Целые значения между квантилями 0.001 и 0.999
x = np.arange(rv.ppf(0.001), rv.ppf(0.999) + 1)

# Случайная выборка
r = rv.rvs(size=size, random_state=seed)

# Рисунок
fig, ax = plt.subplots()

# Частоты значений в выборке
values, counts = np.unique(r, return_counts=True)
ax.bar(values, counts / size, width=0.8, color='lightgrey', edgecolor='k', label='Выборка')

# Вероятности значений (PMF), функция распределения (CDF) и функция выживания (SF)
ax.vlines(x, 0, rv.pmf(x), color='#3182bd', lw=3, label='PMF')
ax.step(x, rv.cdf(x), where='post', color='k', lw=1.5, label='CDF')
ax.step(x, rv.sf(x), where='post', color='#df65b0', lw=1.5, label='SF')

# Оформление рисунка
ax.legend(bbox_to_anchor=(0, 1.1, 1, 0.2), loc="center", borderaxespad=0, ncol=4)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.set_title('Распределение: {distribution}')
ax.set_xlabel('X значение')
ax.set_ylabel('Вероятность')

plt.show()
"""


class CodeGenerator(object):
    """
    Генерирует самостоятельный скрипт Python, который строит выбранное распределение.
    :param distribution: имя распределения в scipy.stats, например 'beta'
    :param parameters: значения параметров в порядке SciPy: параметры формы, затем loc и scale,
                       например {'a': 2.31, 'b': 0.63, 'loc': 0.0, 'scale': 1.0}
    :param seed: зерно генератора; скрипт строит ту же выборку, что sample_distribution с этим зерном
    """
    def __init__(self, distribution, parameters, seed=DEFAULT_SEED):
        self.distribution = distribution
        self.parameters = parameters
        self.seed = seed

    def get_generated_code(self):
        discrete = is_discrete(self.distribution)
        # у дискретных распределений нет scale: параметры формы, затем loc
        common = ['loc'] if discrete else ['scale', 'loc']
        shape_names = [name for name in self.parameters if name not in common]
        integral = integer_parameters(self.distribution)

        def literal(name):
            value = self.parameters[name]
            return str(int(value)) if name in integral else str(value)

        # сначала scale и loc, затем параметры формы по одному на строку
        assignments = [f'{name}={literal(name)}' for name in [*common, *shape_names]]
        # параметры формы позиционно, loc и scale по имени: "a, b, loc=loc, scale=scale"
        arguments = [*shape_names, *(f'{name}={name}' for name in reversed(common))]
        template = DISCRETE_TEMPLATE if discrete else TEMPLATE
        return template.format(timestamp=time.strftime("%Y%m%d_%H%M%S"),
                               matplotlib_version=matplotlib.__version__,
                               numpy_version=numpy.__version__,
                               scipy_version=scipy.__version__,
                               distribution=self.distribution,
                               seed=self.seed,
                               size=SAMPLE_SIZE,
                               assignments='\n'.join(assignments),
                               arguments=', '.join(arguments))


FIT_TEMPLATE = """\
# -*- coding: utf-8 -*-
# {timestamp}
# ---
# Подбор параметров распределения {distribution} методом максимального правдоподобия.
# Рядом со скриптом должен лежать файл {data_file}: одно число в строке.

import matplotlib.pyplot as plt  # v{matplotlib_version}
import numpy as np  # v{numpy_version}
from scipy import stats  # v{scipy_version}

data = np.loadtxt('{data_file}')

# Оценка параметров (в порядке SciPy: {parameter_names})
parameters = stats.{distribution}.fit(data{fit_arguments})
rv = stats.{distribution}(*parameters)
for name, value in zip({parameter_list}, parameters):
    print(f'{{name}} = {{value:.6g}}')

# Показатели качества подгонки
log_likelihood = np.sum(rv.logpdf(data))
n_free = {n_free}
print(f'ln L = {{log_likelihood:.3f}}')
print(f'AIC = {{2 * n_free - 2 * log_likelihood:.3f}}')
print(f'BIC = {{n_free * np.log(len(data)) - 2 * log_likelihood:.3f}}')
# Статистика Колмогорова - Смирнова. Ее табличное p-значение завышено: параметры оценены по тем же данным
print(f'KS = {{stats.kstest(data, rv.cdf).statistic:.4f}}')

# Гистограмма данных и подобранная плотность
x = np.linspace(data.min(), data.max(), 800)
fig, ax = plt.subplots()
ax.hist(data, bins='fd', density=True, color='lightgrey', edgecolor='k', label='Данные')
ax.plot(x, rv.pdf(x), color='#3182bd', lw=2, label='{distribution}')
ax.set_xlabel('X значение')
ax.set_ylabel('Плотность')
ax.legend()

plt.show()
"""


class FitCodeGenerator(object):
    """
    Генерирует скрипт, который повторяет подгонку распределения к данным из файла.
    :param result: FitResult подобранного распределения
    :param fix_loc: был ли зафиксирован loc = 0
    :param data_file: имя файла с данными, который скачивается вместе со скриптом
    """
    def __init__(self, result, fix_loc=False, data_file='data.csv'):
        self.result = result
        self.fix_loc = fix_loc
        self.data_file = data_file

    def get_generated_code(self):
        names = list(self.result.parameters)
        return FIT_TEMPLATE.format(timestamp=time.strftime("%Y%m%d_%H%M%S"),
                                   matplotlib_version=matplotlib.__version__,
                                   numpy_version=numpy.__version__,
                                   scipy_version=scipy.__version__,
                                   distribution=self.result.name,
                                   data_file=self.data_file,
                                   parameter_names=', '.join(names),
                                   parameter_list=repr(names),
                                   fit_arguments=', floc=0.0' if self.fix_loc else '',
                                   n_free=self.result.n_free)
