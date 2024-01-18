"""
Testing of callbacks related to graphs
"""
from __future__ import annotations

from typing import Any

import pytest

from primap_visualisation_tool.app import (
    AppState,
    update_category_graph,
    update_overview_graph,
)

dropdowns_with_null_values = pytest.mark.parametrize(
    "country, category, entity",
    (
        pytest.param(None, "1", "CH4", id="country is None"),
        pytest.param("NZL", None, "CH4", id="category is None"),
        pytest.param("NZL", "1", None, id="entity is None"),
        pytest.param(None, "1", None, id="multiple values are None"),
        pytest.param(None, None, None, id="all values are None"),
    ),
)


def get_starting_app_state(
    category_graph: Any | None = None, overview_graph: Any | None = None
) -> AppState:
    app_state = AppState(
        country_options=("AUS", "NZL"),
        country_index=0,
        category_options=("0", "1"),
        category_index=0,
        entity_options=("CO2", "CH4"),
        entity_index=0,
        category_graph=category_graph,
        overview_graph=overview_graph,
    )

    return app_state


def check_starting_values_dont_clash_with_starting_state(
    app_state: AppState,
    starting_country: str,
    starting_category: str,
    starting_entity: str,
) -> None:
    assert app_state.country != starting_country
    assert app_state.category != starting_category
    assert app_state.entity != starting_entity


@dropdowns_with_null_values
def test_update_overview_graph_can_handle_null_selection(country, category, entity):
    app_state = get_starting_app_state(
        category_graph="Mock starting value",
    )
    check_starting_values_dont_clash_with_starting_state(
        app_state=app_state,
        starting_country=country,
        starting_category=category,
        starting_entity=entity,
    )

    res = update_overview_graph(
        country=country, category=category, entity=entity, app_state=app_state
    )

    # This checks that the returned value is just taken from the existing figure
    assert res == app_state.overview_graph

    # This checks that update_all_indexes wasn't called i.e. that the app state
    # hasn't changed
    assert app_state.country != country
    assert app_state.category != category
    assert app_state.entity != entity


@dropdowns_with_null_values
def test_update_category_graph_can_handle_null_selection(country, category, entity):
    app_state = get_starting_app_state()
    check_starting_values_dont_clash_with_starting_state(
        app_state=app_state,
        starting_country=country,
        starting_category=category,
        starting_entity=entity,
    )

    res = update_category_graph(
        country=country, category=category, entity=entity, app_state=app_state
    )

    # This checks that the returned value is just taken from the existing figure
    assert res == app_state.category_graph

    # This checks that update_all_indexes wasn't called i.e. that the app state
    # hasn't changed
    assert app_state.country != country
    assert app_state.category != category
    assert app_state.entity != entity
