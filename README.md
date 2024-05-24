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

Full documentation can (soon, once we have uploaded it [TODO set up RtD?]) be found at:
[primap-visualisation-tool.readthedocs.io](https://primap-visualisation-tool.readthedocs.io/en/latest/).
We recommend reading the docs there because the internal documentation links
don't render correctly on GitHub's viewer.

## Installation

<!--- sec-begin-installation -->

The PRIMAP visualisation tool can be installed from source with:

```bash
poetry install --all-extras
```

Primap visualisation tool can (soon, once we have set it up [TODO make available on RtD?]) be installed with conda or pip:

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

<!--- sec-end-installation -->

## Run the app

<!--- sec-begin-run -->

The first time you run the app, we suggest simply running it from the root directory with

```bash
poetry run python src/primap_visualisation_tool_stateless_app/main.py --dataset <path-to-dataset>
```

If you don't have a dataset available already, simply use `tests/test-data/test_ds.nc`, e.g.

```bash
poetry run python src/primap_visualisation_tool_stateless_app/main.py --dataset tests/test-data/test_ds.nc
```

### Plotting configuration

The first time you run the app, it will create a plotting configuration file for you.
The file will be saved in the same directory as your dataset
and will be named `<dataset-name>_plotting-config.yaml`.
For example, with the test file `tests/test-data/test_ds.nc`,
the created file is `tests/test-data/test_ds_plotting-config.yaml`.

The plotting configuration file allows you to change the configuration of the plots made by the tool.
Each key in the `source_scenario_settings` section is the name of a source-scenario in the data file.
Each value is itself a dictionary.
As the user, for each source-scenario, you can set its "color", "dash" and "width".

The next time you run the app, the configuration file will be used for configuration.
If you wish, you can make a copy of the configuration file and save it elsewhere.
Then, tell the app to use the configuration file with the `--plotting-config-yaml` option, e.g.

```bash
poetry run python src/primap_visualisation_tool_stateless_app/main.py --dataset <path-to-dataset> --plotting-config-yaml <path-to-plotting-config-yaml>
```

### Notes database and other options

The app's other options are quite self-explanatory.
A help message can be shown with:

```bash
poetry run python src/primap_visualisation_tool_stateless_app/main.py --help
```

The key other option for most users is `--notes-db`.
This option allows you to specify the file in which to save the notes database.
If it is not supplied,
a file in the same directory as your dataset, named `<dataset-name>.db` will be used.
For example, with the test file `tests/test-data/test_ds.nc`,
the default notes database file is `tests/test-data/test_ds.db`.
For post-processing, this notes file can be read into a :obj:`pd.DataFrame`
using {py:func}`primap_visualisation_tool_stateless_app.notes.db.read_country_notes_db_as_pd`.

<!--- sec-end-run -->

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

### Code layout/structure

Dash doesn't play nicely with global state.
[TODO: find issues etc. where we have discussed this]
Hence, we try to avoid using global state wherever possible.
This isn't perfect because we don't have a true front-end, back-end split,
but the current set up is close enough for the tests to mostly behave.

The app itself lives in `src/primap_visualisation_tool_stateless_app`.
The command-line interface to run the app lives in `src/primap_visualisation_tool_stateless_app/main.py`.
The other files handle the other components of the app, including:

- callbacks
- creation of app instances
- handling the PRIMAP dataset (e.g. filtering, re-shaping)
- holding the dataset
  - dash doesn't like global state, so we do this in a way which is more like
    having a back-end, although it is not exactly a back-end so more thought
    would be needed for a truely stateless app with a separate back- and front-end
- creating/updating figures
- setting up the app's layout
