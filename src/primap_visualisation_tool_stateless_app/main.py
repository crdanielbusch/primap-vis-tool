"""
Run the app
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import cattrs.preconf.pyyaml
import click
import primap2 as pm  # type: ignore
from loguru import logger

import primap_visualisation_tool_stateless_app.figures
import primap_visualisation_tool_stateless_app.notes.db_filepath_holder
from primap_visualisation_tool_stateless_app.callbacks import register_callbacks
from primap_visualisation_tool_stateless_app.create_app import create_app
from primap_visualisation_tool_stateless_app.dataset_handling import (
    infer_source_scenarios,
)
from primap_visualisation_tool_stateless_app.dataset_holder import (
    set_application_dataset,
)

DEFAULT_LOGGING_CONFIG = dict(
    handlers=[
        dict(
            sink=sys.stderr,
            colorize=True,
            format=" - ".join(
                [
                    "<green>{time:!UTC}</>",
                    "<lvl>{level}</>",
                    "<cyan>{name}:{file}:{line}</>",
                    "<lvl>{message}</>",
                ]
            ),
        )
    ],
)
"""Default configuration used with :meth:`loguru.logger.configure`"""


def setup_logging(config: dict[str, Any] | None = None) -> None:
    """
    Early setup for logging.

    Parameters
    ----------
    config
        Passed to :meth:`loguru.logger.configure`. If not passed,
        :const:`DEFAULT_LOGGING_CONFIG` is used.
    """
    if config is None:
        config = DEFAULT_LOGGING_CONFIG

    logger.configure(**config)
    logger.enable("primap_visualisation_tool_stateless_app")


converter_yaml = cattrs.preconf.pyyaml.make_converter()


@click.command()
@click.option("--port", default=8050, help="Port to run the app on", type=int)
@click.option(
    "--dataset",
    required=True,
    help="Dataset to visualise",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, exists=True),
)
@click.option(
    "--notes-db",
    required=False,
    default=None,
    help=(
        "Database file for notes "
        "If not supplied, we will save into a file in the same directory as the dataset,"
        "with the same name as dataset, with the extension changed to `.db`."
    ),
    type=click.Path(file_okay=True, dir_okay=False, readable=True, writable=True),
)
@click.option(
    "--plotting-config-yaml",
    required=False,
    default=None,
    help=(
        "File which defines the plotting config to use. "
        "If not supplied, we will look for a file in the same directory as the dataset,"
        "with the same name as the dataset plus 'plotting-config', "
        "with the extension changed to `.yaml`."
        "If this file does not exist, "
        "a config is created automatically and saved in the default path."
    ),
    type=click.Path(file_okay=True, dir_okay=False, readable=True, writable=True),
)
@click.option(
    "--debug/--no-debug",
    help="Should we run in debug mode",
    default=True,
)
def run_app(
    port: int,
    dataset: str,
    notes_db: str | None,
    plotting_config_yaml: str | None,
    debug: bool,
) -> None:
    """
    Run the PRIMAP visualisation tool
    """
    setup_logging()

    dataset_p = Path(dataset)
    loaded_ds = pm.open_dataset(dataset_p)
    logger.info(f"Loaded data from {dataset_p.absolute()}")
    set_application_dataset(loaded_ds)

    if plotting_config_yaml is not None:
        plotting_config_yaml_p = Path(plotting_config_yaml)

    else:
        plotting_config_yaml_default_name = f"{dataset_p.stem}_plotting-config.yaml"
        plotting_config_yaml_default = (
            dataset_p.parent / plotting_config_yaml_default_name
        )

        if plotting_config_yaml_default.exists():
            logger.info(
                "Will load plotting config from existing default file: "
                f"{plotting_config_yaml_default.absolute()}"
            )

        else:
            source_scenario_definition = infer_source_scenarios(loaded_ds)
            plotting_config = primap_visualisation_tool_stateless_app.figures.create_default_plotting_config(
                source_scenarios=source_scenario_definition
            )

            with open(plotting_config_yaml_default, "w") as fh:
                fh.write(converter_yaml.dumps(plotting_config, sort_keys=False))

            logger.info(
                f"Wrote plotting config to {plotting_config_yaml_default}. Config={plotting_config}"
            )

        plotting_config_yaml_p = plotting_config_yaml_default

    with open(plotting_config_yaml_p) as fh:
        plotting_config = converter_yaml.loads(
            fh.read(), primap_visualisation_tool_stateless_app.figures.PlottingConfig
        )

    primap_visualisation_tool_stateless_app.figures.PLOTTING_CONFIG = plotting_config

    if notes_db is None:
        notes_db_p = dataset_p.with_suffix(".db")
        logger.info(f"Will save notes into: {notes_db_p.absolute()}")
        notes_db = str(notes_db_p)

    primap_visualisation_tool_stateless_app.notes.db_filepath_holder.APPLICATION_NOTES_DB_PATH_HOLDER = Path(
        notes_db
    )

    app = create_app()
    logger.info("Created app")
    register_callbacks(app)
    logger.info("Running app")
    app.run(debug=debug, port=port)


if __name__ == "__main__":
    run_app()
