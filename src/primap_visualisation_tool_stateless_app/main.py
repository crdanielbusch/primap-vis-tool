"""
Run the app
"""
from __future__ import annotations

from pathlib import Path

import click
import primap2 as pm  # type: ignore

import primap_visualisation_tool_stateless_app.notes.db_filepath_holder
from primap_visualisation_tool_stateless_app.callbacks import register_callbacks
from primap_visualisation_tool_stateless_app.create_app import create_app
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
    default=None,
    help=(
        "Database file for notes "
        "(if not supplied, we will save into a file in the same directory as the dataset,"
        "with the same name as dataset, "
        "with the extension changed to `.db`)"
    ),
    type=click.Path(file_okay=True, dir_okay=False, readable=True, writable=True),
)
@click.option(
    "--debug/--no-debug",
    help="Should we run in debug mode",
    default=True,
)
def run_app(port: int, dataset: str, notes_db: str | None, debug: bool) -> None:
    """
    Run the PRIMAP visualisation tool
    """
    dataset = Path(dataset)
    loaded_ds = pm.open_dataset(dataset)
    set_application_dataset(loaded_ds)

    if notes_db is None:
        notes_db = dataset.with_suffix(".db")

    primap_visualisation_tool_stateless_app.notes.db_filepath_holder.APPLICATION_NOTES_DB_PATH_HOLDER = Path(
        notes_db
    )

    app = create_app()
    register_callbacks(app)
    app.run(debug=debug, port=port)


if __name__ == "__main__":
    run_app()
