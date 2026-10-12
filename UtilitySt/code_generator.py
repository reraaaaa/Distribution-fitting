import time

TEMPLATE = """\
# -*- coding: utf-8 -*-
# {timestamp}
# ---

import matplotlib.pyplot as plt #v3.2.2
import numpy as np #v1.18.5
from scipy.stats import {distribution} #v1.6.1

# Set random seed
np.random.seed(1)

# Function parameters
{assignments}

# Генерировать равномерно числа в течение указанного интервала
size = 400
x = np.linspace({distribution}.ppf(0.001, {arguments}),
                {distribution}.ppf(0.999, {arguments}),
                size)

# Freeze the distribution
rv = {distribution}({arguments})

# Generate random numbers
r = {distribution}.rvs({arguments}, size=size)

# Make a plot
fig, ax = plt.subplots(2, 1,
                       gridspec_kw={{'height_ratios': [9, 0.7]}})

# Plot PDF, CDF and SF
ax[0].plot(x, rv.pdf(x), linestyle='-', color='#3182bd', lw=3, label='PDF')
ax[0].plot(x, rv.cdf(x), linestyle='-', color='k', lw=3, label='CDF')
ax[0].plot(x, rv.sf(x), linestyle='-', color='#df65b0', lw=3, label='SF')

# Plot Histogram
ax[0].hist(r, density=True, bins=20, color='lightgrey',
           edgecolor='k', label='Sample')

# Plot Boxplot
bp = ax[1].boxplot(r, patch_artist=True,
           vert=False,
           notch=False,
           showfliers=False,
           )
# Boxplot aestetic
for median in bp['medians']: median.set(color ='red', linewidth = 2)
for patch in bp['boxes']: patch.set(facecolor='white')

# Set legend
ax[0].legend(bbox_to_anchor=(0,1.1,1,0.2),
             loc="center",
             borderaxespad=0, ncol=2)

# Set Figure aestetics
ax[0].spines['top'].set_visible(False)
ax[0].spines['right'].set_visible(False)
ax[0].set_title('Distribution: {distribution}')

ax[1].set_xlim(ax[0].get_xlim())
ax[1].set_ylim(0.9, 1.1)
ax[1].spines['left'].set_visible(False)
ax[1].spines['top'].set_visible(False)
ax[1].spines['right'].set_visible(False)
ax[1].set_yticklabels([])
ax[1].set_yticks([])

ax[1].set_xlabel('X value')
ax[0].set_ylabel('Density')

plt.show()
"""


class CodeGenerator(object):
    """
    Генерирует самостоятельный скрипт Python, который строит выбранное распределение.
    :param distribution: имя распределения в scipy.stats, например 'beta'
    :param parameters: значения параметров в порядке SciPy: параметры формы, затем loc и scale,
                       например {'a': 2.31, 'b': 0.63, 'loc': 0.0, 'scale': 1.0}
    """
    def __init__(self, distribution, parameters):
        self.distribution = distribution
        self.parameters = parameters

    def get_generated_code(self):
        *shape_names, loc, scale = self.parameters
        # сначала scale и loc, затем параметры формы по одному на строку
        assignments = [f'{name}={self.parameters[name]}' for name in [scale, loc, *shape_names]]
        # параметры формы позиционно, loc и scale по имени: "a, b, loc=loc, scale=scale"
        arguments = [*shape_names, f'{loc}={loc}', f'{scale}={scale}']
        return TEMPLATE.format(timestamp=time.strftime("%Y%m%d_%H%M%S"),
                               distribution=self.distribution,
                               assignments='\n'.join(assignments),
                               arguments=', '.join(arguments))
