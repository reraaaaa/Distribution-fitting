import time

import matplotlib
import numpy
import scipy

from .sampling import DEFAULT_SEED, SAMPLE_SIZE

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
        *shape_names, loc, scale = self.parameters
        # сначала scale и loc, затем параметры формы по одному на строку
        assignments = [f'{name}={self.parameters[name]}' for name in [scale, loc, *shape_names]]
        # параметры формы позиционно, loc и scale по имени: "a, b, loc=loc, scale=scale"
        arguments = [*shape_names, f'{loc}={loc}', f'{scale}={scale}']
        return TEMPLATE.format(timestamp=time.strftime("%Y%m%d_%H%M%S"),
                               matplotlib_version=matplotlib.__version__,
                               numpy_version=numpy.__version__,
                               scipy_version=scipy.__version__,
                               distribution=self.distribution,
                               seed=self.seed,
                               size=SAMPLE_SIZE,
                               assignments='\n'.join(assignments),
                               arguments=', '.join(arguments))
