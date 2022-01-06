import json
from bs4 import BeautifulSoup
import requests
import string
from scipy import stats
from six.moves import urllib

def dis_button_names():
    names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            names.append(str(name[0]))
    return names

def dis_url_names():
    url_names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            url = 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.' + str(name[0]) + '.html#scipy.stats.' + str(name[0])
            url_names.append(url)
    return url_names

def dis_functions():
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
    all_params = []
    names = []
    for name, params in sorted(stats._distr_params.distcont):
        names.append(name)
        loc, scale = 0.00, 1.00
        params = list(params) + [loc, scale]
        all_params.append(params)
    return all_params

def dis_parameters_name():

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

def doc_name():
    doc_names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            url = 'stats.' + str(name[0]) + ('.__doc__')
            doc_names.append(url)
    return doc_names

def doc_dictionaries():
    doc = doc_name()
    distribution_names = dis_button_names()
    doc_dictionaries = {distribution: doc[i] for i, distribution in enumerate(distribution_names)}
    return doc_dictionaries

def functions_dictionaries():
    functions = dis_functions()
    distribution_names = dis_button_names()
    func_dictionaries = {distribution: functions[i] for i, distribution in enumerate(distribution_names)}
    return func_dictionaries

def parameters_dictionaries():
    names = dis_button_names()
    all_params_names = dis_parameters_name()
    all_params = dis_parameters()
    all_dist_params_dict = {function: {param: f"{all_params[i][j]:.2f}" for j, param in enumerate(all_params_names[i])}
                            for i, function in enumerate(names)}
    return all_dist_params_dict
