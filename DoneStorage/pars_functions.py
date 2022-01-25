import json
from bs4 import BeautifulSoup
import requests
import string
from scipy import stats
import re
from six.moves import urllib


def dis_fullname():
    # ['Alpha Distribution', 'Anglit Distribution', ...]
    dis_fullname = []
    url_names = 'https://docs.scipy.org/doc/scipy/tutorial/stats/continuous.html'
    get_url = requests.get(url_names)
    get_text = get_url.text
    soup = BeautifulSoup(get_text, "html.parser")
    x = soup.find("div", dict(id="continuous-distributions-in-scipy-stats"))
    categories = x.find_all('li', {'class': 'toctree-l1'})
    for x in categories:
        dis_fullname.append(x.text)
    return dis_fullname


def dis_hrefname():
    # ['continuous_alpha.html', 'continuous_anglit.html',...]
    dis_hrefname = []
    url_names = 'https://docs.scipy.org/doc/scipy/tutorial/stats/continuous.html'
    get_url = requests.get(url_names)
    get_text = get_url.text
    soup = BeautifulSoup(get_text, "html.parser")
    x = soup.find("div", dict(id="continuous-distributions-in-scipy-stats"))
    categories = x.find_all(class_='reference internal', href=True)
    for i in categories:
        dis_hrefname.append(i['href'])
    dis_hrefname.pop(0)
    return dis_hrefname


def dis_name(dis_hrefname):
    dis_name = []
    for i in dis_hrefname:
        f = i.replace('.html', '').replace('continuous_', '')
        dis_name.append(f)
    return dis_name


def dis_button_names():
    # ['alpha', 'anglit', 'arcsine', ...]
    names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            names.append(str(name[0]))
    return names


def dis_url_names():
    # ['https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.alpha.html#scipy.stats.alpha'...]
    url_names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            url = 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.' + str(
                name[0]) + '.html#scipy.stats.' + str(name[0])
            url_names.append(url)
    return url_names


def dis_functions():
    # '\n\\[f(x, a) = \\frac{1}{x^2 \\Phi(a) \\sqrt{2\\pi}} *\n
    # \\exp(-\\frac{1}{2} (a-1/x)^2)\\]', '\n\\[f(x) = \\sin(2x + \\pi/2) = \\cos(2x)\\]'
    functions = []
    url_names = dis_url_names()
    for idx, i in enumerate(url_names):
        if idx == 87:
            print(' \[f(x, a, b) = \frac{1}{ \left(x*log( \frac{b}{a} \right) }')
        else:
            html_doc = urllib.request.urlopen(i).read()
            soup = BeautifulSoup(html_doc, 'html.parser')
            divTag = soup.find_all("div", class_="math notranslate nohighlight")
            for tag in divTag:
                functions.append(tag.text)
    return functions


def dis_parameters():
    # [[3.570477051665046, 0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [1.0, 0.0, 1.0],...]
    all_params = []
    names = []
    for name, params in sorted(stats._distr_params.distcont):
        names.append(name)
        loc, scale = 0.00, 1.00
        params = list(params) + [loc, scale]
        all_params.append(params)
    return all_params


def dis_parameters_name():
    # [['a', 'loc', 'scale'], ['loc', 'scale'],...]
    all_params_names = []

    for name, params in sorted(stats._distr_params.distcont):
        dist = getattr(stats, name)
        p_names = ['loc', 'scale']
        if dist.shapes:
            p_names = [sh.strip() for sh in dist.shapes.split(',')] + ['loc', 'scale']
            all_params_names.append(p_names)
        else:
            all_params_names.append(['loc', 'scale'])
    return all_params_names


def stats_name():
    # ['stats.alpha', 'stats.anglit', 'stats.arcsine',...]
    stats_names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            url = 'stats.' + str(name[0])
            stats_names.append(url)
    return stats_names


def doc_name():
    # ['stats.alpha.__doc__', 'stats.anglit.__doc__',...]
    doc_names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            url = 'stats.' + str(name[0]) + ('.__doc__')
            doc_names.append(url)
    return doc_names


def stats_dictionaries():
    # {'alpha': 'stats.alpha', 'anglit': 'stats.anglit',...}
    stats = stats_name()
    distribution_names = dis_button_names()
    stats_dictionaries = {distribution: stats[i] for i, distribution in enumerate(distribution_names)}
    return stats_dictionaries


def doc_dictionaries():
    # {'alpha': 'stats.alpha.__doc__', 'anglit': 'stats.anglit.__doc__',...}
    doc = doc_name()
    distribution_names = dis_button_names()
    doc_dictionaries = {distribution: doc[i] for i, distribution in enumerate(distribution_names)}
    return doc_dictionaries


def functions_dictionaries():
    # {'alpha': '\n\\[f(x, a) = \\frac{1}{x^2 \\Phi(a) \\sqrt{2\\pi}} *\n
    # \\exp(-\\frac{1}{2} (a-1/x)^2)\\]',...}
    functions = dis_functions()
    distribution_names = dis_button_names()
    func_dictionaries = {distribution: functions[i] for i, distribution in enumerate(distribution_names)}
    return func_dictionaries


def parameters_dictionaries():
    # {'alpha': {'a': '3.57', 'loc': '0.00', 'scale': '1.00'},...}
    names = dis_button_names()
    all_params_names = dis_parameters_name()
    all_params = dis_parameters()
    all_dist_params_dict = {function: {param: f"{all_params[i][j]:.2f}" for j, param in enumerate(all_params_names[i])}
                            for i, function in enumerate(names)}
    return all_dist_params_dict


"""""
def url_dictionaries():

    url_dictionaries = {distribution: [dis_url_names()[i], scipy_distribution_proper_names()[i]] for i, distribution in enumerate(distr_selectbox_names())}

    return url_dictionaries
"""""
dis_hrefname = dis_hrefname()
b = dis_fullname()
c = dis_button_names()
r = dis_name(dis_hrefname)
