"""Ссылки между страницами. Страницы регистрирует точка входа, потому что st.Page создается там."""
import streamlit as st

PAGES = {}


def register(**pages):
    PAGES.update(pages)


def page_link(key, label, icon=None):
    """
    Ссылка на страницу приложения. Если навигация не запущена (страница вызвана отдельно, как в тестах),
    ссылка не показывается.
    """
    page = PAGES.get(key)
    if page is not None:
        st.page_link(page, label=label, icon=icon)
