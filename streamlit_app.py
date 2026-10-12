"""
Created on 21/12/2021
Author: D-one
"""

from pathlib import Path

import streamlit as st

from app_pages import p_explore, p_fitting, p_introduction

LOGO_IMAGE = Path(__file__).resolve().parent / "images" / "logo_w.png"

st.set_page_config(page_title='Distribution-Fitting')
st.logo(str(LOGO_IMAGE), size='large')

page = st.navigation([
    st.Page(p_introduction, title="Главная", url_path="introduction", default=True),
    st.Page(p_explore, title="База распределений", url_path="explore"),
    st.Page(p_fitting, title="Подбор закона распределения", url_path="fitting"),
])
page.run()

st.sidebar.header("О нас")
st.sidebar.warning("доп инфа")
