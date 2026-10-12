<div align="center">

# Distribution Fitting

**Интерактивный справочник непрерывных распределений вероятностей из `scipy.stats`**

Выберите распределение, двигайте параметры и смотрите, как меняются плотность, функция распределения и выборка.

[![Открыть в Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://distribution-fitting.streamlit.app)

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.65-FF4B4B?logo=streamlit&logoColor=white)
![SciPy](https://img.shields.io/badge/SciPy-1.11-8CAAE6?logo=scipy&logoColor=white)
![License](https://img.shields.io/github/license/reraaaaa/Distribution-fitting?color=0080ff)

<a href="https://distribution-fitting.streamlit.app">
  <img src="images/preview.png" alt="Страница распределения Alpha: формула плотности, график PDF с гистограммой выборки и блочной диаграммой, ползунки параметров в боковой панели" width="900">
</a>

</div>

## Возможности

| | |
| --- | --- |
| **94 распределения** | Все непрерывные распределения из документации SciPy, которые есть в установленной версии |
| **Параметры** | Ползунки для параметров формы, `loc` и `scale` в границах области определения каждого параметра. Недопустимое сочетание даёт предупреждение, а не ошибку |
| **Графики** | PDF, CDF и функция выживания, гистограмма и блочная диаграмма случайной выборки, тёмная и светлая тема |
| **Квартили и σ** | Квартили распределения и области «среднее ± 1/2/3σ» с подписью реальной вероятности попадания: 68/95/99.7% верны только для нормального распределения |
| **Формула** | Плотность в LaTeX из документации SciPy и ссылка на страницу распределения |
| **Статистика** | Таблица: теоретические значения распределения рядом с оценками по выборке |
| **Экспорт** | Готовый скрипт Python, который строит тот же график и ту же выборку |

Подбор распределения по собственным данным запланирован, но ещё не реализован: эта страница пока заглушка.

## Запуск

### В браузере

Нажмите на значок **Open in Streamlit** выше.

### Локально

```sh
git clone https://github.com/reraaaaa/Distribution-fitting
cd Distribution-fitting
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Приложение откроется на <http://localhost:8501>. При старте нужен интернет: список распределений читается из документации SciPy.

Ставьте зависимости именно из `requirements.txt`, а не обновляйте пакеты по одному: закреплённый SciPy 1.11 не работает с NumPy 2.

### Свой экземпляр на Streamlit Community Cloud

1. Сделайте форк репозитория.
2. На [share.streamlit.io](https://share.streamlit.io) создайте приложение: ветка `master`, файл `streamlit_app.py`.

## Разработка

```sh
pip install -r requirements-dev.txt
pytest          # около 10 минут; сеть не нужна, страницы документации SciPy сохранены в tests/fixtures
ruff check .
```

| Путь | Что внутри |
| --- | --- |
| `streamlit_app.py` | Точка входа и навигация по страницам |
| `app_pages/` | Страницы: главная, база распределений, заглушка подбора |
| `ParsDistributions/` | Список распределений из документации SciPy, формулы и параметры по умолчанию из самого SciPy |
| `UtilitySt/` | Выборка и проверка параметров, рисунок matplotlib, генератор скрипта |
| `tests/` | Тесты, включая прогон приложения по каждому распределению |

## Лицензия

MIT, см. [LICENSE](LICENSE).
