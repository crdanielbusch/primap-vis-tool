"""
Test that our entity dropdown does what we expect

This may end up being re-named/combined with tests of our other drop-downs,
depending on how much duplication there is.
"""

from __future__ import annotations

import copy
from contextvars import copy_context

import xarray as xr
from dash._callback_context import context_value
from dash._utils import AttributeDict

from primap_visualisation_tool.app import (
    AppState,
    get_country_options,
    handle_entity_click,
)

# Tests to write:
# - test that the entity dropdown does what we want
#   - update entity dropdown to a new value
#   - check
#     - source-scenario dropdown updates
#       - should update to reflect only the source-scenarios in the new entity
#     - entity figure updates
#       - fairly self-explanatory
#     - category figure updates
#       - should update to reflect only the categories in the new entity
#     - main figure updates
#       - should update to reflect only the source-scenarios in the new entity
#   - inputs for the test
#     - dataset (we'll need to create)
#   - cases
#     - nothing needs to change in source-scenario dropdown
#     - nothing needs to change in main figure
#     - things need to change in source-scenario dropdown
#     - things need to change in main figure
#     - entity plot has to always update, as does the category plot
#       - category plot might show same categories
#       - category plot might show different categories


def create_testing_dataset() -> xr.Dataset:
    raise NotImplementedError()


def create_app_state(  # noqa: PLR0913
    dataset: xr.Dataset,
    start_country: str | None = None,
    start_category: str | None = None,
    start_entity: str | None = None,
    start_source_scenario: str | None = None,
    filename: str = "testing_app_state",
    present_index_cols: list[str] | None = None,
    category_dimension: str = "category (IPCC2006_PRIMAP)",
    source_scenario_dimension: str = "SourceScen",
) -> AppState:
    country_name_iso_mapping = get_country_options(dataset)
    country_dropdown_options = tuple(sorted(country_name_iso_mapping.keys()))

    category_options = tuple(dataset[category_dimension].to_numpy())

    entity_options = tuple(i for i in dataset.data_vars)

    source_scenario_options = tuple(dataset[source_scenario_dimension].to_numpy())
    source_scenario_visible = {
        k: v
        for (k, v) in zip(
            source_scenario_options, [True] * len(source_scenario_options)
        )
    }

    if present_index_cols is None:
        present_index_cols = ["not", "used"]

    app_state = AppState(
        country_options=country_dropdown_options,
        country_name_iso_mapping=country_name_iso_mapping,
        country_index=country_dropdown_options.index(start_country),
        category_options=category_options,
        category_index=category_options.index(start_category),
        entity_options=entity_options,
        entity_index=entity_options.index(start_entity),
        source_scenario_options=source_scenario_options,
        source_scenario_index=source_scenario_options.index(start_source_scenario),
        source_scenario_visible=source_scenario_visible,
        ds=dataset,
        filename=filename,
        present_index_cols=present_index_cols,
    )

    return app_state


def test_entity_click_one_forward_switch_from_co2_to_hfcs():
    starting_entity = "CO2"
    dataset = create_testing_dataset()
    app_state = create_app_state(dataset)
    starting_categories = app_state.category_options
    exp_categories = copy.deepcopy(starting_categories)

    # We would have preferred to just update the entity value,
    # then see what happens.
    # However, we couldn't work out if an API for that exists
    # so we're just doing it this way instead.
    def run_callback():
        raise NotImplementedError(  # noqa: TRY003
            "need to define where call is coming from"
        )
        context_value.set(
            AttributeDict(**{"triggered_inputs": [{"Something": "must go here"}]})
        )

        return handle_entity_click(
            entity_in=starting_entity,
            n_clicks_next_entity=1,
            n_clicks_previous_entity=0,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    exp_new_entity = "HFCS (SARGWP100)"
    assert app_state.entity == exp_new_entity

    exp_source_scenario_options = ["PRIMAP_hist_2.5.1", "RCMIP"]
    assert app_state.source_scenario == exp_source_scenario_options

    # TODO in future MR: update this so that the categories change to only available categories
    # (x-ref timeseries selection section in #27)
    assert app_state.category_options == exp_categories

    assert app_state.entity_graph
    assert False, "Figure out what we can test about this reliably"

    assert app_state.category_graph
    assert False, "Figure out what we can test about this reliably"

    assert app_state.overview_graph
    assert False, "Figure out what we can test about this reliably"

    assert False, "Write test"
