from bs4 import BeautifulSoup
import requests
from scipy import stats
import pandas as pd


class DistributionParser(object):
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
    BASE_URL = 'https://scipy.github.io/devdocs/tutorial/stats/continuous.html'
    #BASE_URL = 'https://scipy.github.io/devdocs/tutorial/stats/discrete.html'
    DISTRIBUTION_ID = "continuous-distributions-in-scipy-stats"
    #DISTRIBUTION_ID = "discrete-distributions-in-scipy-stats"

    def __init__(self):
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
            response = requests.get(self.BASE_URL)
            response.raise_for_status()
        except requests.RequestException as e:
            print(f"Failed to get URL {self.BASE_URL}: {e}")
            return None
        return BeautifulSoup(response.text, "html.parser")

    def _fetch_distributions_and_hrefs(self):
        """
        :return: {'Alpha Distribution': 'continuous_alpha.html', 'Anglit Distribution': 'continuous_anglit.html',...}
        """
        div = self.soup.find(id=self.DISTRIBUTION_ID)
        lis = div.find_all("li", {"class": "toctree-l1"})
        distributions_and_hrefs = {}

        for li in lis:
            link = li.find(class_='reference internal', href=True)
            if link and not link['href'].startswith('#'):
                distributions_and_hrefs[li.text] = link['href']
        distributions_and_hrefs.pop('Jones and Faddy Skew-T Distribution')
        return distributions_and_hrefs

    def _fetch_distributions(self):
        """
        :return: ['Alpha Distribution', 'Anglit Distribution',...
        """
        distributions_and_hrefs = self._fetch_distributions_and_hrefs()
        distributions = list(distributions_and_hrefs.keys())
        return distributions

    def _extract_distribution_names(self):
        """
        :return: ['alpha', 'anglit', 'arcsine',...
        """
        hrefs = list(self._fetch_distributions_and_hrefs().values())
        names = [name.replace('continuous_', '').replace('.html', '') for name in hrefs]
        return names

    def _generate_distribution_urls(self):
        """
        :return: ['https://scipy.github.io/devdocs/tutorial/stats/continuous_alpha.html',...
        """
        hrefs = list(self._fetch_distributions_and_hrefs().values())
        urls = sorted(set(f'https://scipy.github.io/devdocs/tutorial/stats/{href}' for href in hrefs))
        return urls

    def _fetch_distribution_docstrings(self):
        """
        :return: info docs text...
        """
        names = self._extract_distribution_names()
        docstrings = [getattr(stats, name).__doc__ for name in names]
        return docstrings

    def _fetch_dictionaries_stat(self):
        """
        :return: ['stats.alpha', 'stats.anglit', 'stats.arcsine',...
        """
        names = self._extract_distribution_names()
        stat = {name: 'stats.' + name for name in names}
        return stat

    def _fetch_distribution_functions(self):
        """
        :return: [f(x, a) = \\frac{1}{x^2 \\Phi(a) \\sqrt{2\\pi}},...
        """
        docstrings = self._fetch_distribution_docstrings()
        equations = [''.join(docstring.split('\n')[i + 2:i + 4]) for docstring in docstrings for i, line in
                     enumerate(docstring.split('\n')) if 'math::' in line]
        return equations

    def _fetch_distribution_parameters(self):
        """
        :return: [['a', 'loc', 'scale'],...
        :return: [[3.570477051665046, 0.0, 1.0], [0.0, 1.0],...
        """
        names = self._extract_distribution_names()
        parse_params = sorted(stats._distr_params.distcont)
        df = pd.DataFrame(parse_params, columns=['dist', 'param'])
        df2 = pd.DataFrame(names, columns=['dist'])
        inner_join = pd.merge(df2, df, on='dist', how='left')
        inner_join = inner_join.drop_duplicates(subset=['dist'])
        inner_join = inner_join.values.tolist()

        all_params_names = []
        all_params = []
        for i, params in inner_join:
            dist = getattr(stats, i)
            p_names = ['loc', 'scale']
            if dist.shapes:
                p_names = [sh.strip() for sh in dist.shapes.split(',')] + ['loc', 'scale']
            all_params_names.append(p_names)
            loc, scale = 0.00, 1.00
            params = list(params) + [loc, scale]
            all_params.append(params)
        return all_params_names, all_params

    def _generate_distribution_dictionaries(self):
        """
        :return: all dictionaries
        """
        all_params_names, all_params = self._fetch_distribution_parameters()
        return {
            'doc_dic': {distribution: doc for distribution, doc in zip(self.names, self.docstrings)},
            'functions_dic': {distribution: function for distribution, function in zip(self.names, self.equations)},
            'fullname_dic': {distribution: fullname for distribution, fullname in zip(self.names, self.distributions)},
            'parameters_dic': {function: {param: f"{all_params[i][j]:.2f}"
                                          for j, param in enumerate(all_params_names[i])}
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
