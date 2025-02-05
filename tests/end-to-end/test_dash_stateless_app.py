"""
End to end testing of an app that doesn't use global state
"""

from __future__ import annotations

import re
import time
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import dash
import dash.testing
import primap2 as pm
import pytest
import selenium.webdriver.remote.webelement
import xarray as xr
from dash import html
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

import primap_visualisation_tool_stateless_app
import primap_visualisation_tool_stateless_app.callbacks
import primap_visualisation_tool_stateless_app.create_app
import primap_visualisation_tool_stateless_app.dataset_holder
import primap_visualisation_tool_stateless_app.figures
import primap_visualisation_tool_stateless_app.notes
import primap_visualisation_tool_stateless_app.notes.db_filepath_holder
from primap_visualisation_tool_stateless_app.iso_mapping import name_to_iso3

TEST_DATA_DIR = Path(__file__).parent.parent / "test-data"
TEST_DS_FILE = TEST_DATA_DIR / "test_ds.nc"


def get_element_workaround(
    dash_duo,
    expected_id_component: str,
    class_name: str = "dash-graph",
    timeout: float = 5.0,
    repeat_freq: float = 0.5,
) -> Any:
    """
    Get an element in the page

    This is a workaround.
    It feels like there should be a way to do this directly via the dash_duo API,
    I just can't work out what it is.

    Parameters
    ----------
    dash_duo
        Dash duo instance

    expected_id_component
        The string we expected to find in the component's ID

    class_name
        The element's class name

    timeout
        How long to wait before timing out

    repeat_freq
        How quickly to check if there are new elements

    Returns
    -------
        Element that has an ID that matches ``expected_id_component``.

    Raises
    ------
    ValueError
        More than one element has an ID that matches ``expected_id_component``.

    KeyError
        No elements have an ID that matches ``expected_id_component``.
    """
    now = time.time()
    while time.time() < (now + timeout):
        matching = []
        try:
            found_elements = dash_duo.driver.find_elements(By.CLASS_NAME, class_name)
            for element in found_elements:
                if expected_id_component in element.get_attribute("id"):
                    matching.append(element)

        except selenium.common.exceptions.StaleElementReferenceException:
            continue

        if len(matching) == 1:
            return matching[0]

        if len(matching) > 1:
            matching_element_ids = [e.get_attribute("id") for e in matching]
            msg = (
                "More than one element has an id that contains {expected_id_component}. "
                f"{matching_element_ids=}"
            )
            raise ValueError(msg)

        time.sleep(repeat_freq)

    available_element_ids = [e.get_attribute("id") for e in found_elements]
    msg = (
        f"No element with an id containing {expected_id_component} was found. "
        f"We looked for elements with {class_name=}. "
        f"The element ids we found were {available_element_ids}."
    )
    raise KeyError(msg)


@pytest.fixture
def app_default():
    test_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )
    app = primap_visualisation_tool_stateless_app.create_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)

    return app


def setup_app(
    dash_duo, ds: xr.Dataset, db_path: Path | None = None
) -> dash.testing.composite.DashComposite:
    """
    Setup the app
    """
    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(ds)
    if db_path is not None:
        primap_visualisation_tool_stateless_app.notes.db_filepath_holder.APPLICATION_NOTES_DB_PATH_HOLDER = (
            db_path
        )

    app = primap_visualisation_tool_stateless_app.create_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    # Returning the app too may be necessary at some point
    return dash_duo


def test_001_dash_example(dash_duo):
    # A test that the dash example runs.
    # If this breaks things are really broken - i.e. there is an issue beyond our code.
    app = dash.Dash(__name__)
    app.layout = html.Div(id="nully-wrapper", children=0)
    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("#nully-wrapper", "0", timeout=4)
    assert dash_duo.find_element("#nully-wrapper").text == "0"


def test_002_app_starts(dash_duo, app_default):
    dash_duo.start_server(app_default)

    # Give time to sort out and shut down
    time.sleep(2)


def test_003_dropdown_country(dash_duo, tmp_path):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    tmp_db = tmp_path / "003_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_contains_text("#dropdown-country", "EARTH", timeout=4)

    # Give time to sort out and shut down
    time.sleep(2)


def test_004_dropdown_country_earth_not_present(dash_duo):
    test_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_file)
    test_ds = test_ds.pr.loc[{"area (ISO3)": ["AUT", "AUS"]}]

    setup_app(dash_duo=dash_duo, ds=test_ds)

    dash_duo.wait_for_contains_text("#dropdown-country", "Australia", timeout=4)

    # Give time to sort out and shut down
    time.sleep(2)


def test_005_dropdown_category(dash_duo):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    setup_app(dash_duo=dash_duo, ds=test_ds)

    dash_duo.wait_for_contains_text("#dropdown-category", "M.0.EL", timeout=4)

    # Give time to sort out and shut down
    time.sleep(2)


def test_006_dropdown_entity(dash_duo):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    setup_app(dash_duo=dash_duo, ds=test_ds)

    dash_duo.wait_for_contains_text("#dropdown-entity", "CO2", timeout=4)

    # Give time to sort out and shut down
    time.sleep(2)


def test_007_country_buttons(dash_duo, tmp_path):
    test_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_file)

    tmp_db = tmp_path / "007_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("next_country", timeout=2)

    dash_duo.wait_for_contains_text("#dropdown-country", "EARTH", timeout=4)

    # Click next
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # Country dropdown should update
    dash_duo.wait_for_contains_text("#dropdown-country", "EU27BX", timeout=4)

    # Click previous
    button_country_prev = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_prev.click()

    # Country dropdown should be back to where it started
    dash_duo.wait_for_contains_text("#dropdown-country", "EARTH", timeout=4)

    # Give time to sort out and shut down
    time.sleep(2)


def test_008_initial_figures(dash_duo, tmp_path):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    tmp_db = tmp_path / "008_notes_database.db"

    setup_app(dash_duo=dash_duo, ds=test_ds, db_path=tmp_db)

    # Add a sleep to give the page time to load.
    # Working out if the page is actually loaded looks incredibly difficult
    # (e.g. https://stackoverflow.com/a/11002061),
    # hence we go for this very basic solution.
    time.sleep(2.0)

    # Make sure that expected elements are on the page before continuing
    get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-overview", timeout=5
    )
    get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-entity-split", timeout=5
    )

    # If we don't provide plotting config, the defaults are used
    source_scenario_definition = (
        primap_visualisation_tool_stateless_app.dataset_handling.infer_source_scenarios(
            test_ds
        )
    )
    plotting_config = (
        primap_visualisation_tool_stateless_app.figures.create_default_plotting_config(
            source_scenarios=source_scenario_definition
        )
    )

    expected_graph_overview_source_scenarios = [
        "PRIMAP-hist_v2.5_final_nr, HISTCR",
        "PRIMAP-hist_v2.5_final_nr, HISTTP",
        "PRIMAP-hist_v2.4.2_final_nr, HISTCR",
        "PRIMAP-hist_v2.4.2_final_nr, HISTTP",
        "CRF 2023, 230926",
        "CRF 2022, 230510",
        "EDGAR 7.0, HISTORY",
        "FAOSTAT 2022, HISTORY",
        "UNFCCC NAI, 231015",
    ]
    expected_graph_overview_items = []
    for k, v in plotting_config.source_scenario_settings.items():
        if k not in expected_graph_overview_source_scenarios:
            continue

        exp_line = [k]
        for info in ["color", "dash", "width"]:
            if info in v:
                exp_line.append(v[info])
            else:
                exp_line.append(None)

        expected_graph_overview_items.append(tuple(exp_line))

    figures_expected_items = (
        (
            "graph-overview",
            expected_graph_overview_items,
        ),
        (
            "graph-category-split",
            [
                ("total dashed", None, None, None),
                ("total", None, None, None),
                ("1 pos", None, None, None),
                ("2 pos", None, None, None),
                ("4 pos", None, None, None),
                ("5 pos", None, None, None),
                ("M.AG pos", None, None, None),
            ],
        ),
        (
            "graph-entity-split",
            [
                ("total dashed", None, None, None),
                ("total", None, None, None),
                ("CO2 pos", None, None, None),
            ],
        ),
    )
    for figure_id, expected_legend_items in figures_expected_items:
        figure = get_element_workaround(
            dash_duo=dash_duo, expected_id_component=figure_id, timeout=5
        )
        wait = WebDriverWait(dash_duo.driver, timeout=4)
        wait.until(lambda d: figure.find_elements(By.CLASS_NAME, "legend"))
        legend = figure.find_element(By.CLASS_NAME, "legend")
        traces = legend.find_elements(By.CLASS_NAME, "traces")
        legend_items = [trace.text for trace in traces]

        assert len(legend_items) == len(expected_legend_items)

        for i, (name, color, exp_dash, width) in enumerate(expected_legend_items):
            assert legend_items[i] == name
            # TODO right we just test name of traces in category in entity
            if all([color, exp_dash]):
                trace = traces[i]
                js_line = trace.find_element(By.CLASS_NAME, "js-line")
                style = js_line.get_attribute("style")
                assert f"stroke: {color}" in style

                if width is not None:
                    assert f"stroke-width: {width}px" in style

                if exp_dash == "solid":
                    assert "stroke-dasharray" not in style
                elif exp_dash == "dot":
                    assert "stroke-dasharray: 3px, 3px" in style
                else:
                    raise NotImplementedError(exp_dash)

    # Give time to sort out and shut down
    time.sleep(2)


def test_009_deselect_source_scenario_option(dash_duo):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    setup_app(dash_duo=dash_duo, ds=test_ds)
    time.sleep(2.0)
    figure_overview = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-overview", timeout=5
    )
    wait = WebDriverWait(dash_duo.driver, timeout=4)

    # find all traces in the plot
    scatter_layer = figure_overview.find_element(By.CLASS_NAME, "scatterlayer.mlayer")
    traces = scatter_layer.find_elements(By.TAG_NAME, "path")
    assert len(traces) == 9

    time.sleep(2)

    wait.until(lambda d: figure_overview.find_elements(By.CLASS_NAME, "legend"))
    legend = figure_overview.find_element(By.CLASS_NAME, "legend")
    traces = legend.find_elements(By.CLASS_NAME, "traces")
    for trace in traces:
        if trace.text != "EDGAR 7.0, HISTORY":
            continue

        toggles = trace.find_elements(By.CLASS_NAME, "legendtoggle")
        assert len(toggles) == 1
        toggle = toggles[0]
        toggle.click()

    time.sleep(2)

    # after clicking the legend toggle, one trace should disappear
    scatter_layer = figure_overview.find_element(By.CLASS_NAME, "scatterlayer.mlayer")
    traces = scatter_layer.find_elements(By.TAG_NAME, "path")
    assert len(traces) == 8

    # Click next
    button_category_next = dash_duo.driver.find_element(By.ID, "next_category")
    button_category_next.click()

    time.sleep(2)

    # find all traces in the plot
    # and make sure one is still invisible
    scatter_layer = figure_overview.find_element(By.CLASS_NAME, "scatterlayer.mlayer")
    traces = scatter_layer.find_elements(By.TAG_NAME, "path")
    assert len(traces) == 8


def test_010_category_buttons(dash_duo, tmp_path):
    test_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_file)

    tmp_db = tmp_path / "009_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)

    dash_duo.wait_for_contains_text("#dropdown-category", "M.0.EL")

    # Click next
    button_category_next = dash_duo.driver.find_element(By.ID, "next_category")
    button_category_next.click()

    # Category dropdown should update
    dash_duo.wait_for_contains_text("#dropdown-category", "M.AG")

    # Click previous
    button_category_prev = dash_duo.driver.find_element(By.ID, "prev_category")
    button_category_prev.click()

    # Category dropdown should update back to where it started
    dash_duo.wait_for_contains_text("#dropdown-category", "M.0.EL")

    # Give time to sort out and shut down
    time.sleep(2)


def test_011_entity_buttons(dash_duo):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    setup_app(dash_duo=dash_duo, ds=test_ds)

    dash_duo.wait_for_contains_text("#dropdown-entity", "CO2")

    # Click previous
    button_entity_prev = dash_duo.driver.find_element(By.ID, "prev_entity")
    button_entity_prev.click()

    # Entity dropdown should update
    dash_duo.wait_for_contains_text("#dropdown-entity", "CH4")

    # Click next
    button_entity_next = dash_duo.driver.find_element(By.ID, "next_entity")
    button_entity_next.click()

    # Entity dropdown should update back to where it started
    dash_duo.wait_for_contains_text("#dropdown-entity", "CO2")

    # Give time to sort out and shut down
    time.sleep(2)


def test_012_dropdown_source_scenario(dash_duo):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    setup_app(dash_duo=dash_duo, ds=test_ds)

    dash_duo.wait_for_contains_text(
        "#dropdown-source-scenario",
        "PRIMAP-hist_v2.5_final_nr, HISTCR",
    )

    # Give time to sort out and shut down
    time.sleep(2)


def test_013_dropdown_source_scenario_option_not_available(dash_duo):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    setup_app(dash_duo=dash_duo, ds=test_ds)
    # Give time to set up
    time.sleep(2)

    # Re-size the window to ensure the drop-down
    # and the clear buttons don't overlap.
    dash_duo.driver.set_window_size(2000, 1500)

    dropdown_source_scenario_div = dash_duo.driver.find_element(
        By.ID, "dropdown-source-scenario"
    )

    # Find the arrow that expands the dropdown options and click on it
    dropdown_source_scenario_div.find_element(
        # By.CLASS_NAME, "Select-arrow-zone"
        By.CLASS_NAME,
        "Select-arrow",
    ).click()

    # simulate keyboard
    action = ActionChains(dash_duo.driver)
    action.send_keys(Keys.ARROW_DOWN)
    action.send_keys(Keys.ARROW_DOWN)
    action.send_keys(Keys.ENTER)
    action.perform()

    dash_duo.wait_for_contains_text(
        "#dropdown-source-scenario",
        "UNFCCC NAI, 231015",
    )

    # Click next country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    dash_duo.wait_for_contains_text(
        "#dropdown-source-scenario",
        "PRIMAP-hist_v2.4.2_final_nr, HISTCR",
    )

    # Give time to sort out and shut down
    time.sleep(2)


def get_dropdown_value(
    dropdown_element: selenium.webdriver.remote.webelement.WebElement,
) -> str:
    """
    Dropdowns contain a clear element too, hence this isn't trivial

    Probably not the best way to do this, but also easier than
    always referring to 'react-select-x--value-item' IDs.
    """
    return dropdown_element.text.splitlines()[0]


def test_015_notes_save_basic(dash_duo, tmp_path):
    time.sleep(2)
    test_ds_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "014_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)

    # Add some input
    input_for_first_country = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(input_for_first_country)

    # Re-size the window to ensure buttons don't overlap.
    # Will be fixed once we update the layout.
    dash_duo.driver.set_window_size(2000, 1500)

    # Make sure database save operation has finished and been confirmed to the user
    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    current_country = get_dropdown_value(dropdown_country)
    current_country_iso3 = name_to_iso3(current_country)
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {current_country} saved", timeout=2
    )
    # Output should now be in the database
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert (
        db.set_index("country_iso3")["notes"].loc[current_country_iso3]
        == input_for_first_country
    )
    # and user should be notified with path in which data is saved too
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert re.match(
        rf"Notes for {current_country} saved at .* in {tmp_db}", note_saved_div.text
    )

    # Click forward until Ecuador to make sure the iso3 country code is saved in the DB
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()
    button_country_next.click()

    time.sleep(2)

    # Add some input
    input_for_second_country = "All looks great again!"
    input_for_notes.send_keys(input_for_second_country)

    time.sleep(2)

    # Make sure database save operation has finished and been confirmed to the user
    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    current_country = get_dropdown_value(dropdown_country)
    current_country_iso3 = name_to_iso3(current_country)
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {current_country} saved", timeout=2
    )

    # Output should now be in the database
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 2
    assert (
        db.set_index("country_iso3")["notes"].loc[current_country_iso3]
        == input_for_second_country
    )

    # Give time to sort out and shut down
    time.sleep(2)


def test_016_notes_save_and_step(dash_duo, tmp_path):
    test_ds_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "016_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.driver.set_window_size(2000, 1500)

    # Add some input
    note_to_save = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(note_to_save)

    # Make sure database save operation has finished and been confirmed to the user
    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    current_country = get_dropdown_value(dropdown_country)
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {current_country} saved", timeout=2
    )

    # Click forward one country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # Output should be in the database too
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert (
        db.set_index("country_iso3")["notes"].loc[name_to_iso3(current_country)]
        == note_to_save
    )

    # Click back one country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # The previous note should be reloaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    current_country = get_dropdown_value(dropdown_country)

    # give time to update save notification
    time.sleep(2)
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert note_saved_div.text == f"Loaded existing notes for {current_country}"

    # Give time to sort out and shut down
    time.sleep(2)


def test_017_notes_step_without_user_save(dash_duo, tmp_path):
    test_ds_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "016_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.driver.set_window_size(2000, 1500)

    # Add some input
    note_to_save = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(note_to_save)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    country_before_click = get_dropdown_value(dropdown_country)

    # Click forward one country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # The note was saved automatically
    # and the inputs should be cleared.
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    assert not input_for_notes.text
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    # The notification is empty
    assert re.match(
        "",
        note_saved_div.text,
    )

    # Output should be in the database too
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert (
        db.set_index("country_iso3")["notes"].loc[name_to_iso3(country_before_click)]
        == note_to_save
    )

    # Click back one country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # The previous note should be reloaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    current_country = get_dropdown_value(dropdown_country)
    assert note_saved_div.text == f"Loaded existing notes for {current_country}"

    # Give time to sort out and shut down
    time.sleep(2)


def test_018_notes_step_without_input_is_quiet(dash_duo, tmp_path):
    test_ds_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "017_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.driver.set_window_size(2000, 1500)

    # Click forward without any input
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # Should get no input or messages
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    assert not input_for_notes.text
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert not note_saved_div.text

    # Add some input
    note_to_save = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(note_to_save)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    country_with_notes = get_dropdown_value(dropdown_country)

    # Click forward one country
    button_country_next.click()

    # We saved before clicking, hence inputs should be cleared
    # and a confirmation shown.
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    assert not input_for_notes.text

    # Output should be in the database too
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert (
        db.set_index("country_iso3")["notes"].loc[name_to_iso3(country_with_notes)]
        == note_to_save
    )

    # Click back one country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # The previous note should be reloaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    assert input_for_notes.text == note_to_save
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    # time.sleep(2)
    assert note_saved_div.text == f"Loaded existing notes for {country_with_notes}"

    # Give time to sort out and shut down
    time.sleep(2)


def test_019_notes_load_from_dropdown_selection(dash_duo, tmp_path):
    test_ds_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "018_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.driver.set_window_size(2000, 1500)
    # Give time to set up
    time.sleep(2)

    # Go to a country
    dropdown_country_input = dash_duo.find_element("#dropdown-country input")
    country_with_notes = "Egypt"
    dropdown_country_input.send_keys(country_with_notes)
    dropdown_country_input.send_keys(Keys.ENTER)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    assert get_dropdown_value(dropdown_country) == country_with_notes

    # Save a note
    note_to_save = f"Note for {country_with_notes}"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(note_to_save)
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)

    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {country_with_notes} saved at", timeout=2
    )

    # Go to a different country via the buttons
    dash_duo.multiple_click("#next_country", 15, delay=0.05)
    time.sleep(1.0)
    assert get_dropdown_value(dropdown_country) != country_with_notes

    # Go back to the first country via the dropdown menu
    dropdown_country_input.send_keys(country_with_notes)
    dropdown_country_input.send_keys(Keys.ENTER)

    # Check that notes were loaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Loaded existing notes for {country_with_notes}", timeout=2
    )

    # Give time to sort out and shut down
    time.sleep(2)


def test_020_notes_multi_step_flow(dash_duo, tmp_path):
    test_ds_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "019_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.driver.set_window_size(2000, 1500)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    first_country = get_dropdown_value(dropdown_country)

    # Add some input for our first country
    input_for_first_country = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(input_for_first_country)
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_first_country, timeout=2
    )

    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {first_country} saved at", timeout=2
    )

    # Click forward a country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    time.sleep(1)
    button_country_next.click()

    # Make sure input field has finished updating
    dash_duo.wait_for_text_to_equal("#input-for-notes", "")

    second_country = get_dropdown_value(dropdown_country)
    assert second_country != first_country

    # Add input
    input_for_second_country = "Not so good"
    input_for_notes.send_keys(input_for_second_country)
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_second_country, timeout=2
    )
    time.sleep(1)

    # Make sure database has finished before checking
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {second_country} saved", timeout=2
    )

    # Both outputs should now be in the database
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 2
    assert (
        db.set_index("country_iso3")["notes"].loc[name_to_iso3(first_country)]
        == input_for_first_country
    )
    assert (
        db.set_index("country_iso3")["notes"].loc[name_to_iso3(second_country)]
        == input_for_second_country
    )

    # Click back to starting country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    time.sleep(1)
    button_country_previous.click()

    # Previous input should reappear
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_first_country, timeout=2
    )
    assert input_for_notes.text == input_for_first_country
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert note_saved_div.text == (f"Loaded existing notes for {first_country}")

    # Click back one more country
    time.sleep(1)
    button_country_previous.click()

    # Input field should be empty again
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    assert not input_for_notes.text

    # Click forward two countries
    time.sleep(1)
    dash_duo.multiple_click("#next_country", 2, delay=0.01)

    # Previous input should reappear
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_second_country, timeout=2
    )
    assert input_for_notes.text == input_for_second_country
    # Depending on how fast you click, the note about EARTH already
    # being saved may or may not appear, so don't check that here.
    assert f"Loaded existing notes for {second_country}" in note_saved_div.text

    # Give time to sort out and shut down
    time.sleep(2)


def test_021_auto_save_and_load_existing(dash_duo, tmp_path):
    """
    Test behaviour if changing country triggers both auto-saving and loading of an existing note
    """
    test_ds_file = TEST_DS_FILE
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "020_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.driver.set_window_size(2000, 1500)
    # Give time to set up
    time.sleep(2)

    # Go to a country
    dropdown_country_input = dash_duo.find_element("#dropdown-country input")
    country_with_notes = "Jordan"
    dropdown_country_input.send_keys(country_with_notes)
    dropdown_country_input.send_keys(Keys.ENTER)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    first_country = get_dropdown_value(dropdown_country)

    # Add some input for our first country
    input_for_first_country = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(input_for_first_country)
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_first_country, timeout=2
    )

    # Click forward a country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    second_country = get_dropdown_value(dropdown_country)
    assert second_country != first_country

    # Add input
    input_for_second_country = "Not so good"
    input_for_notes.send_keys(input_for_second_country)
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_second_country, timeout=2
    )

    # Click back to the previous country without saving
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # Check note loaded into notes input field
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_first_country, timeout=2
    )
    # Check information provided to the user
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert re.match(
        "",
        note_saved_div.text,
    )

    # Check that both notes are in the database
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 2
    assert (
        db.set_index("country_iso3")["notes"].loc[name_to_iso3(first_country)]
        == input_for_first_country
    )
    assert (
        db.set_index("country_iso3")["notes"].loc[name_to_iso3(second_country)]
        == input_for_second_country
    )

    # Give time to sort out and shut down
    time.sleep(2)


def get_xtick_values(graph):
    return [
        v.text
        for v in graph.find_elements_by_class_name("xaxislayer-above")[
            0
        ].find_elements_by_class_name("xtick")
    ]


def get_ytick_values(graph):
    return [
        v.text
        for v in graph.find_elements_by_class_name("yaxislayer-above")[
            0
        ].find_elements_by_class_name("ytick")
    ]


def assert_graph_ticks_equal(
    graphs,
    xticks_expected: Iterable[list[str], ...] | None = None,
    yticks_expected: Iterable[list[str], ...] | None = None,
):
    """
    Assert that the graph ticks equal what we expect

    `xticks_expected`/`yticks_expected`
    should provide the expected ticks for each graph in `graphs`.

    This appears to be sensitive to window size,
    which is quite annoying.
    Not sure how to fix.
    """
    if not xticks_expected and not yticks_expected:
        msg = "Function won't do anything"
        raise AssertionError(msg)

    for i, graph in enumerate(graphs):
        if xticks_expected is not None:
            xticks_expected_graph = xticks_expected[i]
            actual_xticks = get_xtick_values(graph)
            assert xticks_expected_graph == actual_xticks

        if yticks_expected is not None:
            yticks_expected_graph = yticks_expected[i]
            actual_yticks = get_ytick_values(graph)
            assert yticks_expected_graph == actual_yticks


def assert_graph_ticks_not_equal(
    graphs,
    xticks_compare: Iterable[list[str], ...] | None = None,
    yticks_compare: Iterable[list[str], ...] | None = None,
):
    """
    Assert that the graph ticks are not equal to some value, e.g. have changed

    `xticks_expected`/`yticks_expected`
    should provide the expected ticks for each graph in `graphs`.

    This appears to be sensitive to window size,
    which is quite annoying.
    Not sure how to fix.
    """
    if not xticks_compare and not yticks_compare:
        msg = "Function won't do anything"
        raise AssertionError(msg)

    for i, graph in enumerate(graphs):
        if xticks_compare is not None:
            xticks_expected_graph = xticks_compare[i]
            actual_xticks = get_xtick_values(graph)
            assert xticks_expected_graph != actual_xticks

        if yticks_compare is not None:
            yticks_expected_graph = yticks_compare[i]
            actual_yticks = get_ytick_values(graph)
            assert yticks_expected_graph != actual_yticks


def assert_ticks_consistent_across_graphs(
    graphs,
    check_xticks=True,
    check_yticks=True,
):
    """
    Assert that the ticks are consistent across all our graphs
    """
    if not check_xticks and not check_yticks:
        msg = "Function won't do anything"
        raise AssertionError(msg)

    for i, graph in enumerate(graphs):
        if i == 0:
            exp_xticks = get_xtick_values(graph)
            exp_yticks = get_ytick_values(graph)
        else:
            if check_xticks:
                # This appears to be sensitive to window size,
                # which is quite annoying.
                # Not sure how to fix.
                actual_xticks = get_xtick_values(graph)
                assert exp_xticks == actual_xticks

            if check_yticks:
                actual_yticks = get_ytick_values(graph)
                assert exp_yticks == actual_yticks


def test_022_linked_zoom(dash_duo, tmp_path):
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    tmp_db = tmp_path / "021_notes_database.db"

    dash_duo = setup_app(dash_duo=dash_duo, ds=test_ds, db_path=tmp_db)
    # Give time to set up
    time.sleep(2)

    # Make sure that expected elements are on the page before continuing
    graph_overview = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-overview", timeout=5
    )
    graph_entity_split = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-entity-split", timeout=5
    )
    graph_category_split = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-category-split", timeout=5
    )

    # Re-size the window.
    # This ensures consistent behaviour of the ticks.
    # A much nicer way to handle this would be to get the actual Python objects
    # that correspond to the app's state, then just check them directly.
    # However, I can't work out how to do that right now, so I'm using this hack instead.
    dash_duo.driver.set_window_size(1412, 1000)
    # Give time to respond to new size
    time.sleep(1)

    graphs = [graph_overview, graph_category_split, graph_entity_split]

    # Can't see a better way to do this, maybe someone else finds it.
    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Zoom in via entity graph
    dash_duo.zoom_in_graph_by_ratio(graph_entity_split, zoom_box_fraction=0.2)
    time.sleep(1.0)

    # Limits of all graphs should update
    assert_ticks_consistent_across_graphs(
        graphs=graphs,
        check_xticks=True,
        check_yticks=True,
    )
    assert_graph_ticks_not_equal(
        graphs, xticks_compare=graphs_xticks_prev, yticks_compare=graphs_yticks_prev
    )

    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Reset via entity graph
    ActionChains(dash_duo.driver).double_click(graph_entity_split).perform()
    time.sleep(1.0)

    # Limits of all graphs should update
    assert_ticks_consistent_across_graphs(
        graphs=graphs,
        check_xticks=True,
        check_yticks=True,
    )
    assert_graph_ticks_not_equal(
        graphs, xticks_compare=graphs_xticks_prev, yticks_compare=graphs_yticks_prev
    )

    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Zoom in via category graph
    dash_duo.zoom_in_graph_by_ratio(graph_category_split, zoom_box_fraction=0.1)
    time.sleep(1.0)

    # Limits of all graphs should update
    assert_ticks_consistent_across_graphs(
        graphs=graphs,
        check_xticks=True,
        check_yticks=True,
    )
    assert_graph_ticks_not_equal(
        graphs, xticks_compare=graphs_xticks_prev, yticks_compare=graphs_yticks_prev
    )

    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Reset via category graph
    ActionChains(dash_duo.driver).double_click(graph_category_split).perform()
    time.sleep(1.0)

    # Limits of all graphs should update
    assert_ticks_consistent_across_graphs(
        graphs=graphs,
        check_xticks=True,
        check_yticks=True,
    )
    assert_graph_ticks_not_equal(
        graphs, xticks_compare=graphs_xticks_prev, yticks_compare=graphs_yticks_prev
    )

    # Check overview graph last because its zoom only affects the x-axis.
    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Zoom in on overview graph
    dash_duo.zoom_in_graph_by_ratio(graph_overview, zoom_box_fraction=0.2)

    assert_ticks_consistent_across_graphs(
        graphs=graphs,
        check_xticks=True,
        check_yticks=True,
    )
    assert_graph_ticks_not_equal(graphs, xticks_compare=graphs_xticks_prev)
    assert_graph_ticks_equal(graphs, yticks_expected=graphs_yticks_prev)

    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Reset via overview graph
    ActionChains(dash_duo.driver).double_click(graph_overview).perform()
    time.sleep(1.0)

    assert_ticks_consistent_across_graphs(
        graphs=graphs,
        check_xticks=True,
        check_yticks=True,
    )
    assert_graph_ticks_not_equal(graphs, xticks_compare=graphs_xticks_prev)
    assert_graph_ticks_equal(graphs, yticks_expected=graphs_yticks_prev)


def test_022_zoom_country_dropdown_change(dash_duo, tmp_path):  # noqa: PLR0915
    """
    Test the behaviour of the zoom's reset as we cycle through countries
    """
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    tmp_db = tmp_path / "022_notes_database.db"

    dash_duo = setup_app(dash_duo=dash_duo, ds=test_ds, db_path=tmp_db)
    # Give time to set up
    time.sleep(2)

    # Make sure that expected elements are on the page before continuing
    graph_overview = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-overview", timeout=5
    )
    graph_entity_split = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-entity-split", timeout=5
    )
    graph_category_split = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-category-split", timeout=5
    )
    graphs = [graph_overview, graph_category_split, graph_entity_split]

    # Click to next country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()
    # Give a second to sort itself out
    time.sleep(1)

    # Re-size the window.
    # This ensures consistent behaviour of the ticks.
    # A much nicer way to handle this would be to get the actual Python objects
    # that correspond to the app's state, then just check them directly.
    # However, I can't work out how to do that right now, so I'm using this hack instead.
    dash_duo.driver.set_window_size(1400, 948)
    # Give time to respond to new size
    time.sleep(1)

    # Zoom in on overview graph
    dash_duo.zoom_in_graph_by_ratio(graph_overview, zoom_box_fraction=0.2)

    xticks_prev = get_xtick_values(graph_overview)
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Click to next country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()
    # Give a second to sort itself out
    time.sleep(1)

    # Re-size the window
    # This seems to make the ticks behave for some reason
    dash_duo.driver.set_window_size(1200, 948)
    # Give a second to sort itself out
    time.sleep(0.5)

    dash_duo.driver.set_window_size(1400, 948)
    # Give a second to sort itself out
    time.sleep(0.5)

    # x-tick values of all plots should be unchanged.
    assert_graph_ticks_equal(graphs, xticks_expected=[xticks_prev for _ in graphs])
    # y-ticks should have changed.
    assert_graph_ticks_not_equal(graphs, yticks_compare=graphs_yticks_prev)

    # If we zoom in using the overview graph's range zoom,
    # the x-axis limits should change, but the y-axis limits shouldn't.
    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    dash_duo.zoom_in_graph_by_ratio(graph_overview, zoom_box_fraction=0.2)
    # Give a second to sort itself out
    time.sleep(0.5)

    # x-tick values of all plots should change
    assert_graph_ticks_not_equal(graphs, xticks_compare=graphs_xticks_prev)
    # y-ticks should not have changed.
    assert_graph_ticks_equal(graphs, yticks_expected=graphs_yticks_prev)

    # Zoom in via entity graph.
    # This has the side-effect of locking the y-axis zoom too.
    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    dash_duo.zoom_in_graph_by_ratio(graph_entity_split, zoom_box_fraction=0.2)
    # Give a second to sort itself out
    time.sleep(0.5)

    assert_graph_ticks_not_equal(
        graphs, xticks_compare=graphs_xticks_prev, yticks_compare=graphs_yticks_prev
    )
    assert_ticks_consistent_across_graphs(
        graphs=graphs,
        check_xticks=True,
        check_yticks=True,
    )

    # Click to next country.
    # This has the side-effect of unlocking the y-axis zoom.
    graphs_xticks_prev = [get_xtick_values(graph) for graph in graphs]
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()
    # Give a second to sort itself out
    time.sleep(1)

    # Re-size the window
    # This seems to make the ticks behave for some reason
    dash_duo.driver.set_window_size(1200, 948)
    # Give a second to sort itself out
    time.sleep(0.5)

    dash_duo.driver.set_window_size(1400, 948)
    # Give a second to sort itself out
    time.sleep(0.5)

    # x-tick values of all plots should be unchanged,
    # but y-tick values should update
    # because changing country causes the y-axis
    # limit to reset.
    assert_graph_ticks_equal(graphs, xticks_expected=graphs_xticks_prev)
    assert_graph_ticks_not_equal(graphs, yticks_compare=graphs_yticks_prev)


@pytest.mark.parametrize(
    "source_scenario_element_to_alter",
    (
        "dropdown-source-scenario",
        "dropdown-source-scenario-dashed",
    ),
)
def test_023_zoom_source_scenario_dropdown_change(
    dash_duo, tmp_path, source_scenario_element_to_alter
):
    """
    Test the behaviour of the zoom's reset as we cycle through source-scenarios
    """
    test_file = TEST_DS_FILE

    test_ds = pm.open_dataset(test_file)

    tmp_db = tmp_path / "023_notes_database.db"

    dash_duo = setup_app(dash_duo=dash_duo, ds=test_ds, db_path=tmp_db)
    # Give time to set up
    time.sleep(2)

    # Make sure that expected elements are on the page before continuing
    graph_overview = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-overview", timeout=5
    )
    graph_entity_split = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-entity-split", timeout=5
    )
    graph_category_split = get_element_workaround(
        dash_duo=dash_duo, expected_id_component="graph-category-split", timeout=5
    )
    graphs = [graph_overview, graph_category_split, graph_entity_split]

    # Re-size the window.
    # This ensures consistent behaviour of the ticks.
    # A much nicer way to handle this would be to get the actual Python objects
    # that correspond to the app's state, then just check them directly.
    # However, I can't work out how to do that right now, so I'm using this hack instead.
    dash_duo.driver.set_window_size(1400, 948)
    # Give time to respond to new size
    time.sleep(1)

    # Zoom in on category graph
    dash_duo.zoom_in_graph_by_ratio(graph_category_split, zoom_box_fraction=0.2)
    # Give a second to sort itself out
    time.sleep(1)

    xticks_prev = get_xtick_values(graph_overview)
    graphs_yticks_prev = [get_ytick_values(graph) for graph in graphs]

    # Alter the dropdown
    dropdown_source_scenario_div = dash_duo.driver.find_element(
        By.ID, source_scenario_element_to_alter
    )

    # Find the arrow that expands the dropdown options and click on it
    dropdown_source_scenario_div.find_element(
        By.CLASS_NAME, "Select-arrow-zone"
    ).click()

    # simulate keyboard
    action = ActionChains(dash_duo.driver)
    action.send_keys(Keys.ARROW_DOWN)
    action.send_keys(Keys.ARROW_DOWN)
    action.send_keys(Keys.ENTER)
    action.perform()
    time.sleep(0.3)

    dash_duo.wait_for_contains_text(
        f"#{source_scenario_element_to_alter}",
        "UNFCCC NAI, 231015",
    )

    # x-tick and y-tick values of all plots should be unchanged.
    assert_graph_ticks_equal(
        graphs,
        xticks_expected=[xticks_prev for _ in graphs],
        yticks_expected=graphs_yticks_prev,
    )
