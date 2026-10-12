# -*- coding: utf-8 -*-
"""
Created on 29/12/2023
Aauthor: D-one
"""
from bs4 import BeautifulSoup
import requests
from scipy import stats
import scipy.stats._distr_params  # noqa: F401 - значения параметров по умолчанию


class DistributionParser:
    """
    Класс DistributionParser предназначен для анализа и извлечения информации о статистических распределениях
    из документации SciPy. BASE_URL и DISTRIBUTION_ID — это атрибуты класса, в которых хранится URL-адрес анализируемой
    веб-страницы и идентификатор HTML раздела, содержащего дистрибутивы, соответственно.
    Метод __init__ инициализирует экземпляр класса. Он извлекает HTML-содержимое веб-страницы с помощью метода _get_soup
    и сохраняет его в self.soup. Затем он вызывает различные методы для извлечения различных фрагментов информации о
    распределениях и сохраняет их в переменных экземпляра.
     _fetch_distributions извлекает названия дистрибутивов с веб-страницы.
     _fetch_distribution_hrefs извлекает hrefs (ссылки) дистрибутивов с веб-страницы.
     _generate_distribution_urls генерирует полные URL-адреса для дистрибутивов, используя hrefs.
     _fetch_distribution_docstrings извлекает строки документации дистрибутивов из модуля scipy.stats.
     _extract_distribution_names извлекает имена дистрибутивов из hrefs.
     _fetch_distribution_functions извлекает математические функции распределений из строк документации.
     _fetch_distribution_parameters_names и _fetch_distribution_parameters извлекают имена и значения параметров
     распределений соответственно.
     _generate_distribution_dictionaries генерирует словари, которые сопоставляют имена дистрибутивов с различными
    фрагментами информации о дистрибутивах.
     Методы get_ возвращают соответствующие переменные экземпляра.
    Этот класс можно использовать для программного доступа к подробной информации о непрерывных распределениях в
    модуле scipy.stats.
    """

    def __init__(self, type_rv):
        """
        :param type_rv: continuous or discrete
        """
        if type_rv == 'discrete':
            self.BASE_URL = 'https://scipy.github.io/devdocs/tutorial/stats/discrete.html'
            self.DISTRIBUTION_ID = "discrete-distributions-in-scipy-stats"
        else:
            self.BASE_URL = 'https://scipy.github.io/devdocs/tutorial/stats/continuous.html'
            self.DISTRIBUTION_ID = "continuous-distributions-in-scipy-stats"
        self.soup = self._get_soup()
        self.distributions_and_hrefs = self._fetch_distributions_and_hrefs()
        self.distributions = self._fetch_distributions()
        self.names = self._extract_distribution_names()
        self.urls = self._generate_distribution_urls()
        self.docstrings = self._fetch_distribution_docstrings()
        self.equations = self._fetch_distribution_functions()
        self.parameters = self._fetch_distribution_parameters()
        self.dictionaries = self._generate_distribution_dictionaries()
        self.stat = self._fetch_dictionaries_stat()

    def _get_soup(self):
        try:
            response = requests.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to get URL {self.BASE_URL}: {e}") from e
        return BeautifulSoup(response.text, "html.parser")

    def _is_continuous(self):
        return self.DISTRIBUTION_ID == "continuous-distributions-in-scipy-stats"

    def _name_from_href(self, href):
        """
        :return: 'continuous_alpha.html' -> 'alpha'
        """
        prefix = 'continuous_' if self._is_continuous() else 'discrete_'
        return href.replace(prefix, '').replace('.html', '')

    def _fetch_distributions_and_hrefs(self):
        """
        :return: {'Alpha Distribution': 'continuous_alpha.html', 'Anglit Distribution': 'continuous_anglit.html',...}
        """
        div = self.soup.find(id=self.DISTRIBUTION_ID)
        if div is None:
            raise ValueError(f"Section '{self.DISTRIBUTION_ID}' not found on {self.BASE_URL}")
        lis = div.find_all("li", {"class": "toctree-l1"})
        distributions_and_hrefs = {}

        for li in lis:
            link = li.find(class_='reference internal', href=True)
            if link and not link['href'].startswith('#'):
                # Страница devdocs может описывать распределения, которых нет в установленной версии SciPy
                if hasattr(stats, self._name_from_href(link['href'])):
                    distributions_and_hrefs[li.text.strip()] = link['href']
        return distributions_and_hrefs

    def _fetch_distributions(self):
        """
        :return: ['Alpha Distribution', 'Anglit Distribution',...
        """
        return list(self.distributions_and_hrefs.keys())

    def _extract_distribution_names(self):
        """
        :return: ['alpha', 'anglit', 'arcsine',...
        """
        return [self._name_from_href(href) for href in self.distributions_and_hrefs.values()]

    def _generate_distribution_urls(self):
        """
        :return: ['https://scipy.github.io/devdocs/tutorial/stats/continuous_alpha.html',...
        """
        return [f'https://scipy.github.io/devdocs/tutorial/stats/{href}'
                for href in self.distributions_and_hrefs.values()]

    def _fetch_distribution_docstrings(self):
        """
        :return: info docs text...
        """
        return [getattr(stats, name).__doc__ or '' for name in self.names]

    def _fetch_dictionaries_stat(self):
        """
        :return: ['stats.alpha', 'stats.anglit', 'stats.arcsine',...
        """
        return {name: 'stats.' + name for name in self.names}

    def _fetch_distribution_functions(self):
        """
        Одно уравнение на распределение: первый блок math:: из строки документации ('' если блока нет).
        :return: [f(x, a) = \\frac{1}{x^2 \\Phi(a) \\sqrt{2\\pi}},...
        """
        equations = []
        for docstring in self.docstrings:
            lines = docstring.split('\n')
            equation = ''
            for i, line in enumerate(lines):
                if 'math::' in line:
                    equation = ''.join(lines[i + 2:i + 4])
                    break
            equations.append(equation)
        return equations

    def _fetch_distribution_parameters(self):
        """
        :return: [['a', 'loc', 'scale'],...
        :return: [[3.570477051665046, 0.0, 1.0], [0.0, 1.0],...
        """
        if self._is_continuous():
            parse_params = stats._distr_params.distcont
            # loc, scale
            tail_names, tail_values = ['loc', 'scale'], [0.00, 1.00]
        else:
            parse_params = stats._distr_params.distdiscrete
            # у дискретных распределений нет scale
            tail_names, tail_values = ['loc'], [0.00]

        default_shapes = {}
        for dist_name, params in parse_params:
            if isinstance(dist_name, str):
                default_shapes.setdefault(dist_name, params)

        all_params_names = []
        all_params = []
        for name in self.names:
            dist = getattr(stats, name)
            p_names = [sh.strip() for sh in dist.shapes.split(',')] if dist.shapes else []
            all_params_names.append(p_names + tail_names)
            all_params.append(list(default_shapes.get(name, ())) + tail_values)
        return all_params_names, all_params

    def _generate_distribution_dictionaries(self):
        """
        :return: all dictionaries
        """
        all_params_names, all_params = self.parameters
        return {
            'doc_dic': {distribution: doc for distribution, doc in zip(self.names, self.docstrings)},
            'functions_dic': {distribution: function for distribution, function in zip(self.names, self.equations)},
            'fullname_dic': {distribution: fullname for distribution, fullname in zip(self.names, self.distributions)},
            'parameters_dic': {
                function: {param: f"{value:.2f}" for param, value in zip(all_params_names[i], all_params[i]) if
                           isinstance(value, (int, float))}
                for i, function in enumerate(self.names)},
            'url_dic': {distribution: [url, fullname] for distribution, url, fullname in
                        zip(self.names, self.urls, self.distributions)}
        }

    def get_distributions_and_hrefs(self):
        return self.distributions_and_hrefs

    def get_distributions(self):
        return self.distributions

    def get_distribution_names(self):
        return self.names

    def get_distribution_urls(self):
        return self.urls

    def get_distribution_docstrings(self):
        return self.docstrings

    def get_dictionaries_stat(self):
        return self.stat

    def get_distribution_functions(self):
        return self.equations

    def get_distribution_parameters(self):
        return self.parameters

    def get_dictionaries(self):
        return self.dictionaries
