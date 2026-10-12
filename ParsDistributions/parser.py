# -*- coding: utf-8 -*-
"""
Created on 29/12/2023
Aauthor: D-one
"""
import re
from dataclasses import dataclass

import requests
import scipy.stats._distr_params  # noqa: F401 - значения параметров по умолчанию
from bs4 import BeautifulSoup
from scipy import stats

DOCS_URL = 'https://scipy.github.io/devdocs/tutorial/stats/'


@dataclass(frozen=True)
class DistributionInfo:
    """
    Все, что приложение знает об одном распределении.
    :param name: имя в scipy.stats, например 'alpha'
    :param fullname: заголовок из документации, например 'Alpha Distribution'
    :param url: страница распределения в документации SciPy
    :param docstring: строка документации из scipy.stats
    :param equation: формула в LaTeX из строки документации ('' если формулы нет)
    :param parameters: значения по умолчанию, например {'a': 3.57, 'loc': 0.0, 'scale': 1.0}
    """
    name: str
    fullname: str
    url: str
    docstring: str
    equation: str
    parameters: dict


@dataclass(frozen=True)
class _Kind:
    """Отличия непрерывных распределений от дискретных."""
    page: str
    section_id: str
    href_prefix: str
    default_shapes: list
    # параметры, общие для всех распределений этого вида (у дискретных нет scale)
    common_parameters: dict


_KINDS = {
    'continuous': _Kind(page='continuous.html',
                        section_id='continuous-distributions-in-scipy-stats',
                        href_prefix='continuous_',
                        default_shapes=stats._distr_params.distcont,
                        common_parameters={'loc': 0.00, 'scale': 1.00}),
    'discrete': _Kind(page='discrete.html',
                      section_id='discrete-distributions-in-scipy-stats',
                      href_prefix='discrete_',
                      default_shapes=stats._distr_params.distdiscrete,
                      common_parameters={'loc': 0.00}),
}


class DistributionParser:
    """
    Класс DistributionParser собирает информацию о статистических распределениях: список распределений, их названия
    и ссылки берутся со страницы документации SciPy, а строки документации, формулы и параметры по умолчанию -
    из установленного модуля scipy.stats.
    Результат лежит в self.distributions: словарь {имя в scipy.stats: DistributionInfo} в порядке страницы.
    Распределения, которых нет в установленной версии SciPy, пропускаются.
    """

    def __init__(self, type_rv='continuous'):
        """
        :param type_rv: continuous or discrete
        """
        self.kind = _KINDS['discrete' if type_rv == 'discrete' else 'continuous']
        self.url = DOCS_URL + self.kind.page
        self.distributions = self._parse(self._get_soup())

    def _get_soup(self):
        try:
            response = requests.get(self.url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get URL {self.url}: {e}") from e
        return BeautifulSoup(response.text, "html.parser")

    def _parse(self, soup):
        section = soup.find(id=self.kind.section_id)
        if section is None:
            raise ValueError(f"Section '{self.kind.section_id}' not found on {self.url}")

        default_shapes = {}
        for name, shapes in self.kind.default_shapes:
            if isinstance(name, str):
                default_shapes.setdefault(name, shapes)

        distributions = {}
        for li in section.find_all("li", {"class": "toctree-l1"}):
            link = li.find(class_='reference internal', href=True)
            if not link or link['href'].startswith('#'):
                continue
            href = link['href']
            name = href.replace(self.kind.href_prefix, '').replace('.html', '')
            # Страница devdocs может описывать распределения, которых нет в установленной версии SciPy
            if not hasattr(stats, name):
                continue
            docstring = getattr(stats, name).__doc__ or ''
            distributions[name] = DistributionInfo(name=name,
                                                   fullname=li.text.strip(),
                                                   url=DOCS_URL + href,
                                                   docstring=docstring,
                                                   equation=self._extract_equation(docstring),
                                                   parameters=self._default_parameters(name, default_shapes))
        return distributions

    @staticmethod
    def _math_blocks(docstring):
        """
        :return: содержимое всех блоков ".. math::" строки документации, каждый блок одной строкой
        """
        lines = docstring.split('\n')
        blocks = []
        i = 0
        while i < len(lines):
            directive = re.match(r'^(\s*)\.\. math::\s*(.*)$', lines[i])
            i += 1
            if not directive:
                continue
            indent = len(directive.group(1))
            body = [directive.group(2)] if directive.group(2) else []
            # блок - это все строки с отступом больше, чем у директивы
            while i < len(lines) and (not lines[i].strip() or len(lines[i]) - len(lines[i].lstrip()) > indent):
                if lines[i].strip():
                    body.append(lines[i].strip())
                i += 1
            blocks.append(' '.join(body))
        return blocks

    @classmethod
    def _extract_equation(cls, docstring):
        """
        Формула плотности: блок math::, который начинается с "f(". Если таких блоков несколько (частный случай
        и общий), берется тот, у которого больше аргументов. Определения статистик (D_n = ...) плотностью
        не являются и пропускаются.
        :return: например f(x, a) = \\frac{1}{x^2 \\Phi(a) \\sqrt{2\\pi}} или '', если формулы плотности нет
        """
        densities = [block for block in cls._math_blocks(docstring) if re.match(r'f\s*\(', block)]
        if not densities:
            return ''
        equation = max(densities, key=lambda block: block[:block.index(')')].count(','))
        # многострочная формула с выравниванием (&, \\\\) рендерится только внутри окружения
        if ('&' in equation or '\\\\' in equation) and not equation.startswith('\\begin'):
            equation = '\\begin{aligned}' + equation.rstrip('\\ ') + '\\end{aligned}'
        return equation

    def _default_parameters(self, name, default_shapes):
        """
        :return: {'a': 3.57, 'loc': 0.0, 'scale': 1.0} - параметры формы, затем общие параметры
        """
        dist = getattr(stats, name)
        shape_names = [sh.strip() for sh in dist.shapes.split(',')] if dist.shapes else []
        parameters = dict(zip(shape_names, default_shapes.get(name, ()), strict=False))
        parameters.update(self.kind.common_parameters)
        return {param: round(float(value), 2) for param, value in parameters.items()
                if isinstance(value, (int, float))}
