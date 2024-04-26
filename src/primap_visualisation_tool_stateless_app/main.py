"""
Run the app
"""
from __future__ import annotations

import warnings
from pathlib import Path

import click
import primap2 as pm  # type: ignore

import primap_visualisation_tool_stateless_app.notes.db_filepath_holder
from primap_visualisation_tool_stateless_app import create_app
from primap_visualisation_tool_stateless_app.callbacks import register_callbacks
from primap_visualisation_tool_stateless_app.dataset_holder import (
    set_application_dataset,
)


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
    default=Path("default-notes-db.db"),
    help="Database file for notes",
    type=click.Path(file_okay=True, dir_okay=False, readable=True, writable=True),
)
@click.option(
    "--debug/--no-debug",
    help="Should we run in debug mode",
    default=True,
)
def run_app(port: int, dataset: str, notes_db: str, debug: bool) -> None:
    """
    Run the PRIMAP visualisation tool
    """
    loaded_ds = pm.open_dataset(dataset)
    set_application_dataset(loaded_ds)

    primap_visualisation_tool_stateless_app.notes.db_filepath_holder.APPLICATION_NOTES_DB_PATH_HOLDER = Path(
        notes_db
    )

    app = create_app()
    register_callbacks(app)
    with warnings.catch_warnings(action="ignore"):  # type: ignore
        app.run(debug=debug, port=port)


if __name__ == "__main__":
    run_app()
