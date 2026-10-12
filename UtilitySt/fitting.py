"""Подбор закона распределения по данным. Чистые функции, без Streamlit."""
import io
import math
import re
import time
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats

# Распределения, выбранные по умолчанию
DEFAULT_DISTRIBUTIONS = ['norm', 'lognorm', 'gamma', 'expon', 'weibull_min', 'beta', 't', 'logistic',
                         'uniform', 'cauchy']

MIN_OBSERVATIONS = 10
MAX_OBSERVATIONS = 100_000
# подгонка идет не более чем по стольким наблюдениям (случайная подвыборка)
MAX_FIT_OBSERVATIONS = 10_000
# распределение пропускается, если оценка времени его подгонки больше лимита, секунд
TIME_LIMIT = 15.0

EXAMPLE_PARAMETERS = {'a': 2.5, 'loc': 1.0, 'scale': 2.0}


class DataError(ValueError):
    """Данные, по которым нельзя подбирать распределение."""


@dataclass(frozen=True)
class FitResult:
    """
    Результат подгонки одного распределения.
    :param name: имя распределения в scipy.stats
    :param parameters: оценки параметров в порядке SciPy: параметры формы, затем loc и scale
    :param n_free: число оцененных параметров (зафиксированный loc не считается)
    :param log_likelihood: логарифм правдоподобия в точке оценки
    :param aic, bic: информационные критерии, меньше - лучше
    :param ks_statistic, ks_pvalue: критерий Колмогорова - Смирнова; p-значение завышено,
           потому что параметры оценены по тем же данным
    :param sse: сумма квадратов отклонений плотности от гистограммы данных
    :param skipped: причина, по которой распределение не подобрано ('' если подобрано)
    """
    name: str
    parameters: dict = field(default_factory=dict)
    n_free: int = 0
    log_likelihood: float = math.nan
    aic: float = math.nan
    bic: float = math.nan
    ks_statistic: float = math.nan
    ks_pvalue: float = math.nan
    sse: float = math.nan
    skipped: str = ''

    @property
    def ok(self):
        return not self.skipped

    def frozen(self):
        """
        :return: frozen распределение с подобранными параметрами
        """
        return getattr(stats, self.name)(*self.parameters.values())


def example_data(size=500, seed=1):
    """
    Пример данных: выборка из гамма-распределения с параметрами EXAMPLE_PARAMETERS.
    """
    return stats.gamma(*EXAMPLE_PARAMETERS.values()).rvs(size=size, random_state=seed)


def decode(raw):
    """
    Текст файла: UTF-8 (с BOM или без), иначе Windows-1251, в которой сохраняет русский Excel.
    """
    for encoding in ('utf-8-sig', 'cp1251'):
        try:
            text = raw.decode(encoding)
        except UnicodeDecodeError:
            continue
        if '\x00' not in text:
            return text
    raise DataError('файл не похож на текстовый: это не CSV и не TXT')


def detect_separator(lines):
    """
    Разделитель столбцов. Запятая неоднозначна: в файлах из русского Excel это десятичный разделитель.
    Если каждая строка - одно число с запятой ("1,5"), считаем файл одним столбцом.
    :return: разделитель для pandas или None для файла из одного столбца
    """
    if any(';' in line for line in lines):
        return ';'
    if any('\t' in line for line in lines):
        return '\t'
    if any(',' in line for line in lines):
        # первая строка может быть заголовком без запятой
        body = lines[1:] if ',' not in lines[0] else lines
        if body and all(re.fullmatch(r'[-+]?\d+,\d+', line) for line in body):
            return None
        return ','
    if any(re.search(r'\S\s+\S', line) for line in lines):
        return r'\s+'
    return None


def read_table(file):
    """
    Читает CSV или TXT в таблицу строк; числа из них достает to_numeric.
    Файл без строки заголовка распознается по тому, что вся первая строка - числа.
    :param file: байты или файловый объект
    :raises DataError: если файл не читается как таблица
    """
    raw = file if isinstance(file, (bytes, bytearray)) else file.read()
    lines = [line.strip() for line in decode(raw).splitlines() if line.strip()]
    if not lines:
        raise DataError('в файле нет данных')
    separator = detect_separator(lines[:200])
    try:
        if separator is None:
            table = pd.DataFrame({0: lines})
        else:
            table = pd.read_csv(io.StringIO('\n'.join(lines)), sep=separator, header=None, dtype=str,
                                engine='python')
    except Exception as e:
        raise DataError(f'файл не удалось прочитать как таблицу: {e}') from e

    if all(_is_number(value) for value in table.iloc[0].dropna()):
        table.columns = [f'Столбец {i + 1}' for i in range(table.shape[1])]
    else:
        table.columns = [str(value).strip() for value in table.iloc[0].fillna('')]
        table = table.iloc[1:].reset_index(drop=True)
    if table.empty:
        raise DataError('в файле нет данных')
    return table


def _is_number(value):
    try:
        float(str(value).replace(',', '.'))
    except ValueError:
        return False
    return True


def to_numeric(column):
    """
    Числа из столбца; запятая как десятичный разделитель тоже понимается. Нечисловые значения становятся NaN.
    """
    if pd.api.types.is_numeric_dtype(column):
        return pd.to_numeric(column, errors='coerce')
    return pd.to_numeric(column.astype(str).str.strip().str.replace(',', '.', regex=False), errors='coerce')


def numeric_columns(table):
    """
    :return: названия столбцов, в которых хватает чисел для подбора
    """
    return [column for column in table.columns
            if np.isfinite(to_numeric(table[column])).sum() >= MIN_OBSERVATIONS]


def clean_data(values):
    """
    Оставляет конечные числа и проверяет, что по ним можно подбирать распределение.
    :return: (массив float64, сколько значений отброшено)
    :raises DataError: мало наблюдений, слишком много наблюдений или все значения одинаковы
    """
    numbers = to_numeric(pd.Series(values)).to_numpy(dtype=float)
    data = numbers[np.isfinite(numbers)]
    dropped = len(numbers) - len(data)
    if len(data) < MIN_OBSERVATIONS:
        raise DataError(f'нужно не меньше {MIN_OBSERVATIONS} чисел, найдено {len(data)}')
    if len(data) > MAX_OBSERVATIONS:
        raise DataError(f'слишком много наблюдений: {len(data)}, допускается до {MAX_OBSERVATIONS}')
    if np.ptp(data) == 0:
        raise DataError('все значения одинаковы, распределение подобрать нельзя')
    return data, dropped


def fitting_sample(data, limit=MAX_FIT_OBSERVATIONS, seed=1):
    """
    Подвыборка для подгонки: все данные, если их не больше limit, иначе случайные limit наблюдений.
    """
    if len(data) <= limit:
        return data
    return np.random.default_rng(seed).choice(data, size=limit, replace=False)


def looks_discrete(data):
    """
    Целые значения с малым числом уникальных - скорее всего, дискретная величина (счетчик, оценка),
    для которой непрерывное распределение не подходит.
    """
    return bool(np.all(data == np.round(data)) and len(np.unique(data)) < 20)


def histogram(data):
    """
    Гистограмма плотности данных. Число столбцов - по правилу Фридмана - Диакониса, но не больше 100.
    :return: (плотность, границы столбцов)
    """
    edges = np.histogram_bin_edges(data, bins='fd')
    if len(edges) - 1 > 100:
        edges = np.histogram_bin_edges(data, bins=100)
    return np.histogram(data, bins=edges, density=True)


def estimated_fit_seconds(dist, data):
    """
    Оценка времени подгонки сверху: время одного вычисления функции правдоподобия на всех данных,
    умноженное на предельное число итераций оптимизатора SciPy (200 на параметр).
    """
    try:
        start = dist._fitstart(data)
    except Exception:
        start = (1.0,) * dist.numargs + (0.0, 1.0)
    # первый вызов прогревает внутренние структуры SciPy и сразу показывает очень медленные распределения
    began = time.perf_counter()
    dist.nnlf(start, data[:5])
    warmup = time.perf_counter() - began
    if warmup > 0.5:
        return math.inf
    probe = data[:500]
    began = time.perf_counter()
    dist.nnlf(start, probe)
    per_observation = (time.perf_counter() - began) / len(probe)
    return per_observation * len(data) * 200 * len(start)


def probability_mass_over_data(dist, estimates, data):
    """
    Интеграл подобранной плотности по диапазону данных. У настоящей плотности он не больше 1.
    Больше 1 он бывает у круговых распределений (vonmises: плотность периодична, а данные шире периода)
    и при численных ошибках нормировки в SciPy; правдоподобие такой "плотности" завышено,
    и по AIC она незаслуженно обгоняла бы честные модели.
    """
    grid = np.linspace(data.min(), data.max(), 4001)
    density = dist.pdf(grid, *estimates)
    finite = np.isfinite(density)
    by_density = float(np.trapezoid(density[finite], grid[finite])) if finite.sum() > 1 else 0.0
    by_cdf = float(dist.cdf(data.max(), *estimates) - dist.cdf(data.min(), *estimates))
    return max(by_density, by_cdf)


def fit_distribution(name, data, fix_loc=False, time_limit=TIME_LIMIT):
    """
    Подбирает параметры одного распределения методом максимального правдоподобия и считает показатели качества.
    Никогда не бросает исключение: неудача возвращается как FitResult с причиной в skipped.
    :param name: имя распределения в scipy.stats
    :param data: массив наблюдений после clean_data
    :param fix_loc: зафиксировать loc = 0 (тогда сдвиг не оценивается)
    """
    dist = getattr(stats, name)
    n = len(data)
    with warnings.catch_warnings(), np.errstate(all='ignore'):
        warnings.simplefilter('ignore')
        try:
            estimate = estimated_fit_seconds(dist, data)
            if estimate > time_limit:
                return FitResult(name, skipped='плотность считается слишком медленно для подгонки на этих данных')

            estimates = dist.fit(data, floc=0.0) if fix_loc else dist.fit(data)
            shape_names = [sh.strip() for sh in dist.shapes.split(',')] if dist.shapes else []
            parameters = dict(zip([*shape_names, 'loc', 'scale'], (float(value) for value in estimates),
                                  strict=True))

            log_likelihood = float(np.sum(dist.logpdf(data, *estimates)))
            if not math.isfinite(log_likelihood):
                return FitResult(name, skipped='правдоподобие не определено: часть данных лежит вне носителя '
                                                'распределения или параметры выродились')
            mass = probability_mass_over_data(dist, estimates, data)
            if mass > 1.01:
                return FitResult(name, skipped=f'плотность при подобранных параметрах не нормирована: на диапазоне '
                                                f'данных она интегрируется в {mass:.2f} вместо значения не больше 1 '
                                                f'(круговое распределение или численная ошибка SciPy)')
            n_free = len(estimates) - (1 if fix_loc else 0)
            ks = stats.kstest(data, dist.cdf, args=estimates)
            density, edges = histogram(data)
            centers = (edges[:-1] + edges[1:]) / 2
            sse = float(np.sum((dist.pdf(centers, *estimates) - density) ** 2))
            if not (math.isfinite(sse) and math.isfinite(ks.statistic)):
                return FitResult(name, skipped='показатели качества подгонки не вычисляются')
        except Exception as e:
            return FitResult(name, skipped=f'подгонка не удалась: {type(e).__name__}: {e}'[:200])

    return FitResult(name=name, parameters=parameters, n_free=n_free, log_likelihood=log_likelihood,
                     aic=2 * n_free - 2 * log_likelihood,
                     bic=n_free * math.log(n) - 2 * log_likelihood,
                     ks_statistic=float(ks.statistic), ks_pvalue=float(ks.pvalue), sse=sse)


def ranked(results):
    """
    :return: подобранные распределения, от лучшего к худшему по AIC
    """
    return sorted((result for result in results if result.ok), key=lambda result: result.aic)


def results_table(results):
    """
    Сводная таблица подобранных распределений, отсортированная по AIC.
    ΔAIC - отставание от лучшего: до 2 модели практически неразличимы, больше 10 - явно хуже.
    """
    best = ranked(results)
    rows = [{
        'Распределение': result.name,
        'AIC': result.aic,
        'ΔAIC': result.aic - best[0].aic,
        'BIC': result.bic,
        'KS p-значение': result.ks_pvalue,
        'KS статистика': result.ks_statistic,
        'ln L': result.log_likelihood,
        'SSE': result.sse,
        'Оценено параметров': result.n_free,
        # самая длинная колонка - последней, чтобы показатели были видны без прокрутки
        'Параметры': ', '.join(f'{param} = {value:.4g}' for param, value in result.parameters.items()),
    } for result in best]
    return pd.DataFrame(rows)


def data_statistics(data):
    """
    Описательная статистика данных.
    """
    series = pd.Series(data)
    return pd.DataFrame({'Значение': [len(series), series.mean(), series.std(), series.skew(), series.kurtosis(),
                                      series.min(), series.quantile(0.25), series.median(), series.quantile(0.75),
                                      series.max()]},
                        index=['Наблюдений', 'Среднее', 'Стандартное отклонение', 'Асимметрия',
                               'Эксцесс (избыточный)', 'Минимум', 'Q1 (25%)', 'Медиана (50%)', 'Q3 (75%)',
                               'Максимум'])
