"""
Created on 21/12/2021
Aauthor: D-one
"""

# Streamlit

import streamlit as st
from DoneStorage.p_explore import p_explore
from DoneStorage.p_fitting import p_fitting
from DoneStorage.p_introduction import p_introduction

import numpy as np

np.random.seed(1)

st.set_page_config(page_title='DistributionFitting')

logo, name = st.sidebar.columns(2)
with logo:
    image = "https://www.google.com/url?sa=i&url=https%3A%2F%2Fwww.scribbr.com%2Fstatistics%2Fstandard-normal" \
            "-distribution%2F&psig=AOvVaw1BIc7bWIQjSDoTjpj3DEqI&ust=1640472586303000&source=images&cd=vfe&ved" \
            "=0CAsQjRxqFwoTCIiq6OLC_fQCFQAAAAAdAAAAABAD "
    st.image(image, use_column_width=True)
with name:
    st.markdown("<h1 style='text-align: left; color: grey;'> \
                Distribution Fitting </h1>", unsafe_allow_html=True)

st.sidebar.write(" ")


def main():
    pages = {
        "Главная": p_introduction,
        "База распределений": p_explore,
        "Подбор закона распределения": p_fitting,
    }
    st.sidebar.title("Main options")
    # Кнопки

    page = st.sidebar.radio("Выбор:", tuple(pages.keys()))

    # Отобразить выбранную страницу

    pages[page]()
    # О нас

    st.sidebar.header("О нас")
    st.sidebar.warning(
        """
    доп инфа
    """
    )


if __name__ == "__main__":
    main()
