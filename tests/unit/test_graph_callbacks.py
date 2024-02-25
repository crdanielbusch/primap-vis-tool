"""
Testing of callbacks related to graphs
"""
from __future__ import annotations

import os
from contextvars import copy_context
from typing import Any
from unittest.mock import Mock

import pandas as pd
import pytest
from dash._callback_context import context_value
from dash._utils import AttributeDict
from dash.exceptions import PreventUpdate  # type: ignore
from pandas.testing import assert_frame_equal

from primap_visualisation_tool.app import (
    AppState,
    get_filename,
    save_note,
    update_category_graph,
    update_entity_graph,
    update_overview_graph,
    update_source_scenario_dropdown,
    update_table,
    update_xyrange_category_figure,
    update_xyrange_entity_figure,
    update_xyrange_overview_figure,
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
        source_scenario_visible={"not": "used"},
        ds="not used",
        category_graph=category_graph,
        overview_graph=overview_graph,
        entity_graph=entity_graph,
        filename="test_filename",
        present_index_cols=["not", "used"],
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
        xyrange_data={"not", "used"},
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


@dropdowns_with_null_values
def test_update_category_graph_can_handle_null_selection(
    country, category, entity, source_scenario
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

    def run_callback():
        context_value.set(
            AttributeDict(**{"triggered_inputs": [{"prop_id": "not used"}]})
        )
        return update_category_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=0,
            xyrange_data={"not", "used"},
            xyrange_data_entity={"not", "used"},
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


@dropdowns_with_null_values
def test_update_entity_graph_can_handle_null_selection(
    country, category, entity, source_scenario
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

    def run_callback():
        context_value.set(
            AttributeDict(**{"triggered_inputs": [{"prop_id": "not used"}]})
        )
        return update_entity_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=0,
            xyrange_data={"not", "used"},
            xyrange_data_category={"not", "used"},
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


def test_update_entity_graph_is_triggered():
    app_state = Mock()

    country = "AUS"
    category = "M0EL"
    entity = "CO2"
    source_scenario = "PRIMAP-hist_v2.5_final_nr, HISTTP"
    memory_data = None
    xyrange_data = {"not", "used"}
    prop_id = "xyrange-entity.data"

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_entity_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=memory_data,
            xyrange_data={"not", "used"},
            xyrange_data_category={"not", "used"},
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    # check calls
    app_state.update_entity_range.assert_called_once_with(xyrange_data)


def test_update_category_graph_update_range_is_triggered():
    app_state = Mock()

    country = "AUS"
    category = "M0EL"
    entity = "CO2"
    source_scenario = "PRIMAP-hist_v2.5_final_nr, HISTTP"
    memory_data = None
    xyrange_data = {"not", "used"}
    xyrange_data_entity = {"not", "used"}
    prop_id = "xyrange-category.data"

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_category_graph(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            memory_data=memory_data,
            xyrange_data=xyrange_data,
            xyrange_data_entity=xyrange_data_entity,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    # check calls
    app_state.update_category_range.assert_called_once_with(xyrange_data)


def test_save_note_return_nothing_when_empty_text_area():
    save_button_clicks = 0  # not needed
    app_state = Mock()
    text_input = None
    memory_data = ["not", "needed"]

    res = save_note(save_button_clicks, memory_data, text_input, app_state)

    assert res == ("", "")


def test_save_note_clear_when_change_state():
    save_button_clicks = 0  # not needed
    app_state = Mock()
    text_input = "Some text"
    memory_data = ["not", "needed"]

    def run_callback():
        context_value.set(
            AttributeDict(**{"triggered_inputs": [{"prop_id": "memory.data"}]})
        )
        return save_note(
            save_button_clicks=save_button_clicks,
            memory_data=memory_data,
            text_input=text_input,
            app_state=app_state,
        )

    ctx = copy_context()
    res = ctx.run(run_callback)

    assert res == ("", "")


def test_save_note():
    save_button_clicks = 0  # not needed
    memory_data = ["not", "needed"]
    app_state = get_starting_app_state()

    # input from user
    text_input = "any text"

    expected_output = pd.DataFrame(
        {
            "country": app_state.country_name_iso_mapping[
                app_state.country_options[app_state.country_index]
            ],
            "category": app_state.category_options[app_state.category_index],
            "entity": app_state.entity_options[app_state.entity_index],
            "note": "any text",
        },
        index=[0],
    )

    def run_callback():
        context_value.set(
            AttributeDict(**{"triggered_inputs": [{"prop_id": "save_button.n_clicks"}]})
        )
        return save_note(
            save_button_clicks=save_button_clicks,
            memory_data=memory_data,
            text_input=text_input,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    filename = f"{app_state.filename[:-3]}_notes.csv"

    output = pd.read_csv(filename, header=0, dtype=str)

    os.remove(filename)

    assert_frame_equal(output, expected_output)


@pytest.mark.xfail
def test_get_get_column_defs():
    app_state = get_starting_app_state()

    expected_outcome = [
        {"field": "time", "sortable": True, "filter": "agNumberColumnFilter"},
        {"field": "area (ISO3)", "sortable": True},
        {"field": "category (IPCC2006_PRIMAP)", "sortable": True},
        {"field": "SourceScen", "sortable": True},
        {"field": app_state.entity, "sortable": True, "filter": "agNumberColumnFilter"},
    ]

    res = app_state.get_column_defs()

    assert res == expected_outcome


def test_get_row_data():
    app_state = Mock()
    memory_data = {"not", "used"}

    update_table(memory_data, app_state)

    app_state.get_row_data.assert_called_once_with()
    app_state.get_column_defs.assert_called_once_with()


@pytest.mark.parametrize(
    "user_input, test_ds, current_version, old_version, test_ds_name, expected_res",
    (
        pytest.param(
            "mock_dataset_name.nc",
            False,
            "not needed",
            "not needed",
            "not needed",
            "mock_dataset_name.nc",
            id="User input, test data set False",
        ),
        pytest.param(
            "mock_dataset_name.nc",
            True,
            "not needed",
            "not needed",
            "not needed",
            "mock_dataset_name.nc",
            id="User input, test data set True",
        ),
        pytest.param(
            None,
            True,
            "not needed",
            "not needed",
            "test_ds.nc",
            "test_ds.nc",
            id="No user input, test data set True",
        ),
        pytest.param(
            None,
            False,
            "v2.5_final",
            "v2.4.2_final",
            "not needed",
            "combined_data_v2.5_final_v2.4.2_final.nc",
            id="No user input, test data set False",
        ),
    ),
)
def test_get_filename(  # noqa: PLR0913
    user_input, test_ds, expected_res, current_version, old_version, test_ds_name
):
    res = get_filename(
        user_input=user_input,
        test_ds=test_ds,
        current_version=current_version,
        old_version=old_version,
        test_ds_name=test_ds_name,
    )

    assert res == expected_res


@pytest.mark.parametrize(
    "prop_id, layout_data_overview, layout_data_category, layout_data_entity",
    (
        pytest.param(
            "not needed",
            None,
            "not needed",
            "not needed",
            id="layout_data_overview is None",
        ),
        pytest.param(
            "not needed",
            "not needed",
            None,
            "not needed",
            id="layout_data_category is None",
        ),
        pytest.param(
            "not needed",
            "not needed",
            "not needed",
            None,
            id="layout_data_entity is None",
        ),
        pytest.param(
            "graph-overview.relayoutData",
            "{'dragmode': 'zoom'}",
            "not needed",
            "not needed",
            id="User selects zoom in overview figure",
        ),
        pytest.param(
            "graph-category-split.relayoutData",
            "{'dragmode': 'zoom'}",
            "not needed",
            "not needed",
            id="User selects zoom in category figure",
        ),
        pytest.param(
            "graph-entity-split.relayoutData",
            "{'dragmode': 'zoom'}",
            "not needed",
            "not needed",
            id="User selects zoom in category figure",
        ),
    ),
)
def test_update_xyrange_overview_figure_prevent_update(
    prop_id, layout_data_overview, layout_data_category, layout_data_entity
):
    app_state = get_starting_app_state()

    figure_overview_dict = {"not", "used"}
    figure_category_dict = {"not", "used"}
    figure_entity_dict = {"not", "used"}

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_xyrange_overview_figure(
            layout_data_overview=layout_data_overview,
            layout_data_category=layout_data_category,
            layout_data_entity=layout_data_entity,
            figure_overview_dict=figure_overview_dict,
            figure_category_dict=figure_category_dict,
            figure_entity_dict=figure_entity_dict,
            app_state=app_state,
        )

    ctx = copy_context()

    with pytest.raises(PreventUpdate) as excinfo:
        ctx.run(run_callback)

    assert excinfo.type == PreventUpdate


@pytest.mark.parametrize(
    "prop_id, layout_data_overview, layout_data_category,"
    " layout_data_entity, x_source_figure, y_source_figure, autorange",
    (
        pytest.param(
            "graph-overview.relayoutData",
            "{'xaxis.range': ['2018-09-11 09:06:26.6349', '2021-08-01 17:45:23.6277']}",
            "not needed",
            "not needed",
            "figure_overview_dict",
            "figure_overview_dict",
            False,
            id="User selects rangeslider in overview plot",
        ),
        pytest.param(
            "graph-overview.relayoutData",
            "{'xaxis.autorange': True}",
            "not needed",
            "not needed",
            "figure_overview_dict",
            "figure_overview_dict",
            True,
            id="User clicks on autorange in overview plot",
        ),
        pytest.param(
            "graph-category-split.relayoutData",
            "not needed",
            {
                "xaxis.range[0]": "",
                "xaxis.range[1]": "",
                "yaxis.range[0]": 0,
                "yaxis.range[1]": 0,
            },
            "not needed",
            "figure_category_dict",
            "figure_category_dict",
            False,
            id="User changes view in category plot",
        ),
        pytest.param(
            "graph-category-split.relayoutData",
            "not needed",
            {"xaxis.autorange": True},
            "not needed",
            "figure_category_dict",
            "figure_category_dict",
            True,
            id="User selects autorange or reset axes in category plot",
        ),
        pytest.param(
            "graph-entity-split.relayoutData",
            "not needed",
            "not needed",
            {
                "xaxis.range[0]": "",
                "xaxis.range[1]": "",
                "yaxis.range[0]": 0,
                "yaxis.range[1]": 0,
            },
            "figure_entity_dict",
            "figure_entity_dict",
            False,
            id="User changes view in entity plot",
        ),
        pytest.param(
            "graph-entity-split.relayoutData",
            "not needed",
            "not needed",
            {"xaxis.autorange": True},
            "figure_entity_dict",
            "figure_entity_dict",
            True,
            id="User selects autorange or reset axes in entity plot",
        ),
    ),
)
def test_update_xyrange_overview_figure(  # noqa: PLR0913
    prop_id,
    layout_data_overview,
    layout_data_category,
    layout_data_entity,
    x_source_figure,
    y_source_figure,
    autorange,
):
    app_state = Mock()
    figure_overview_dict = "mock figure_overview_dict"
    figure_category_dict = "mock figure_category_dict"
    figure_entity_dict = "mock figure_entity_dict"

    # dict to assign varibale to test scenario
    figure_dicts = {
        "figure_overview_dict": figure_overview_dict,
        "figure_category_dict": figure_category_dict,
        "figure_entity_dict": figure_entity_dict,
    }

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_xyrange_overview_figure(
            layout_data_overview=layout_data_overview,
            layout_data_category=layout_data_category,
            layout_data_entity=layout_data_entity,
            figure_overview_dict=figure_overview_dict,
            figure_category_dict=figure_category_dict,
            figure_entity_dict=figure_entity_dict,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    app_state.get_xyrange_from_figure.assert_called_once_with(
        x_source_figure=figure_dicts[x_source_figure],
        y_source_figure=figure_dicts[y_source_figure],
        autorange=autorange,
    )


@pytest.mark.parametrize(
    "prop_id, layout_data_overview, layout_data_entity",
    (
        pytest.param(
            "not needed",
            None,
            "not needed",
            id="layout_data_overview is None",
        ),
        pytest.param(
            "not needed",
            "not needed",
            None,
            id="layout_data_entity is None",
        ),
        pytest.param(
            "graph-overview.relayoutData",
            "{'dragmode': 'zoom'}",
            "not needed",
            id="User uses buttons in overview figure but layout stays",
        ),
        pytest.param(
            "graph-entity-split.relayoutData",
            "not needed",
            "{'dragmode': 'zoom'}",
            id="User uses buttons in entity figure but layout stays",
        ),
    ),
)
def test_update_xyrange_category_figure_prevent_update(
    prop_id, layout_data_overview, layout_data_entity
):
    app_state = get_starting_app_state()

    figure_overview_dict = {"not", "used"}
    figure_category_dict = {"not", "used"}
    figure_entity_dict = {"not", "used"}

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_xyrange_category_figure(
            layout_data_overview=layout_data_overview,
            layout_data_entity=layout_data_entity,
            figure_overview_dict=figure_overview_dict,
            figure_category_dict=figure_category_dict,
            figure_entity_dict=figure_entity_dict,
            app_state=app_state,
        )

    ctx = copy_context()

    with pytest.raises(PreventUpdate) as excinfo:
        ctx.run(run_callback)

    assert excinfo.type == PreventUpdate


@pytest.mark.parametrize(
    "prop_id, layout_data_overview, layout_data_entity, x_source_figure, y_source_figure, autorange",
    (
        pytest.param(
            "graph-overview.relayoutData",
            "{'xaxis.range': ['2018-09-11 09:06:26.6349', '2021-08-01 17:45:23.6277']}",
            "not needed",
            "figure_overview_dict",
            "figure_category_dict",
            False,
            id="User selects rangeslider in overview plot",
        ),
        pytest.param(
            "graph-overview.relayoutData",
            "{'xaxis.autorange': True}",
            "not needed",
            "figure_overview_dict",
            "figure_category_dict",
            True,
            id="User clicks on autorange in overview plot",
        ),
        pytest.param(
            "graph-entity-split.relayoutData",
            "not needed",
            {
                "xaxis.range[0]": "",
                "xaxis.range[1]": "",
                "yaxis.range[0]": 0,
                "yaxis.range[1]": 0,
            },
            "figure_entity_dict",
            "figure_entity_dict",
            False,
            id="User changes view in entity plot",
        ),
        pytest.param(
            "graph-entity-split.relayoutData",
            "not needed",
            {"xaxis.autorange": True},
            "figure_entity_dict",
            "figure_entity_dict",
            True,
            id="User selects autorange or reset axes in entity plot",
        ),
    ),
)
def test_update_xyrange_category_figure(  # noqa: PLR0913
    prop_id,
    layout_data_overview,
    layout_data_entity,
    x_source_figure,
    y_source_figure,
    autorange,
):
    app_state = Mock()
    figure_overview_dict = "mock figure_overview_dict"
    figure_category_dict = "mock figure_category_dict"
    figure_entity_dict = "mock figure_entity_dict"

    # dict to assign varibales to test scenario
    figure_dicts = {
        "figure_overview_dict": figure_overview_dict,
        "figure_category_dict": figure_category_dict,
        "figure_entity_dict": figure_entity_dict,
    }

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_xyrange_category_figure(
            layout_data_overview=layout_data_overview,
            layout_data_entity=layout_data_entity,
            figure_overview_dict=figure_overview_dict,
            figure_category_dict=figure_category_dict,
            figure_entity_dict=figure_entity_dict,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    app_state.get_xyrange_from_figure.assert_called_once_with(
        x_source_figure=figure_dicts[x_source_figure],
        y_source_figure=figure_dicts[y_source_figure],
        autorange=autorange,
    )


@pytest.mark.parametrize(
    "prop_id, layout_data_overview, layout_data_category",
    (
        pytest.param(
            "not needed",
            None,
            "not needed",
            id="layout_data_overview is None",
        ),
        pytest.param(
            "not needed",
            "not needed",
            None,
            id="layout_data_category is None",
        ),
        pytest.param(
            "graph-overview.relayoutData",
            "{'dragmode': 'zoom'}",
            "not needed",
            id="User selects zoom in overview figure",
        ),
        pytest.param(
            "graph-category-split.relayoutData",
            "not needed",
            "{'dragmode': 'zoom'}",
            id="User selects zoom in category figure",
        ),
    ),
)
def test_update_xyrange_entity_figure_prevent_update(
    prop_id, layout_data_overview, layout_data_category
):
    app_state = get_starting_app_state()

    figure_overview_dict = {"not", "used"}
    figure_category_dict = {"not", "used"}
    figure_entity_dict = {"not", "used"}

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_xyrange_entity_figure(
            layout_data_overview=layout_data_overview,
            layout_data_category=layout_data_category,
            figure_overview_dict=figure_overview_dict,
            figure_category_dict=figure_category_dict,
            figure_entity_dict=figure_entity_dict,
            app_state=app_state,
        )

    ctx = copy_context()

    with pytest.raises(PreventUpdate) as excinfo:
        ctx.run(run_callback)

    assert excinfo.type == PreventUpdate


@pytest.mark.parametrize(
    "prop_id, layout_data_overview, layout_data_category, x_source_figure, y_source_figure, autorange",
    (
        pytest.param(
            "graph-overview.relayoutData",
            "{'xaxis.range': ['2018-09-11 09:06:26.6349', '2021-08-01 17:45:23.6277']}",
            "not needed",
            "figure_overview_dict",
            "figure_entity_dict",
            False,
            id="User selects rangeslider in overview plot",
        ),
        pytest.param(
            "graph-overview.relayoutData",
            "{'xaxis.autorange': True}",
            "not needed",
            "figure_overview_dict",
            "figure_entity_dict",
            True,
            id="User clicks on autorange in overview plot",
        ),
        pytest.param(
            "graph-category-split.relayoutData",
            "not needed",
            {
                "xaxis.range[0]": "",
                "xaxis.range[1]": "",
                "yaxis.range[0]": 0,
                "yaxis.range[1]": 0,
            },
            "figure_category_dict",
            "figure_category_dict",
            False,
            id="User changes view in category plot",
        ),
        pytest.param(
            "graph-category-split.relayoutData",
            "not needed",
            {"xaxis.autorange": True},
            "figure_category_dict",
            "figure_category_dict",
            True,
            id="User selects autorange or reset axes in category plot",
        ),
    ),
)
def test_update_xyrange_entity_figure(  # noqa: PLR0913
    prop_id,
    layout_data_overview,
    layout_data_category,
    x_source_figure,
    y_source_figure,
    autorange,
):
    app_state = Mock()
    figure_overview_dict = "mock figure_overview_dict"
    figure_category_dict = "mock figure_category_dict"
    figure_entity_dict = "mock figure_entity_dict"

    # dict to assign varibales from test scenario
    figure_dicts = {
        "figure_overview_dict": figure_overview_dict,
        "figure_category_dict": figure_category_dict,
        "figure_entity_dict": figure_entity_dict,
    }

    def run_callback():
        context_value.set(AttributeDict(**{"triggered_inputs": [{"prop_id": prop_id}]}))
        return update_xyrange_entity_figure(
            layout_data_overview=layout_data_overview,
            layout_data_category=layout_data_category,
            figure_overview_dict=figure_overview_dict,
            figure_category_dict=figure_category_dict,
            figure_entity_dict=figure_entity_dict,
            app_state=app_state,
        )

    ctx = copy_context()
    ctx.run(run_callback)

    app_state.get_xyrange_from_figure.assert_called_once_with(
        x_source_figure=figure_dicts[x_source_figure],
        y_source_figure=figure_dicts[y_source_figure],
        autorange=autorange,
    )


# rangeslider in overview figure
# {'xaxis.range': ['2018-09-11 09:06:26.6349', '2021-08-01 17:45:23.6277']}
# {'xaxis.autorange': True}
# {'dragmode': 'pan'}
# {'dragmode': 'zoom'}
# {'xaxis.autorange': True, 'xaxis.showspikes': False}
