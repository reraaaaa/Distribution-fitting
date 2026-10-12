"""
Created on 21/12/2021
Author: D-one
"""

from pathlib import Path

import scipy
import streamlit as st

from app_pages import navigation, p_discrete, p_explore, p_fitting, p_introduction

IMAGES = Path(__file__).resolve().parent / "images"
REPOSITORY = "https://github.com/reraaaaa/Distribution-fitting"

st.set_page_config(page_title='Distribution Fitting', page_icon=':material/monitoring:')

# логотип под тему: темные штрихи на светлой теме и светлые на темной
theme = getattr(st.context.theme, "type", None) or "dark"
st.logo(str(IMAGES / f"logo_{theme}.png"), size='large')

pages = {
    "introduction": st.Page(p_introduction, title="Главная", icon=":material/home:",
                            url_path="introduction", default=True),
    "explore": st.Page(p_explore, title="Непрерывные", icon=":material/monitoring:", url_path="explore"),
    "discrete": st.Page(p_discrete, title="Дискретные", icon=":material/bar_chart:", url_path="discrete"),
    "fitting": st.Page(p_fitting, title="Подбор закона распределения", icon=":material/query_stats:",
                       url_path="fitting"),
}
navigation.register(**pages)
page = st.navigation({
    "": [pages["introduction"]],
    "Распределения": [pages["explore"], pages["discrete"]],
    "Данные": [pages["fitting"]],
})
page.run()

st.sidebar.caption(f"SciPy {scipy.__version__} · [Исходный код на GitHub]({REPOSITORY})")
