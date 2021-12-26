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
    url_names = []
    for i, name in enumerate(sorted(stats._distr_params.distcont)):
        if i == 87:
            pass
        else:
            url = 'https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.' + str(name[0]) + '.html#scipy.stats.' + str(name[0])
            url_names.append(url)
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

x = dis_button_names()
y = dis_url_names()
z = dis_functions()