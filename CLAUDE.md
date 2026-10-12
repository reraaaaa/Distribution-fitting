# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A Streamlit app for risk managers, in Russian. Two things it does:

- **Explorer** (continuous and discrete `scipy.stats` distributions): parameter sliders, plots, a calculator (interval probability, quantiles, VaR, Expected Shortfall), a theory-versus-sample statistics table, export of a standalone script. The selected distribution and parameters live in the page address.
- **Fitting**: fits continuous distributions to the user's data by maximum likelihood, ranks them by AIC, and offers Monte Carlo goodness-of-fit p-values, bootstrap intervals and risk measures for a fitted distribution.

UI strings, docstrings and comments are in Russian; keep new user-facing text in Russian. Defaults and examples are chosen for risk work (returns and losses, heavy tails, VaR/ES at 95 / 97.5 / 99%).

## Commands

```sh
pip install -r requirements-dev.txt      # app dependencies + pytest + ruff
streamlit run streamlit_app.py           # serves on :8501; needs network at first load
pytest                                   # full suite, about 15 CPU-minutes, no network needed
pytest tests/test_fitting.py             # one file
pytest tests/test_app.py -k "norm"       # one distribution through the app
pytest -k "not all_distributions and not test_distribution_renders_and_exports_runnable_code and not test_display_toggles"   # quick suite, about 6 minutes
ruff check .
```

- Run everything from the repo root: imports are root-relative (`app_pages`, `ParsDistributions`, `UtilitySt`).
- Python 3.12+ is required (SciPy and NumPy pins). `venv/` is a local, gitignored Python 3.14 environment; Streamlit Community Cloud deploys on its default Python (3.14 at the time of writing) and cannot be told otherwise from the repo.
- Keep scratch files in `.tmp/` (gitignored), not in system temp directories.
- `requirements.txt` pins compatible-release versions (`scipy~=1.18.1`, `numpy~=2.5.4`, ...). Every pin must have a prebuilt wheel for the Python that Community Cloud uses: a pin without one makes the deploy try to compile from source and fail (this happened with scipy 1.11 on Python 3.14).
- The developer's machine is shared with other heavy work. Do not run CPU-heavy jobs in parallel, and give subagents explicit limits (no multiprocessing, a time cap per script).
- Pushing to `master` redeploys the live site at https://distribution-fitting.streamlit.app.

## Architecture

`streamlit_app.py` registers page functions with `st.navigation` (grouped) and runs the selected one. Sidebars hold inputs; results are in `st.tabs`. Everything inside every tab is computed on each rerun, so anything slow sits behind a button and a cache.

| Page | Function | Tabs |
| --- | --- | --- |
| Главная | `app_pages.introduction.p_introduction` | none |
| Непрерывные | `app_pages.explore.p_explore` | График · Калькулятор · Статистика · Код |
| Дискретные | `app_pages.explore.p_discrete` | same, on the same code (`explore_page(type_rv)`) |
| Подбор закона распределения | `app_pages.fitting.p_fitting` | Сравнение · Графики · Проверка согласия · Интервалы параметров · Калькулятор · Экспорт |

### Layers

- `ParsDistributions.DistributionParser` — scrapes the list of distributions (names, titles, links) from the SciPy **devdocs** tutorial page, then fills each entry from the installed SciPy: docstring, formula, default parameters. Result: `parser.distributions`, a dict of `DistributionInfo` keyed by scipy name, in page order. Distributions missing from the installed SciPy are dropped.
- `UtilitySt.sampling` — pure computation: `sample_distribution` (validates parameters, builds the grid `x`, draws the seeded sample `r`, returns them with the frozen `rv`), `parameter_range` (slider bounds), `integer_parameters`, `InvalidParameters`. Handles continuous and discrete distributions.
- `UtilitySt.risk` — interval probability, VaR, Expected Shortfall for either tail.
- `UtilitySt.fitting` — reading and cleaning data, `fit_distribution`, `goodness_of_fit`, `bootstrap_parameters`.
- `UtilitySt.visual` — `Figure` for continuous distributions, plus module-level functions for discrete, fit, Q-Q and interval figures.
- `UtilitySt.code_generator` — exported scripts from module-level templates.
- `app_pages` — the Streamlit layer only: widgets in, calls to the layers above, results out. `app_pages.calculator` is the calculator tab shared by all pages.

Parameters travel as one ordered dict in SciPy's positional order: `{*shape_params, 'loc', 'scale'}` for continuous, `{*shape_params, 'loc'}` for discrete. Code that unpacks it depends on that order.

### Rules that are easy to break

- **Theory versus sample.** Quartile markers, sigma shading and the "Распределение" table column come from the distribution (`rv.ppf`, `rv.mean()`, `rv.std()`, `rv.stats`). The histogram, boxplot and the "Выборка" column come from the 400 random draws. Keep labels honest about which is which; heavy-tailed distributions (cauchy, levy) have undefined or infinite moments, which must show as nan/inf or a warning, never as a sample estimate.
- **The sample is seeded.** `st.session_state.sample_seed` feeds `rv.rvs(random_state=seed)`; only the "Новая выборка" button changes it. Widget bounds must never depend on `r`.
- **The exported script must reproduce the app.** The template uses the same seed and the same grid formula as `sample_distribution`; `tests/test_code_generator.py` compares the arrays. Change both together.
- **Invalid parameters warn, never raise.** Slider ranges come from SciPy's `_shape_info()` domains, but constraints between parameters (`truncnorm` needs `a < b`) cannot be expressed as ranges. `sample_distribution` raises `InvalidParameters`, and the page shows `st.warning` while keeping the sidebar controls rendered.
- **The curve grid is not uniform.** `curve_grid` merges a uniform grid with a probability-uniform one so narrow peaks are drawn. Do not assume constant spacing in `x`.
- **The parser is cached with `st.cache_resource`** and built once per server process; restart the server to re-scrape. Samples are cached the same way and must be treated as read-only.
- **State in the address.** `share_state` rewrites `st.query_params` on every run; widgets take their initial value from it only when `dist` matches the selected distribution. Widget keys include the distribution name, so values do not leak between distributions.
- **Integer parameters.** A discrete distribution's `loc` and the shape parameters SciPy marks integral must be passed as ints (`hypergeom` rejects floats). `nbinom`'s `n` is marked integral but accepts any positive number; `integer_parameters` goes by the default value.
- **Very heavy discrete tails** make SciPy's quantile search run for seconds; `discrete_grid` checks the CDF first and rejects them.
- **Private SciPy API.** `stats._distr_params` (default shapes), `dist._argcheck` (validation) and `dist._shape_info()` (domains) are private and may change with the SciPy version. The test suite sweeps all distributions and is what will tell you.
- **Formula extraction** picks the `.. math::` block in the docstring that starts with `f(`. Nine distributions have no such block and show no formula; that is intended, a statistic's definition is not a density.

### Fitting: traps already hit

Each of these produced a wrong winner before it was guarded, and each has a regression test in `tests/test_fitting.py`.

- **Fit standardised data.** SciPy's optimiser starts from loc 0, scale 1 and fails on data in currency units or in fractions of a percent. `fit_parameters` standardises, fits, and maps loc and scale back.
- **A fitted density must integrate to at most 1 over the data.** Circular distributions (`vonmises`) and SciPy normalisation errors (`gausshyper`) otherwise win on AIC with an inflated likelihood. The integral must be adaptive with breakpoints at data quantiles: a uniform grid overshoots a steep density on heavy-tailed data several times over and rejects the true model.
- **Unbounded likelihood.** With a free loc and a shape below one, the optimiser parks a density singularity on one observation. `likelihood_spike` rejects such fits.
- **Tabulated KS p-values are inflated** when parameters come from the same data, so the table shows statistics only; p-values come from `goodness_of_fit`, which refits on every simulated sample.
- **Silent data loss is worse than an error.** `clean_data` raises when more than 5% of non-empty values fail to parse; `to_numeric` handles thousands separators, decimal commas, typographic minus signs and parentheses.
- `fit_distribution` never raises: a failed or rejected fit is a `FitResult` with a reason in `skipped`. Slow distributions are skipped by a time estimate, not a timeout.

### Tests

`tests/conftest.py` replaces the docs request with saved pages in `tests/fixtures/`, so nothing touches the network. Page tests use `streamlit.testing.v1.AppTest.from_function` on the page functions: `AppTest.switch_page` cannot reach pages registered as callables. `studentized_range` and `gausshyper` take tens of seconds per evaluation and are skipped in the numeric sweeps.
