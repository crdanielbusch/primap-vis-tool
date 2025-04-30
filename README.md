# Primap visualisation tool

<!---
Can use start-after and end-before directives in docs, see
https://myst-parser.readthedocs.io/en/latest/syntax/organising_content.html#inserting-other-documents-directly-into-the-current-document
-->

<!--- sec-begin-description -->

This app visualises GHG-emissions over time based on sectors, countries and entities. It is based on the Primap dataset.

[![CI](https://github.com/crdanielbusch/primap-vis-tool/actions/workflows/ci.yaml/badge.svg?branch=main)](https://github.com/crdanielbusch/primap-vis-tool/actions/workflows/ci.yaml)

**Other info :**
[![License](https://img.shields.io/github/license/crdanielbusch/primap-vis-tool.svg)](https://github.com/crdanielbusch/primap-vis-tool/blob/main/LICENSE)
[![Last Commit](https://img.shields.io/github/last-commit/crdanielbusch/primap-vis-tool.svg)](https://github.com/crdanielbusch/primap-vis-tool/commits/main)
[![Contributors](https://img.shields.io/github/contributors/crdanielbusch/primap-vis-tool.svg)](https://github.com/crdanielbusch/primap-vis-tool/graphs/contributors)

<!--- sec-end-description -->

## Installation

<!--- sec-begin-installation -->

The PRIMAP visualisation tool can be installed from source
by first cloning the repository, then running:

```sh
poetry install --all-extras
```

<!--- sec-end-installation -->

## Run the app

<!--- sec-begin-run-overview -->

The first time you run the app, we suggest simply running it from the root directory with

```sh
poetry run python src/primap_visualisation_tool_stateless_app/main.py --dataset <path-to-dataset>
```

If you don't have a dataset available already, simply use `tests/test-data/test_ds.nc`, e.g.

```sh
poetry run python src/primap_visualisation_tool_stateless_app/main.py --dataset tests/test-data/test_ds.nc
```

<!--- sec-end-run-overview -->

### Plotting configuration

<!--- sec-begin-run-plotting-config -->

The first time you run the app, it will create a plotting configuration file for you.
The file will be saved in the same directory as your dataset
and will be named `<dataset-name>_plotting-config.yaml`.
For example, with the test file `tests/test-data/test_ds.nc`,
the created file is `tests/test-data/test_ds_plotting-config.yaml`.

The plotting configuration file allows you to change the configuration of the plots made by the tool.
Each key in the `source_scenario_settings` section is the name of a source-scenario in the data file.
Each value is itself a dictionary.
As the user, for each source-scenario, you can set its "color", "dash" and "width".

An example is shown below:


```yaml
# Example format of the YAML format
# For the real source of truth, see `tests/test-data/test_ds_plotting-config.yaml`
source_scenario_settings:
  PRIMAP-hist_v2.5_final_nr, HISTCR:
    color: rgb(0, 0, 0)
    dash: solid
    width: 3
  source_2, scenario_2:
    color: rgb(0, 0, 0)
    dash: dot
    width: 1
```

The next time you run the app, the configuration file will be used for configuration.
If you wish, you can make a copy of the configuration file and save it elsewhere.
Then, tell the app to use the configuration file with the `--plotting-config-yaml` option, e.g.

```bash
poetry run python src/primap_visualisation_tool_stateless_app/main.py --dataset <path-to-dataset> --plotting-config-yaml <path-to-plotting-config-yaml>
```

<!--- sec-end-run-plotting-config -->

### Notes database and other options

<!--- sec-begin-run-notes-db-other -->

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
For post-processing, this notes file can be read into a {py:obj}`pandas.DataFrame`
using {py:func}`primap_visualisation_tool_stateless_app.notes.db.read_country_notes_db_as_pd`.

<!--- sec-end-run-notes-db-other -->

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

To run the tests, you will need to install
[chrome driver](https://developer.chrome.com/docs/chromedriver/).
If you get an error like
".. Message: session not created: This version of ChromeDriver only supports Chrome version ..."
this means you need to update your Chrome driver.
On a Mac, this can be done with something like
`brew install --cask chromedriver`.

For the rest of our developer docs, please see [](development-reference).

[issue_tracker]: https://github.com/crdanielbusch/primap-vis-tool/issues

<!--- sec-end-installation-dev -->

## Licence

Copyright 2023-2025, Climate Resource Pty Ltd

Licensed under the Apache License, Version 2.0 (the "Licence"); you may not use this
project except in compliance with the Licence. You may obtain a copy of the Licence at

<https://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software distributed under
the Licence is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied. See the Licence for the specific language governing
permissions and limitations under the Licence.
