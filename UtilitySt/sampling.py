import math
from dataclasses import dataclass

import numpy as np
from scipy import stats

SAMPLE_SIZE = 400
DEFAULT_SEED = 1


# ошибки, которыми численные методы SciPy сообщают, что не справились с такими параметрами
NUMERIC_ERRORS = (ArithmeticError, ValueError, RuntimeError)


class InvalidParameters(ValueError):
    """Значения параметров, при которых распределение не определено или не может быть построено."""


@dataclass(frozen=True)
class Sample:
    """
    :param x: массив float64 - точки для линий между квантилями 0.001 и 0.999
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
    :param seed: зерно генератора; одинаковое зерно дает одинаковую выборку
    :raises InvalidParameters: если распределение с такими параметрами не определено
    """
    dist = getattr(stats, name)
    *shapes, loc, scale = parameters.values()
    if scale <= 0:
        raise InvalidParameters('scale должен быть больше нуля')
    with np.errstate(all='ignore'):
        if not np.all(dist._argcheck(*shapes)):
            shape_values = ', '.join(f'{param} = {value}' for param, value in list(parameters.items())[:-2])
            raise InvalidParameters(f'недопустимые значения параметров формы ({shape_values})')
        rv = dist(*shapes, loc=loc, scale=scale)
        # на краях области определения численные методы SciPy могут не сойтись или переполниться
        try:
            x = curve_grid(rv, size)
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
            is_integer = bool(shape.integrality)
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
