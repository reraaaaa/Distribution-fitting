<div align="left">
    <img src="https://img.icons8.com/?size=512&id=55494&format=png" width="40%" align="left" style="margin-right: 15px"/>
    <div style="display: inline-block;">
        <h2 style="display: inline-block; vertical-align: middle; margin-top: 0;">DISTRIBUTION-FITTING</h2>
        <p>
	<em>Unleashing Data Insights, One Distribution at a Time!</em>
</p>
        <p>
	<img src="https://img.shields.io/github/license/reraaaaa/Distribution-fitting?style=default&logo=opensourceinitiative&logoColor=white&color=0080ff" alt="license">
	<img src="https://img.shields.io/github/last-commit/reraaaaa/Distribution-fitting?style=default&logo=git&logoColor=white&color=0080ff" alt="last-commit">
	<img src="https://img.shields.io/github/languages/top/reraaaaa/Distribution-fitting?style=default&color=0080ff" alt="repo-top-language">
	<img src="https://img.shields.io/github/languages/count/reraaaaa/Distribution-fitting?style=default&color=0080ff" alt="repo-language-count">
</p>
        <p><!-- default option, no dependency badges. -->
</p>
        <p>
	<!-- default option, no dependency badges. -->
</p>
    </div>
</div>
<br clear="left"/>

##  Table of Contents

- [ Overview](#-overview)
- [ Features](#-features)
- [ Project Structure](#-project-structure)
  - [ Project Index](#-project-index)
- [ Getting Started](#-getting-started)
  - [ Prerequisites](#-prerequisites)
  - [ Installation](#-installation)
  - [ Usage](#-usage)
  - [ Testing](#-testing)
- [ Project Roadmap](#-project-roadmap)
- [ Contributing](#-contributing)
- [ License](#-license)
- [ Acknowledgments](#-acknowledgments)

---

##  Overview

The Distribution-fitting project is an interactive tool designed to simplify statistical data analysis. It allows users to explore, visualize, and fit various statistical distributions, generating Python code for selected distributions. With features like adjustable parameters, descriptive statistics, and data visualization techniques, it's a valuable resource for data scientists, statisticians, and anyone working with data.

---

##  Features

|      | Feature         | Summary       |
| :--- | :---:           | :---          |
| ⚙️  | **Architecture**  | <ul><li>The project is structured into different modules such as `DoneStorage`, `UtilitySt`, and `ParsDistributions` for better organization and separation of concerns.</li><li>The main entry point is `streamlit_app.py` which orchestrates the user interface and functionalities.</li><li>The project uses a modular architecture, with different functionalities encapsulated in different Python scripts.</li></ul> |
| 🔩 | **Code Quality**  | <ul><li>The codebase is written in Python, with a focus on readability and maintainability.</li><li>It follows Python's best practices and coding standards.</li><li>Each Python script has a specific role, making the codebase easier to understand and navigate.</li></ul> |
| 📄 | **Documentation** | <ul><li>The project uses Python as its primary language and has a total of 9 Python files.</li><li>It provides detailed documentation for each Python script, explaining its role and functionality.</li><li>The project uses `pip` as its package manager and provides detailed installation and usage instructions.</li></ul> |
| 🔌 | **Integrations**  | <ul><li>The project integrates with various Python libraries such as `matplotlib`, `scipy`, `numpy`, `pandas`, `requests`, `beautifulsoup4`, `cmasher`, `bokeh`, and `streamlit`.</li><li>It uses `pip` for managing dependencies.</li></ul> |
| 🧩 | **Modularity**    | <ul><li>The project is highly modular, with different functionalities encapsulated in different Python scripts.</li><li>It uses a modular architecture, allowing for easy addition, removal, or modification of features.</li></ul> |
| 🧪 | **Testing**       | <ul><li>The project uses `pytest` for running tests.</li><li>However, the test commands and test cases are not provided in the documentation.</li></ul> |
| ⚡️  | **Performance**   | <ul><li>The project uses efficient Python libraries such as `numpy` and `pandas` for data manipulation, which are known for their performance.</li><li>However, specific performance metrics or benchmarks are not provided in the documentation.</li></ul> |
| 🛡️ | **Security**      | <ul><li>The project does not mention any specific security measures or practices.</li><li>As it's a data analysis and visualization tool, it may not require extensive security measures.</li></ul> |
| 📦 | **Dependencies**  | <ul><li>The project has dependencies on several Python libraries, listed in `requirements.txt`.</li><li>These include libraries for data manipulation (`pandas`, `numpy`), data visualization (`matplotlib`, `bokeh`, `streamlit`), and web scraping (`beautifulsoup4`, `requests`).</li></ul> |

---

##  Project Structure

```sh
└── Distribution-fitting/
    ├── DoneStorage
    │   ├── p_explore.py
    │   ├── p_explore_2.py
    │   ├── p_fitting.py
    │   └── p_introduction.py
    ├── LICENSE
    ├── ParsDistributions
    │   ├── __init__.py
    │   └── parser.py
    ├── README.md
    ├── UtilitySt
    │   ├── __init__.py
    │   ├── code_generator.py
    │   └── visual.py
    ├── images
    │   └── logo_w.png
    ├── requirements
    │   └── requirements.txt
    ├── requirements.txt
    ├── setup.py
    └── streamlit_app.py
```


###  Project Index
<details open>
	<summary><b><code>DISTRIBUTION-FITTING/</code></b></summary>
	<details> <!-- __root__ Submodule -->
		<summary><b>__root__</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/streamlit_app.py'>streamlit_app.py</a></b></td>
				<td>- Streamlit_app.py serves as the main entry point for the Distribution-Fitting application<br>- It orchestrates the user interface, allowing users to navigate between the introduction, distribution exploration, and distribution fitting functionalities<br>- Additionally, it provides information about the project and its authors in the sidebar.</td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/requirements.txt'>requirements.txt</a></b></td>
				<td>- Requirements.txt outlines the necessary libraries for the project, including data manipulation tools like pandas and numpy, data visualization libraries such as matplotlib, bokeh, and streamlit, and web scraping utilities like beautifulsoup4 and requests<br>- It ensures consistent environment setup across different development stages.</td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/setup.py'>setup.py</a></b></td>
				<td>- Setup.py serves as the build script for the 'Distribution-fitting' project<br>- It defines the project metadata, including its name, version, author, and dependencies<br>- The script also specifies the packages to be included in the distribution<br>- It plays a crucial role in preparing the project for distribution and installation.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- DoneStorage Submodule -->
		<summary><b>DoneStorage</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/DoneStorage/p_explore_2.py'>p_explore_2.py</a></b></td>
				<td>- The `p_explore_2.py` file is part of the DoneStorage project and plays a crucial role in the data exploration and visualization aspect of the codebase<br>- It leverages libraries such as Streamlit, Scipy, Pandas, Numpy, Matplotlib, and custom modules to facilitate this.

The primary function of this file is to parse and explore different distributions of data<br>- It uses the `DistributionParser` class from the `ParsDistributions.parser` module to parse continuous data distributions<br>- The parsed data is then used to generate dictionaries that contain various details about the data, such as documentation, functions, full names, parameters, and URLs.

Additionally, the file contains a function `make_expanders` that is used to create expanders in the user interface, which contain a set of options<br>- This function is designed to enhance the user experience by providing a more organized and interactive way to display options.

Overall, this file is a key component in the project's data exploration and visualization pipeline, enabling users to interactively explore and understand the data distributions.</td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/DoneStorage/p_explore.py'>p_explore.py</a></b></td>
				<td>- The 'p_explore.py' file in the 'DoneStorage' directory is a key component of the project, enabling the exploration and visualization of various statistical distributions<br>- It provides interactive sliders and manual input fields for parameter adjustment, generates descriptive statistics, and offers Python code generation for selected distributions.</td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/DoneStorage/p_fitting.py'>p_fitting.py</a></b></td>
				<td>- P_fitting within DoneStorage contributes to the overall codebase by providing a placeholder function<br>- Currently, it doesn't perform any operations but serves as a foundation for future development<br>- It's expected to play a significant role in the project's functionality once fully implemented.</td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/DoneStorage/p_introduction.py'>p_introduction.py</a></b></td>
				<td>- The 'p_introduction.py' in the 'DoneStorage' directory serves as the introductory interface for the Distribution Fitting application<br>- It generates a user-friendly sidebar and main content area, providing an overview of the application's features, instructions for use, and visual aids<br>- It also includes sections for distribution selection, display customization, data import, fitting, and results export.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- UtilitySt Submodule -->
		<summary><b>UtilitySt</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/UtilitySt/code_generator.py'>code_generator.py</a></b></td>
				<td>- CodeGenerator in UtilitySt/code_generator.py generates Python code for statistical analysis and visualization<br>- It creates a script that imports necessary libraries, sets parameters, generates random numbers based on a specified distribution, and plots the probability density function, cumulative distribution function, survival function, histogram, and boxplot of the generated data.</td>
			</tr>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/UtilitySt/visual.py'>visual.py</a></b></td>
				<td>- The 'visual.py' file in the 'UtilitySt' directory is a Python script that provides a class for creating and managing various types of statistical plots<br>- It supports different color schemes, plot styles, and data visualization techniques such as histograms, boxplots, and PDF/CDF lines<br>- The script also includes features for highlighting specific data points and adjusting plot aesthetics.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- ParsDistributions Submodule -->
		<summary><b>ParsDistributions</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/ParsDistributions/parser.py'>parser.py</a></b></td>
				<td>- The 'parser.py' in the ParsDistributions project serves as a comprehensive tool for extracting and analyzing statistical distribution data from the SciPy documentation<br>- It retrieves distribution names, documentation strings, mathematical functions, parameters, and generates URLs for both continuous and discrete distributions<br>- This information is then organized into dictionaries, providing programmatic access to detailed information about the distributions.</td>
			</tr>
			</table>
		</blockquote>
	</details>
	<details> <!-- requirements Submodule -->
		<summary><b>requirements</b></summary>
		<blockquote>
			<table>
			<tr>
				<td><b><a href='https://github.com/reraaaaa/Distribution-fitting/blob/master/requirements/requirements.txt'>requirements.txt</a></b></td>
				<td>- Requirements.txt outlines the necessary libraries for the project, including data manipulation tools like pandas and numpy, data visualization libraries such as matplotlib, bokeh, and streamlit, and web scraping utilities like beautifulsoup4 and requests<br>- These dependencies ensure the project's functionality and compatibility across different environments.</td>
			</tr>
			</table>
		</blockquote>
	</details>
</details>

---
##  Getting Started

###  Prerequisites

Before getting started with Distribution-fitting, ensure your runtime environment meets the following requirements:

- **Programming Language:** Python
- **Package Manager:** Pip


###  Installation

Install Distribution-fitting using one of the following methods:

**Build from source:**

1. Clone the Distribution-fitting repository:
```sh
❯ git clone https://github.com/reraaaaa/Distribution-fitting
```

2. Navigate to the project directory:
```sh
❯ cd Distribution-fitting
```

3. Install the project dependencies:


**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ pip install -r requirements.txt, requirements/requirements.txt
```




###  Usage
Run Distribution-fitting using the following command:
**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ python {entrypoint}
```


###  Testing
Run the test suite using the following command:
**Using `pip`** &nbsp; [<img align="center" src="https://img.shields.io/badge/Pip-3776AB.svg?style={badge_style}&logo=pypi&logoColor=white" />](https://pypi.org/project/pip/)

```sh
❯ pytest
```


---
##  Project Roadmap

- [X] **`Task 1`**: <strike>Implement feature one.</strike>
- [ ] **`Task 2`**: Implement feature two.
- [ ] **`Task 3`**: Implement feature three.

---

##  Contributing

- **💬 [Join the Discussions](https://github.com/reraaaaa/Distribution-fitting/discussions)**: Share your insights, provide feedback, or ask questions.
- **🐛 [Report Issues](https://github.com/reraaaaa/Distribution-fitting/issues)**: Submit bugs found or log feature requests for the `Distribution-fitting` project.
- **💡 [Submit Pull Requests](https://github.com/reraaaaa/Distribution-fitting/blob/main/CONTRIBUTING.md)**: Review open PRs, and submit your own PRs.

<details closed>
<summary>Contributing Guidelines</summary>

1. **Fork the Repository**: Start by forking the project repository to your github account.
2. **Clone Locally**: Clone the forked repository to your local machine using a git client.
   ```sh
   git clone https://github.com/reraaaaa/Distribution-fitting
   ```
3. **Create a New Branch**: Always work on a new branch, giving it a descriptive name.
   ```sh
   git checkout -b new-feature-x
   ```
4. **Make Your Changes**: Develop and test your changes locally.
5. **Commit Your Changes**: Commit with a clear message describing your updates.
   ```sh
   git commit -m 'Implemented new feature x.'
   ```
6. **Push to github**: Push the changes to your forked repository.
   ```sh
   git push origin new-feature-x
   ```
7. **Submit a Pull Request**: Create a PR against the original project repository. Clearly describe the changes and their motivations.
8. **Review**: Once your PR is reviewed and approved, it will be merged into the main branch. Congratulations on your contribution!
</details>

<details closed>
<summary>Contributor Graph</summary>
<br>
<p align="left">
   <a href="https://github.com{/reraaaaa/Distribution-fitting/}graphs/contributors">
      <img src="https://contrib.rocks/image?repo=reraaaaa/Distribution-fitting">
   </a>
</p>
</details>

---

##  License

This project is protected under the [SELECT-A-LICENSE](https://choosealicense.com/licenses) License. For more details, refer to the [LICENSE](https://choosealicense.com/licenses/) file.

---

##  Acknowledgments

- List any resources, contributors, inspiration, etc. here.

---