"""
Run the app
"""
from __future__ import annotations

import warnings
from pathlib import Path

import click
import primap2 as pm

from primap_visualisation_tool_stateless_app import create_app
from primap_visualisation_tool_stateless_app.callbacks import register_callbacks
from primap_visualisation_tool_stateless_app.dataset_holder import (
    set_application_dataset,
)


@click.command()
@click.option("--port", default=8050, help="Port to run the app on", type=int)
@click.option("--dataset", help="Dataset to visualise", required=True, type=Path)
def run_app(port: int, dataset: Path) -> None:
    """
    Run the PRIMAP visualisation tool
    """
    loaded_ds = pm.open_dataset(dataset)
    set_application_dataset(loaded_ds)

    app = create_app()
    register_callbacks(app)
    with warnings.catch_warnings(action="ignore"):  # type: ignore
        app.run(debug=True, port=port)


if __name__ == "__main__":
    run_app()
