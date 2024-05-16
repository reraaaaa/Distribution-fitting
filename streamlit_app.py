"""
Created on 21/12/2021
Author: D-one
"""

import numpy as np
import streamlit as st

from DoneStorage.p_explore_2 import p_explore
from DoneStorage.p_fitting import p_fitting
from DoneStorage.p_introduction import p_introduction

LOGO_IMAGE = "https://raw.githubusercontent.com/reraaaaa/Distribution-fitting/master/images/logo_w.png?token=GHSAT0AAAAAABQQROWMSV5LDKAYXT4KAEYAYO7CYJQ"

st.set_page_config(page_title='Distribution-Fitting')

def run_app():
    pages = {
        "Главная": p_introduction,
        "База распределений": p_explore,
        "Подбор закона распределения": p_fitting,
    }
    st.sidebar.title("Основные параметры")

    page = st.sidebar.radio("Выбор:", tuple(pages.keys()))

    pages[page]()

    st.sidebar.header("О нас")
    st.sidebar.warning(
        """ 
    доп инфа
    """
    )


if __name__ == "__main__":
    logo, name = st.sidebar.columns(2)
    with logo:
        st.image(LOGO_IMAGE, use_column_width=True)
    with name:
        st.markdown("<h1 style='text-align: left; color: grey;'> \
                    Distribution Fitting </h1>", unsafe_allow_html=True)

    st.sidebar.write(" ")
    run_app()
