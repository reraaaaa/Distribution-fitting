from bs4 import BeautifulSoup
import requests
from scipy import stats
import pandas as pd


def dis_fullname():
    # ['Alpha Distribution', 'Anglit Distribution', ...]
    # 15 - erland distribution нет функции
    fullname = []
    url = 'https://docs.scipy.org/doc/scipy/tutorial/stats/continuous.html'
    get_url = requests.get(url)
    get_text = get_url.text
    soup = BeautifulSoup(get_text, "html.parser")
    div = soup.find("div", dict(id="continuous-distributions-in-scipy-stats"))
    categories = div.find_all('li', {'class': 'toctree-l1'})
    for i in categories:
        fullname.append(i.text)
    fullname.pop(15)
    return fullname


def dis_hrefname():
    # ['continuous_alpha.html', 'continuous_anglit.html',...]
    hrefname = []
    url = 'https://docs.scipy.org/doc/scipy/tutorial/stats/continuous.html'
    get_url = requests.get(url)
    get_text = get_url.text
    soup = BeautifulSoup(get_text, "html.parser")
    div = soup.find("div", dict(id="continuous-distributions-in-scipy-stats"))
    href = div.find_all(class_='reference internal', href=True)
    for i in href:
        hrefname.append(i['href'])
    hrefname.pop(0)
    hrefname.pop(15)
    return hrefname


def dis_name():
    # ['alpha', 'anglit', 'arcsine', ...]
    name = []
    hrefname = dis_hrefname()
    for t in hrefname:
        f = t.replace('.html', '').replace('continuous_', '')
        name.append(f)
    return name


def dis_url_names():
    # ['https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.alpha.html#scipy.stats.alpha'...]
    url_names = []
    name = dis_name()
    for i in name:
        urls = 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.' + str(i) + '.html#scipy.stats.' + str(i)
        url_names.append(urls)
    return url_names


def dis_functions():
    # '\n\\[f(x, a) = \\frac{1}{x^2 \\Phi(a) \\sqrt{2\\pi}} *\n
    # \\exp(-\\frac{1}{2} (a-1/x)^2)\\]', '\n\\[f(x) = \\sin(2x + \\pi/2) = \\cos(2x)\\]'
    functions = []
    url_names = dis_url_names()

    for i in url_names:
        get_url = requests.get(i)
        get_text = get_url.text
        soup = BeautifulSoup(get_text, 'html.parser')
        div = soup.find_all("div", class_="math notranslate nohighlight")
        for tag in div:
            functions.append(tag.text)
    return functions


def dis_parameters():
    # [[3.570477051665046, 0.0, 1.0], [0.0, 1.0], [0.0, 1.0], [1.0, 0.0, 1.0],...]

    name = dis_name()
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


def dis_parameters_name():
    # [['a', 'loc', 'scale'], ['loc', 'scale'],...]

    name = dis_name()

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


def stats_name():
    # ['stats.alpha', 'stats.anglit', 'stats.arcsine',...]

    name = dis_name()
    stat = []
    for i in name:
        url = 'stats.' + str(i)
        stat.append(url)
    return stat


def doc_name():
    # ['stats.alpha.__doc__', 'stats.anglit.__doc__',...]

    name = dis_name()
    doc = []
    for i in name:
        url = 'stats.' + str(i) + ('.__doc__')
        doc.append(url)
    return doc

def dis_dictionaries():

    doc = doc_name()
    name = dis_name()
    functions = dis_functions()
    fullname = dis_fullname()
    parameters_name = dis_parameters_name()
    parameters = dis_parameters()
    url_names = dis_url_names()

    doc_dic = {distribution: doc[i] for i, distribution in enumerate(name)}
    functions_dic = {distribution: functions[i] for i, distribution in enumerate(name)}
    fullname_dic = {distribution: fullname[i] for i, distribution in enumerate(name)}
    parameters_dic = {function: {param: f"{parameters[i][j]:.2f}" for j, param in enumerate(parameters_name[i])} for i, function in enumerate(name)}
    url_dic = {distribution: [url_names[i], fullname[i]] for i, distribution in enumerate(name)}

    return doc_dic, functions_dic, fullname_dic, parameters_dic, url_dic
