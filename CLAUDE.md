# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit app with two features. The explorer shows `scipy.stats` continuous distributions interactively: parameter sliders, PDF/CDF/SF plots, a theory-versus-sample statistics table, export of a standalone Python script. The fitting page fits distributions to the user's data by maximum likelihood and ranks them by AIC.

UI strings, docstrings and comments are in Russian; keep new user-facing text in Russian.

## Commands

```sh
pip install -r requirements-dev.txt      # app dependencies + pytest + ruff
streamlit run streamlit_app.py           # serves on :8501; needs network at first load
pytest                                   # full suite, about 10 minutes, no network needed
pytest tests/test_sampling.py            # one file
pytest tests/test_app.py -k "norm"       # one distribution through the app
pytest --deselect tests/test_app.py::test_distribution_renders_and_exports_runnable_code   # skip the per-distribution sweep
ruff check .
```

- Run everything from the repo root: imports are root-relative (`app_pages`, `ParsDistributions`, `UtilitySt`).
- Python 3.12+ is required (SciPy and NumPy pins). `venv/` is a local, gitignored Python 3.14 environment; Streamlit Community Cloud deploys on its default Python (3.14 at the time of writing) and cannot be told otherwise from the repo.
- Keep scratch files in `.tmp/` (gitignored), not in system temp directories.
- `requirements.txt` pins compatible-release versions (`scipy~=1.18.1`, `numpy~=2.5.4`, ...). Every pin must have a prebuilt wheel for the Python that Community Cloud uses: a pin without one makes the deploy try to compile from source and fail (this happened with scipy 1.11 on Python 3.14).

## Architecture

`streamlit_app.py` registers three page functions with `st.navigation` / `st.Page` and runs the selected one.

| Page | Function | State |
| --- | --- | --- |
| Главная | `app_pages.introduction.p_introduction` | static text; `image1..6` are empty placeholders, skipped while empty |
| База распределений | `app_pages.explore.p_explore` | the only working feature |
| Подбор закона распределения | `app_pages.fitting.p_fitting` | fits distributions to uploaded data; written 2026-10-13, statistical review not finished (see PLAN_FITTING.md) |

### Layers

- `ParsDistributions.DistributionParser` — scrapes the list of distributions (names, titles, links) from the SciPy **devdocs** tutorial page, then fills each entry from the installed SciPy: docstring, density formula, default parameters. Result: `parser.distributions`, a dict of `DistributionInfo` keyed by scipy name, in page order. Distributions missing from the installed SciPy are dropped.
- `UtilitySt.sampling` — pure computation, no Streamlit: `sample_distribution` (validates parameters, builds the curve grid `x`, draws the seeded sample `r`, returns them with the frozen `rv` as a `Sample`), `parameter_range` (slider bounds), `InvalidParameters`.
- `UtilitySt.visual` — `Figure(settings, x, r, rv)` draws the matplotlib figure from a `DisplaySettings` dataclass.
- `UtilitySt.code_generator` — `CodeGenerator(distribution, parameters, seed)` renders the exported script from a module-level template.
- `UtilitySt.fitting` — pure computation for the fitting page: reading and cleaning data (`read_table`, `clean_data`), `fit_distribution` (never raises; a failed or rejected fit comes back as a `FitResult` with a reason in `skipped`), `results_table`. Fitted densities whose mass over the data range exceeds 1 are rejected (`probability_mass_over_data`): circular distributions such as `vonmises` and SciPy normalisation errors otherwise win on AIC with an inflated likelihood. Slow distributions are skipped by a time estimate rather than a timeout.
- `app_pages.explore` — the Streamlit layer: widgets produce a parameter dict and a `DisplaySettings`, everything else is delegated to the layers above.

Parameters travel as one ordered dict, `{*shape_params, 'loc', 'scale'}`, in SciPy's positional order. `sample_distribution` and `CodeGenerator` both unpack it as `*shapes, loc, scale`, so the order is load-bearing.

### Rules that are easy to break

- **Theory versus sample.** Quartile markers, sigma shading and the "Распределение" table column come from the distribution (`rv.ppf`, `rv.mean()`, `rv.std()`, `rv.stats`). The histogram, boxplot and the "Выборка" column come from the 400 random draws. Keep labels honest about which is which; heavy-tailed distributions (cauchy, levy) have undefined or infinite moments, which must show as nan/inf or a warning, never as a sample estimate.
- **The sample is seeded.** `st.session_state.sample_seed` feeds `rv.rvs(random_state=seed)`; only the "Новая выборка" button changes it. Widget bounds must never depend on `r`.
- **The exported script must reproduce the app.** The template uses the same seed and the same grid formula as `sample_distribution`; `tests/test_code_generator.py` compares the arrays. Change both together.
- **Invalid parameters warn, never raise.** Slider ranges come from SciPy's `_shape_info()` domains, but constraints between parameters (`truncnorm` needs `a < b`) cannot be expressed as ranges. `sample_distribution` raises `InvalidParameters`, and the page shows `st.warning` while keeping the sidebar controls rendered.
- **The curve grid is not uniform.** `curve_grid` merges a uniform grid with a probability-uniform one so narrow peaks are drawn. Do not assume constant spacing in `x`.
- **The parser is cached with `st.cache_resource`** and built once per server process; restart the server to re-scrape. Samples are cached the same way and must be treated as read-only.
- **Private SciPy API.** `stats._distr_params` (default shapes), `dist._argcheck` (validation) and `dist._shape_info()` (domains) are private and may change with the SciPy version. The test suite sweeps all distributions and is what will tell you.
- **Formula extraction** picks the `.. math::` block in the docstring that starts with `f(`. Nine distributions have no such block and show no formula; that is intended, a statistic's definition is not a density.

### Tests

`tests/conftest.py` replaces the docs request with saved pages in `tests/fixtures/`, so nothing touches the network. Page tests use `streamlit.testing.v1.AppTest.from_function` on the page functions: `AppTest.switch_page` cannot reach pages registered as callables. `studentized_range` and `gausshyper` take tens of seconds per evaluation and are skipped in the numeric sweeps.
