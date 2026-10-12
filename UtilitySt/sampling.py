from dataclasses import dataclass

import numpy as np
from scipy import stats

SAMPLE_SIZE = 400


@dataclass(frozen=True)
class Sample:
    """
    :param x: массив float64 - равномерно расположенные числа между квантилями 0.001 и 0.999
    :param r: массив float64 - случайные числа, сгенерированные из распределения
    :param rv: frozen распределение
    """
    x: np.ndarray
    r: np.ndarray
    rv: object


def sample_distribution(name, parameters, size=SAMPLE_SIZE):
    """
    :param name: имя распределения в scipy.stats
    :param parameters: значения параметров в порядке SciPy: параметры формы, затем loc и scale
    """
    dist = getattr(stats, name)
    *shapes, loc, scale = parameters.values()
    rv = dist(*shapes, loc=loc, scale=scale)
    x = np.linspace(rv.ppf(0.001), rv.ppf(0.999), size)
    r = rv.rvs(size=size)
    return Sample(x=x, r=r, rv=rv)
