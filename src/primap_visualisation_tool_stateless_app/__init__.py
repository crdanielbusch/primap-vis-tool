"""
PRIMAP visualisation tool, stateless version
"""
from __future__ import annotations

import dash_bootstrap_components as dbc  # type: ignore

# from primap_visualisation_tool_stateless_app.callbacks import update_overview_figure
from dash import (
    Dash,  # type: ignore
)

from primap_visualisation_tool_stateless_app.dataset_handling import (
    get_category_options,
    get_category_start,
    get_country_options,
    get_country_start,
    get_entity_options,
    get_entity_start,
)
from primap_visualisation_tool_stateless_app.dataset_holder import (
    get_application_dataset,
)
from primap_visualisation_tool_stateless_app.layout import create_layout


def create_app() -> Dash:
    """
    Create an instance of the app

    Returns
    -------
        App instance
    """
    external_stylesheets = [dbc.themes.SIMPLEX]

    # Tell dash that we're using bootstrap for our external stylesheets so
    # that the Col and Row classes function properly
    app = Dash(__name__, external_stylesheets=external_stylesheets)

    dataset = get_application_dataset()

    layout = create_layout(
        country=get_country_start(dataset),
        country_options=get_country_options(dataset),
        category=get_category_start(dataset),
        category_options=get_category_options(dataset),
        entity=get_entity_start(dataset),
        entity_options=get_entity_options(dataset),
    )
    app.layout = dbc.Container(layout)

    return app
