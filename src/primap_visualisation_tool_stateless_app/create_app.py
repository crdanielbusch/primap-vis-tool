"""
Creation of app instances
"""
from __future__ import annotations

import dash_bootstrap_components as dbc  # type: ignore
from dash import Dash  # type: ignore

from primap_visualisation_tool_stateless_app.dataset_handling import (
    get_category_options,
    get_category_start,
    get_country_options,
    get_country_start,
    get_entity_option_split_by_gwp_annotation,
    get_entity_options,
    get_entity_start,
    get_source_scenario_options,
    get_source_scenario_start,
)
from primap_visualisation_tool_stateless_app.dataset_holder import (
    get_application_dataset,
)
from primap_visualisation_tool_stateless_app.dropdown_defaults import (
    get_dropdown_defaults,
)
from primap_visualisation_tool_stateless_app.layout import create_layout


def create_app() -> Dash:  # type: ignore
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
        country=get_country_start(
            dataset, preferred_starting_country=get_dropdown_defaults().country
        ),
        country_options=get_country_options(dataset),
        category=get_category_start(
            dataset, preferred_starting_category=get_dropdown_defaults().category
        ),
        category_options=get_category_options(dataset),
        entity=get_entity_start(
            dataset, preferred_starting_entity=get_dropdown_defaults().entity
        ),
        entity_options=get_entity_options(dataset),
        all_entities_by_gwp=get_entity_option_split_by_gwp_annotation(dataset),
        gwp=get_dropdown_defaults().gwp,
        source_scenario=get_source_scenario_start(dataset),
        source_scenario_options=get_source_scenario_options(dataset),
    )
    app.layout = dbc.Container(
        layout,
        style={"max-width": "none", "width": "100%"},
    )

    return app
