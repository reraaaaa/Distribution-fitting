import json
from bs4 import BeautifulSoup
import requests
import string

def parse_symbol_nyse():
# Загрузка текущего списка тикеров NYSE c сайта eoddata.
# вернет:
#   df с тикерами NYSE.

    alpha = list(string.ascii_uppercase)
    symbols = []
    for each in alpha:
        url = 'http://eoddata.com/stocklist/NYSE/{}.htm'.format(each)
        resp = requests.get(url)
        site = resp.content
        soup = BeautifulSoup(site, 'html.parser')
        table = soup.find('table', {'class': 'quotes'})
        for row in table.findAll('tr')[1:]:
            symbols.append(row.findAll('td')[0].text.rstrip())
    symbols_clean = []
    for each in symbols:
        each = each.replace('.', '-')
        symbols_clean.append((each.split('-')[0]))
    symbols_clean = list(dict.fromkeys(symbols_clean))
    symbol_df = pd.DataFrame({'Symbol':symbols_clean})
    return symbol_df