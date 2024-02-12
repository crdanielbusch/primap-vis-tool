# Primap visualisation tool

<!---
Can use start-after and end-before directives in docs, see
https://myst-parser.readthedocs.io/en/latest/syntax/organising_content.html#inserting-other-documents-directly-into-the-current-document
-->

<!--- sec-begin-description -->

This app visualises GHG-emissions over time based on sectors, countries and entities. It is based on the Primap dataset.



[![CI](https://github.com/crdanielbusch/primap-visualisation-tool/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/crdanielbusch/primap-visualisation-tool/actions/workflows/ci.yaml)
[![Coverage](https://codecov.io/gh/crdanielbusch/primap-visualisation-tool/branch/main/graph/badge.svg)](https://codecov.io/gh/crdanielbusch/primap-visualisation-tool)
[![Docs](https://readthedocs.org/projects/primap-visualisation-tool/badge/?version=latest)](https://primap-visualisation-tool.readthedocs.io)

**PyPI :**
[![PyPI](https://img.shields.io/pypi/v/primap-visualisation-tool.svg)](https://pypi.org/project/primap-visualisation-tool/)
[![PyPI: Supported Python versions](https://img.shields.io/pypi/pyversions/primap-visualisation-tool.svg)](https://pypi.org/project/primap-visualisation-tool/)
[![PyPI install](https://github.com/crdanielbusch/primap-visualisation-tool/actions/workflows/install.yaml/badge.svg?branch=main)](https://github.com/crdanielbusch/primap-visualisation-tool/actions/workflows/install.yaml)

**Other info :**
[![License](https://img.shields.io/github/license/crdanielbusch/primap-visualisation-tool.svg)](https://github.com/crdanielbusch/primap-visualisation-tool/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/crdanielbusch/primap-visualisation-tool.svg)](https://github.com/crdanielbusch/primap-visualisation-tool/commits/main)
[![Contributors](https://img.shields.io/github/contributors/crdanielbusch/primap-visualisation-tool.svg)](https://github.com/crdanielbusch/primap-visualisation-tool/graphs/contributors)


<!--- sec-end-description -->

Full documentation can be found at:
[primap-visualisation-tool.readthedocs.io](https://primap-visualisation-tool.readthedocs.io/en/latest/).
We recommend reading the docs there because the internal documentation links
don't render correctly on GitHub's viewer.

## Installation

<!--- sec-begin-installation -->

Primap visualisation tool can be installed with conda or pip:

```bash
pip install primap-visualisation-tool
conda install -c conda-forge primap-visualisation-tool
```

Additional dependencies can be installed using

```bash
# To add plotting dependencies
pip install primap-visualisation-tool[plots]

# If you are installing with conda, we recommend
# installing the extras by hand because there is no stable
# solution yet (issue here: https://github.com/conda/conda/issues/7502)
```

## Run the app

The data file required to run the app is not included here. It can be retrieved from
[here](https://gin.hemio.de/jguetschow/PRIMAP-hist_visualization_tool/src/master/data/combined/combined_data_v2.5_final_v2.4.2_final.nc).

The file should be saved in the `data` directory.

To run the app, run the following command in the root directory

```bash
poetry run python src/primap_visualisation_tool/app.py
```

The same command is executed with

```bash
make run-app
```

Use `-p` to specifiy the port number and `-f`to select a file in the `data`directory.

```bash
poetry run python src/primap_visualisation_tool/app.py -p <my-port-number> -f <my-file-name>
```


<!--- sec-end-installation -->

### For developers

<!--- sec-begin-installation-dev -->

For development, we rely on [poetry](https://python-poetry.org) for all our
dependency management. To get started, you will need to make sure that poetry
is installed
([instructions here](https://python-poetry.org/docs/#installing-with-the-official-installer),
we found that pipx and pip worked better to install on a Mac).

For all of work, we use our `Makefile`.
You can read the instructions out and run the commands by hand if you wish,
but we generally discourage this because it can be error prone.
In order to create your environment, run `make virtual-environment`.

If there are any issues, the messages from the `Makefile` should guide you
through. If not, please raise an issue in the [issue tracker][issue_tracker].

For the rest of our developer docs, please see [](development-reference).

[issue_tracker]: https://github.com/crdanielbusch/primap-visualisation-tool/issues

<!--- sec-end-installation-dev -->
