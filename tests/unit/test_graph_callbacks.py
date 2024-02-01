"""
Testing of callbacks related to graphs
"""
from __future__ import annotations

from contextvars import copy_context
from typing import Any
from unittest.mock import Mock

import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict

from primap_visualisation_tool.app import (
    AppState,
    update_category_graph,
    update_entity_graph,
    update_overview_graph,
    update_source_scenario_dropdown,
)

dropdowns_with_null_values = pytest.mark.parametrize(
    "country, category, entity, source_scenario",
    (
        pytest.param(
            None,
            "1",
            "CH4",
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            id="country is None",
        ),
        pytest.param(
            "New Zealand",
            None,
            "CH4",
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            id="category is None",
        ),
        pytest.param(
            "New Zealand",
            "1",
            None,
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            id="entity is None",
        ),
        pytest.param(
            "New Zealand",
            "1",
            "CH4",
            None,
            id="source-scenario is None",
        ),
        pytest.param(
            None,
            "1",
            None,
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            id="multiple values are None",
        ),
        pytest.param(None, None, None, None, id="all values are None"),
    ),
)

dropdowns_with_null_values_prop_id = pytest.mark.parametrize(
    "country, category, entity, source_scenario, prop_id",
    (
        pytest.param(
            None,
            "1",
            "CH4",
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "dropdown-country.value",
            id="country is None",
        ),
        pytest.param(
            "New Zealand",
            None,
            "CH4",
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "dropdown-category.value",
            id="category is None",
        ),
        pytest.param(
            "New Zealand",
            "1",
            None,
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "dropdown-entity.value",
            id="entity is None",
        ),
        pytest.param(
            "New Zealand",
            "1",
            "CH4",
            None,
            "dropdown-source-scenario.value",
            id="source-scenario is None",
        ),
        pytest.param(
            None,
            "1",
            None,
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "dropdown-category.value",
            id="multiple values are None",
        ),
        pytest.param(
            None, None, None, None, "dropdown-category.value", id="all values are None"
        ),
    ),
)


def get_starting_app_state(
    category_graph: Any | None = None,
    overview_graph: Any | None = None,
    entity_graph: Any | None = None,
) -> AppState:
    app_state = AppState(
        country_options=("Australia", "New Zealand"),
        country_name_iso_mapping={"Australia": "AUS", "New Zealand": "NZL"},
        country_index=0,
        category_options=("0", "1"),
        category_index=0,
        entity_options=("CO2", "CH4"),
        entity_index=0,
        source_scenario_options=(
            "PRIMAP-hist_v2.5_final_nr, HISTTP",
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
        ),
        source_scenario_index=0,
        ds="not used",
        category_graph=category_graph,
        overview_graph=overview_graph,
        entity_graph=entity_graph,
    )

    return app_state


def check_starting_values_dont_clash_with_starting_state(
    app_state: AppState,
    starting_country: str,
    starting_category: str,
    starting_entity: str,
    starting_source_scenario: str,
) -> None:
    assert app_state.country != starting_country
    assert app_state.category != starting_category
    assert app_state.entity != starting_entity
    assert app_state.source_scenario != starting_source_scenario


@dropdowns_with_null_values
@pytest.mark.parametrize(
    "memory_data_start, memory_data_exp",
    (
        pytest.param(None, {"_": 0}, id="brand_new"),
        pytest.param({"_": 3}, {"_": 4}, id="increment_existing"),
    ),
)
def test_update_source_scenario_dropdown(  # noqa: PLR0913
    country,
    category,
    entity,
    source_scenario,
    memory_data_start,
    memory_data_exp,
):
    app_state = get_starting_app_state(
        overview_graph="Mock starting value",
    )
    check_starting_values_dont_clash_with_starting_state(
        app_state=app_state,
        starting_country=country,
        starting_category=category,
        starting_entity=entity,
        starting_source_scenario=source_scenario,
    )

    res = update_source_scenario_dropdown(
        country=country,
        category=category,
        entity=entity,
        source_scenario=source_scenario,
        memory_data=memory_data_start,
        app_state=app_state,
    )

    # Check that memory data remains the same value
    assert res[2] == memory_data_start

    # This checks that update_all_indexes wasn't called i.e. that the app state
    # hasn't changed
    assert app_state.country != country
    assert app_state.category != category
    assert app_state.entity != entity
    assert app_state.source_scenario != source_scenario

    if country and category and entity and source_scenario:
        assert res[2] == memory_data_exp


@dropdowns_with_null_values
def test_update_overview_graph_can_handle_null_selection(
    country, category, entity, source_scenario
):
    # This callback will not be triggered when None is selected for source_scenario
    # Therefore, there is nothing in the app to deal with this case
    # TODO: add a test to ensure this logic actually happens
    if source_scenario is None:
        return

    app_state = get_starting_app_state(
        overview_graph="Mock starting value",
    )
    check_starting_values_dont_clash_with_starting_state(
        app_state=app_state,
        starting_country=country,
        starting_category=category,
        starting_entity=entity,
        starting_source_scenario=source_scenario,
    )

    res = update_overview_graph(
        country=country,
        category=category,
        entity=entity,
        memory_data=0,
        app_state=app_state,
    )

    # This checks that the returned value is just taken from the existing figure
    assert res == app_state.overview_graph

    # This checks that update_all_indexes wasn't called i.e. that the app state
    # hasn't changed
    assert app_state.country != country
    assert app_state.category != category
    assert app_state.entity != entity
    assert app_state.source_scenario != source_scenario


@dropdowns_with_null_values_prop_id
def test_update_category_graph_can_handle_null_selection(
    country, category, entity, source_scenario, prop_id
):
    app_state = get_starting_app_state(
        category_graph="Mock starting value",
    )
    check_starting_values_dont_clash_with_starting_state(
        app_state=app_state,
        starting_country=country,
        starting_category=category,
        starting_entity=entity,
        starting_source_scenario=source_scenario,
    )

    # irrelevant for this test, but needs to be dict
    layout_data = {"mock": "mock"}

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_category_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=0,
            layout_data=layout_data,
            app_state=app_state,
        )

    ctx = copy_context()
    res = ctx.run(run_callback)

    # This checks that the returned value is just taken from the existing figure
    assert res == app_state.category_graph

    # This checks that update_all_indexes wasn't called i.e. that the app state
    # hasn't changed
    assert app_state.country != country
    assert app_state.category != category
    assert app_state.entity != entity
    assert app_state.source_scenario != source_scenario


@dropdowns_with_null_values_prop_id
def test_update_entity_graph_can_handle_null_selection(
    country, category, entity, source_scenario, prop_id
):
    app_state = get_starting_app_state(
        entity_graph="Mock starting value",
    )
    check_starting_values_dont_clash_with_starting_state(
        app_state=app_state,
        starting_country=country,
        starting_category=category,
        starting_entity=entity,
        starting_source_scenario=source_scenario,
    )

    # irrelevant for this test, but needs to be dict
    layout_data = {"mock": "mock"}

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_entity_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=0,
            layout_data=layout_data,
            app_state=app_state,
        )

    ctx = copy_context()
    res = ctx.run(run_callback)

    # This checks that the returned value is just taken from the existing figure
    assert res == app_state.entity_graph

    # This checks that update_all_indexes wasn't called i.e. that the app state
    # hasn't changed
    assert app_state.country != country
    assert app_state.category != category
    assert app_state.entity != entity
    assert app_state.source_scenario != source_scenario


def test_update_entity_graph_xrange_is_triggered():
    app_state = Mock()

    country = "AUS"
    category = "M0EL"
    entity = "CO2"
    source_scenario = "PRIMAP-hist_v2.5_final_nr, HISTTP"
    memory_data = None
    layout_data = {"xaxis.range": ["2018-01-09 07:23:20.8123", "2022-01-01"]}
    prop_id = "graph-overview.relayoutData"

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_entity_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=memory_data,
            layout_data=layout_data,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    # check calls
    app_state.update_entity_xrange.assert_called_once_with(layout_data)


def test_update_category_graph_xrange_is_triggered():
    app_state = Mock()

    country = "AUS"
    category = "M0EL"
    entity = "CO2"
    source_scenario = "PRIMAP-hist_v2.5_final_nr, HISTTP"
    memory_data = None
    layout_data = {"xaxis.range": ["2018-01-09 07:23:20.8123", "2022-01-01"]}
    prop_id = "graph-overview.relayoutData"

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_category_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=memory_data,
            layout_data=layout_data,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    # check calls
    app_state.update_category_xrange.assert_called_once_with(layout_data)
