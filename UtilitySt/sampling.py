import math
from dataclasses import dataclass

import numpy as np
import scipy.stats._distr_params  # noqa: F401 - значения параметров по умолчанию
from scipy import stats

SAMPLE_SIZE = 400
DEFAULT_SEED = 1
# дискретное распределение строится, если почти вся вероятность лежит в пределах этого расстояния от медианы
DISCRETE_SPAN = 1e6


# ошибки, которыми численные методы SciPy сообщают, что не справились с такими параметрами
NUMERIC_ERRORS = (ArithmeticError, ValueError, RuntimeError)


class InvalidParameters(ValueError):
    """Значения параметров, при которых распределение не определено или не может быть построено."""


@dataclass(frozen=True)
class Sample:
    """
    :param x: массив float64 - точки для линий между квантилями 0.001 и 0.999 (у дискретных - целые)
    :param r: массив float64 - случайные числа, сгенерированные из распределения
    :param rv: frozen распределение
    """
    x: np.ndarray
    r: np.ndarray
    rv: object


@dataclass(frozen=True)
class ParameterRange:
    """Диапазон ползунка параметра."""
    min_value: float
    max_value: float
    is_integer: bool


def is_discrete(name):
    return isinstance(getattr(stats, name), stats.rv_discrete)


def integer_parameters(name):
    """
    Параметры, которые должны быть целыми: сдвиг дискретного распределения и параметры формы, которые SciPy
    объявляет целочисленными. Исключение - параметр с дробным значением по умолчанию (n у nbinom):
    SciPy называет его целым, но принимает любое положительное число.
    """
    dist = getattr(stats, name)
    defaults = next((shapes for candidate, shapes in (*stats._distr_params.distcont,
                                                      *stats._distr_params.distdiscrete)
                     if candidate == name), ())
    shape_names = [sh.strip() for sh in dist.shapes.split(',')] if dist.shapes else []
    fractional = {param for param, value in zip(shape_names, defaults, strict=False)
                  if not float(value).is_integer()}
    names = {shape.name for shape in dist._shape_info() if shape.integrality} - fractional
    if is_discrete(name):
        names.add('loc')
    return names


def discrete_grid(rv, limit=2000):
    """
    Целые точки между квантилями 0.001 и 0.999. Если их больше limit, сетка прореживается.
    """
    # У очень тяжелого хвоста квантиль 0.999 уходит на десятки порядков, и SciPy ищет его перебором
    # неприемлемо долго. Сначала дешево проверяем по функции распределения, что он в разумных пределах.
    median = float(rv.ppf(0.5))
    if rv.cdf(median + DISCRETE_SPAN) < 0.999 or rv.cdf(median - DISCRETE_SPAN) > 0.001:
        raise InvalidParameters(f'хвост распределения слишком тяжелый: 99.8% вероятности не помещаются '
                                f'в диапазон шириной {2 * DISCRETE_SPAN:.0e} значений')
    low, high = rv.ppf(0.001), rv.ppf(0.999)
    if not (np.isfinite(low) and np.isfinite(high) and low <= high):
        raise InvalidParameters('при этих значениях не вычисляются квантили распределения')
    if high - low < limit:
        return np.arange(low, high + 1)
    return np.unique(np.round(np.linspace(low, high, limit)))


def curve_grid(rv, size=SAMPLE_SIZE):
    """
    Точки для линий: равномерная сетка по x плюс сетка, равномерная по вероятности.
    Вторая сгущается там, где сосредоточена масса, поэтому узкий пик (cauchy, levy) не теряется.
    """
    low, high = rv.ppf(0.001), rv.ppf(0.999)
    if not (np.isfinite(low) and np.isfinite(high) and low < high):
        raise InvalidParameters('при этих значениях не вычисляются квантили распределения')
    return np.union1d(np.linspace(low, high, size), rv.ppf(np.linspace(0.001, 0.999, size)))


def sample_distribution(name, parameters, seed=DEFAULT_SEED, size=SAMPLE_SIZE):
    """
    :param name: имя распределения в scipy.stats
    :param parameters: значения параметров в порядке SciPy: параметры формы, затем loc и scale
                       (у дискретных распределений scale нет)
    :param seed: зерно генератора; одинаковое зерно дает одинаковую выборку
    :raises InvalidParameters: если распределение с такими параметрами не определено
    """
    dist = getattr(stats, name)
    discrete = is_discrete(name)
    if discrete:
        # у дискретных распределений нет scale, а сдвиг и часть параметров формы целые
        shape_names = list(parameters)[:-1]
        integral = integer_parameters(name)
        for param in integral:
            if parameters[param] != round(parameters[param]):
                raise InvalidParameters(f'параметр {param} должен быть целым')
        shapes = [int(parameters[param]) if param in integral else parameters[param] for param in shape_names]
        frozen_arguments = {'loc': int(parameters['loc'])}
    else:
        shape_names = list(parameters)[:-2]
        shapes = [parameters[param] for param in shape_names]
        if parameters['scale'] <= 0:
            raise InvalidParameters('scale должен быть больше нуля')
        frozen_arguments = {'loc': parameters['loc'], 'scale': parameters['scale']}
    with np.errstate(all='ignore'):
        if not np.all(dist._argcheck(*shapes)):
            shape_values = ', '.join(f'{param} = {parameters[param]}' for param in shape_names)
            raise InvalidParameters(f'недопустимые значения параметров формы ({shape_values})')
        rv = dist(*shapes, **frozen_arguments)
        # на краях области определения численные методы SciPy могут не сойтись или переполниться
        try:
            x = discrete_grid(rv) if discrete else curve_grid(rv, size)
            r = rv.rvs(size=size, random_state=seed)
        except NUMERIC_ERRORS as e:
            raise InvalidParameters(f'SciPy не смог вычислить распределение: {e}') from e
    if not np.all(np.isfinite(r)):
        raise InvalidParameters('выборка содержит бесконечные значения')
    return Sample(x=x, r=r, rv=rv)


def parameter_range(name, param, default, step):
    """
    Диапазон ползунка: область определения параметра из SciPy, обрезанная до окна вокруг значения по умолчанию.
    Границы лежат на сетке, кратной шагу, поэтому круглые значения (1.0, 2.0) достижимы.
    :param name: имя распределения в scipy.stats
    :param param: имя параметра ('loc', 'scale' или параметр формы)
    :param default: значение по умолчанию из SciPy
    :param step: шаг ползунка
    """
    is_integer = False
    # граница 0 у scale не входит в область определения
    low_is_open = param == 'scale'
    if param == 'loc':
        low, high = -math.inf, math.inf
        is_integer = is_discrete(name)
    elif param == 'scale':
        low, high = 0.0, math.inf
    else:
        shape = next((shape for shape in getattr(stats, name)._shape_info() if shape.name == param), None)
        if shape is None:
            # SciPy не описывает область определения: считаем положительный параметр положительным
            low, high = (0.0, math.inf) if default > 0 else (-math.inf, math.inf)
            low_is_open = default > 0
        else:
            low, high = shape.domain
            # параметр с дробным значением по умолчанию целым не считаем (n у nbinom)
            is_integer = bool(shape.integrality) and float(default).is_integer()
    if is_integer:
        step = 1

    if math.isfinite(low):
        # наименьшее значение на сетке шага, которое лежит в области определения;
        # SciPy записывает открытую границу как соседнее число (5e-324, 1.0000000000000002)
        min_value = math.ceil(low / step - 1e-9) * step
        if min_value <= low and (low_is_open or low != round(low)):
            min_value += step
    else:
        min_value = min(-10.0, 2 * default)
    if math.isfinite(high):
        max_value = math.floor(high / step + 1e-9) * step
        if max_value >= high and high != round(high):
            max_value -= step
    else:
        max_value = max(10.0, 2 * default)

    min_value, max_value = min(min_value, default), max(max_value, default)
    if is_integer:
        return ParameterRange(int(min_value), int(max_value), True)
    return ParameterRange(round(min_value, 2), round(max_value, 2), False)
