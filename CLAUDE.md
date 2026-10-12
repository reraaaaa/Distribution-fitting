# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit app for exploring `scipy.stats` distributions interactively (parameter sliders, PDF/CDF/SF plots, descriptive statistics, export of a standalone Python script). The "fitting" part of the name is not implemented yet — `DoneStorage/p_fitting.py` is a stub.

UI strings, docstrings and comments are in Russian; keep new user-facing text in Russian.

## Commands

```sh
pip install -r requirements.txt
streamlit run streamlit_app.py        # serves on :8501
```

- The app must be started from the repo root: imports are root-relative (`DoneStorage.…`, `ParsDistributions.…`, `UtilitySt.…`) and `DoneStorage/` has no `__init__.py`.
- The app needs network access at runtime (see `DistributionParser` below).
- `venv/` is a local, gitignored Python 3.10 environment; the devcontainer uses Python 3.11.
- There are no tests and no lint config. The README's `pytest` and `python {entrypoint}` lines are unfilled template text; `setup.py` lists `pytest-runner`/`flake8` in `setup_requires` but nothing is configured for them.
- `requirements.txt` and `requirements/requirements.txt` are duplicates. `setup.py` reads the one in `requirements/`, the devcontainer reads the root one — change both together.

## Architecture

`streamlit_app.py` is the entry point: a sidebar radio maps page titles to page functions and calls the selected one. Each page is a single function in `DoneStorage/` that draws its own sidebar controls and main area.

| Page | Function | State |
| --- | --- | --- |
| Главная | `p_introduction.p_introduction` | static text; the `image1..6` constants are empty placeholders and are skipped while empty |
| База распределений | `p_explore_2.p_explore` | the only working feature |
| Подбор закона распределения | `p_fitting.p_fitting` | stub showing an "in development" notice |

`DoneStorage/p_explore.py` is an unfinished class-based rewrite (`DistributionExplorer`) of `p_explore_2.py`. It is not imported anywhere, does not run as written, and has not received the fixes made to `p_explore_2.py`; the live page is `p_explore_2.py`.

### Data flow of the explore page

1. `ParsDistributions.DistributionParser(type_rv='continuous')` scrapes the distribution list from the SciPy **devdocs** tutorial page (`scipy.github.io/devdocs/tutorial/stats/continuous.html`) with requests + BeautifulSoup, then enriches each name from the installed SciPy: docstring, the LaTeX equation cut out of the docstring's `.. math::` block, shape names from `dist.shapes`, and default shape values from the private `stats._distr_params.distcont`. `get_dictionaries()` returns five dicts keyed by scipy name (`doc_dic`, `functions_dic`, `fullname_dic`, `parameters_dic`, `url_dic`); `p_explore` unpacks them positionally from `.values()`, so their order matters.
2. Sidebar widgets yield `sliders_params`, an ordered list `[*shape_params, loc, scale]`. `get_multi_parameters` turns it into `x` (400 points between the 0.001 and 0.999 quantiles), `r` (400 random variates) and `rv` (the frozen distribution).
3. `UtilitySt.Figure` takes every display toggle plus `x, r, rv` in its constructor; `figure_display_control()` builds and returns the matplotlib figure for `st.pyplot`. Dark/light palettes are class-level dicts, and the mode is applied via global `plt.style.use`.
4. `UtilitySt.CodeGenerator` renders the exported script from one f-string template, fed with preformatted strings (`scale=…`, `loc=…`, newline-joined `shape=value` lines, comma-terminated shape names).

### Things that will bite you

- The parser needs the network. `p_explore_2.load_parser` wraps it in `st.cache_resource`, so it is built once per server process; restart the server (or clear the cache) to re-scrape. A failed request raises `ConnectionError`, which the page shows via `st.error`.
- The distribution list comes from devdocs (unreleased SciPy) while the data comes from the installed, pinned SciPy (`~=1.11.4`). `_fetch_distributions_and_hrefs` drops any distribution the installed SciPy does not have, so the list silently depends on the SciPy version.
- All parser lists (`names`, `distributions`, `urls`, `docstrings`, `equations`, parameters) are parallel and index-aligned in page order; the dicts are built by zipping them. Anything that reorders, filters or changes the length of one of them misaligns the rest.
- `type_rv='discrete'` builds its dictionaries (shapes from `distdiscrete`, `loc` only, no `scale`), but no page uses it and `p_explore` assumes `[*shapes, loc, scale]`.
- `r` is re-sampled on every rerun, so the histogram, boxplot, quantiles and statistics table change on each widget interaction. Widget bounds must not depend on `r` (a slider whose bounds change is a new widget and loses its value) — use `x` or `rv`.
- Slider bounds are derived from the SciPy default in `create_slider`: `[0.01, max(10, 2*default)]` for positive shape/scale parameters, a range reaching below zero for `loc` and for defaults `<= 0`. Nothing validates the combination, so some slider positions are invalid for a given distribution.
- Several widgets are distinguished only by trailing whitespace in their labels (`'Shine'`, `'Shine '`, `'Shine   '`, `''`, `' '`, `'   '`) to avoid duplicate-widget-ID errors — don't "clean up" those strings without adding explicit `key=`s.
- `CodeGenerator`'s template is indented inside the method and dedented with `textwrap.dedent` at the end; every substituted multi-line value must be re-indented to the template's 8 spaces first (as is done for `a`), or the dedent becomes a no-op and the exported script is not valid Python.
- The header/logo block lives under `if __name__ == "__main__":`, which is true under `streamlit run`.
