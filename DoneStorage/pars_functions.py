from bs4 import BeautifulSoup
import requests
from scipy import stats
import pandas as pd
from six.moves import urllib
import csv


def c_dis_fullname():
    # ['Alpha Distribution', 'Anglit Distribution', ...]
    # 15 - erland distribution нет функции
    c_fullname = []
    url = 'https://scipy.github.io/devdocs/tutorial/stats/continuous.html'
    get_url = requests.get(url)
    get_text = get_url.text
    soup = BeautifulSoup(get_text, "html.parser")
    div = soup.find(id="continuous-distributions-in-scipy-stats")
    li = div.find_all("li", {"class": "toctree-l1"})
    for i in li:
        c_fullname.append(i.text)
    c_fullname.pop(15)
    final_c_fullname = set(c_fullname)
    return sorted(final_c_fullname)


def c_dis_hrefname():
    # ['continuous_alpha.html', 'continuous_anglit.html',...]
    c_hrefname = []
    url = 'https://scipy.github.io/devdocs/tutorial/stats/continuous.html'
    get_url = requests.get(url)
    get_text = get_url.text
    soup = BeautifulSoup(get_text, "html.parser")
    div = soup.find(id="continuous-distributions-in-scipy-stats")
    href = div.find_all(class_='reference internal', href=True)
    for i in href:
        c_hrefname.append(i['href'])
    c_hrefname.pop(0)
    c_hrefname.pop(15)
    final_c_hrefname = set(c_hrefname)
    return sorted(final_c_hrefname)


def c_dis_url():

    c_hrefname = c_dis_hrefname()
    c_url = []
    for i in c_hrefname:
        url = 'https://scipy.github.io/devdocs/tutorial/stats/'+str(i)
        c_url.append(url)
    final_c_url = set(c_url)
    return sorted(final_c_url)


def c_dis_name():
    # ['alpha', 'anglit', 'arcsine', ...]

    c_name = []
    c_hrefname = c_dis_hrefname()
    for i in c_hrefname:
        j = i.replace('continuous_', '').replace('.html', '')
        c_name.append(j)
    return c_name

def c_dis_stats_name():
    # ['stats.alpha', 'stats.anglit', 'stats.arcsine',...]

    name = c_dis_name()
    stat = []
    for i in name:
        url = 'stats.' + str(i)
        stat.append(url)
    stat_dic = {distribution: stat[i] for i, distribution in enumerate(name)}
    return stat_dic

def c_dis_stdoc_name():
    # ['stats.alpha.__doc__', 'stats.anglit.__doc__',...]

    c_name = c_dis_name()
    c_stdoc_name = []

    for i in c_name:
        j = (getattr(stats, i).__doc__)
        c_stdoc_name.append(j)
    return c_stdoc_name


def c_dis_functions():
    # '\n\\[f(x, a) = \\frac{1}{x^2 \\Phi(a) \\sqrt{2\\pi}} *\n
    # \\exp(-\\frac{1}{2} (a-1/x)^2)\\]', '\n\\[f(x) = \\sin(2x + \\pi/2) = \\cos(2x)\\]'

    name = c_dis_name()
    l = []

    for n in name:
        l1 = (getattr(stats, n).__doc__)
        l.append(l1)

    eq = []
    reg = []
    for j in range(len(sorted(l))):
        for i, line in enumerate(l[j].split('\n')):
            if 'math::' in line:
                eq.append(l[j].split('\n')[i+2:i+4])
                reg.append(l[j].split('\n')[i+2:i+6])

    class OurList(list):
        def join(self, s):
            return s.join(self)

    joined_eq = []
    for i in eq:
        li = OurList(i)
        li = li.join('')
        joined_eq.append(li)

    return joined_eq


def c_dis_parameters():
    # [[3.570477051665046, 0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [1.0, 0.0, 1.0],...]

    name = c_dis_name()

    parse_params = sorted(stats._distr_params.distcont)
    df = pd.DataFrame(parse_params, columns=['dist', 'param'])
    df2 = pd.DataFrame(name, columns=['dist'])
    inner_join = pd.merge(df2,
                          df,
                          on='dist',
                          how='left')
    inner_join = inner_join.drop_duplicates(subset=['dist'])
    inner_join = inner_join.values.tolist()

    all_params = []
    names = []
    for i, params in inner_join:
        names.append(i)
        loc, scale = 0.00, 1.00
        params = list(params) + [loc, scale]
        all_params.append(params)
    return all_params


def c_dis_parameters_name():
    # [['a', 'loc', 'scale'], ['loc', 'scale'],...]

    name = c_dis_name()

    parse_params = sorted(stats._distr_params.distcont)
    df = pd.DataFrame(parse_params, columns=['dist', 'param'])
    df2 = pd.DataFrame(name, columns=['dist'])
    inner_join = pd.merge(df2,
                          df,
                          on='dist',
                          how='left')
    inner_join = inner_join.drop_duplicates(subset=['dist'])
    inner_join = inner_join.values.tolist()

    all_params_names = []

    for i, params in inner_join:
        dist = getattr(stats, i)
        p_names = ['loc', 'scale']
        if dist.shapes:
            p_names = [sh.strip() for sh in dist.shapes.split(',')] + ['loc', 'scale']
            all_params_names.append(p_names)
        else:
            all_params_names.append(['loc', 'scale'])
    return all_params_names


def c_dis_dictionaries():

    doc = c_dis_stdoc_name()
    name = c_dis_name()
    functions = c_dis_functions()
    fullname = c_dis_fullname()
    parameters_name = c_dis_parameters_name()
    parameters = c_dis_parameters()
    url_names = c_dis_url()

    doc_dic = {distribution: doc[i] for i, distribution in enumerate(name)}
    functions_dic = {distribution: functions[i] for i, distribution in enumerate(name)}
    fullname_dic = {distribution: fullname[i] for i, distribution in enumerate(name)}
    parameters_dic = {function: {param: f"{parameters[i][j]:.2f}" for j, param in enumerate(parameters_name[i])} for i, function in enumerate(name)}
    url_dic = {distribution: [url_names[i], fullname[i]] for i, distribution in enumerate(name)}

    return doc_dic, functions_dic, fullname_dic, parameters_dic, url_dic
