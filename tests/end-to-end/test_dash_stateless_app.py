"""
End to end testing of an app that doesn't use global state
"""
import re
from pathlib import Path

import dash
import dash.testing
import primap2 as pm
import selenium.webdriver.remote.webelement
import xarray as xr
from dash import html
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait

import primap_visualisation_tool_stateless_app
import primap_visualisation_tool_stateless_app.callbacks
import primap_visualisation_tool_stateless_app.dataset_holder
import primap_visualisation_tool_stateless_app.notes


def test_001_dash_example(dash_duo):
    # A test that the dash example runs.
    # If this breaks things are really broken - i.e. there is an issue beyond our code.
    app = dash.Dash(__name__)
    app.layout = html.Div(id="nully-wrapper", children=0)
    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("#nully-wrapper", "0", timeout=4)
    assert dash_duo.find_element("#nully-wrapper").text == "0"


def test_002_app_starts(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)


def test_003_dropdown_country(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    dropdown_country_select_element = dropdown_country.find_element(
        By.ID, "react-select-2--value-item"
    )
    assert dropdown_country_select_element.text == "EARTH"


def test_004_dropdown_country_earth_not_present(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)
    test_ds = test_ds.pr.loc[{"area (ISO3)": ["AUT", "AUS"]}]

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    assert (
        dropdown_country.find_element(By.ID, "react-select-2--value-item").text
        == "Australia"
    )


def test_005_dropdown_category(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    dropdown_category = dash_duo.driver.find_element(By.ID, "dropdown-category")
    assert (
        dropdown_category.find_element(By.ID, "react-select-3--value-item").text
        == "M.0.EL"
    )


def test_006_dropdown_entity(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    dropdown_entity = dash_duo.driver.find_element(By.ID, "dropdown-entity")
    assert (
        dropdown_entity.find_element(By.ID, "react-select-4--value-item").text == "CO2"
    )


def test_007_country_buttons(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    dash_duo.wait_for_element_by_id("next_country", timeout=2)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    dropdown_country_select_element = dropdown_country.find_element(
        By.ID, "react-select-2--value-item"
    )
    assert dropdown_country_select_element.text == "EARTH"

    # Click next
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # Country dropdown should update
    assert dropdown_country_select_element.text == "EU27BX"

    # Click previous
    button_country_prev = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_prev.click()

    # Country dropdown should be back to where it started
    assert dropdown_country_select_element.text == "EARTH"


def test_008_initial_figures(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    figures_expected_items = (
        (
            "graph-overview",
            [
                ("PRIMAP-hist_v2.5_final_nr, HISTCR", "rgb(0, 0, 0)", "solid", 3),
                ("PRIMAP-hist_v2.5_final_nr, HISTTP", "rgb(166, 166, 166)", "solid", 3),
                ("PRIMAP-hist_v2.4.2_final_nr, HISTCR", "rgb(0, 0, 0)", "dot", 3),
                ("PRIMAP-hist_v2.4.2_final_nr, HISTTP", "rgb(166, 166, 166)", "dot", 3),
                ("CRF 2022, 230510", "rgb(60, 179, 113)", "solid", None),
                ("CRF 2023, 230926", "rgb(238, 130, 238)", "solid", None),
                ("EDGAR 7.0, HISTORY", "rgb(255, 165, 0)", "solid", None),
                ("FAOSTAT 2022, HISTORY", "rgb(100, 0, 255)", "solid", None),
                ("UNFCCC NAI, 231015", "rgb(255, 0, 0)", "solid", None),
            ],
        ),
        # (
        #     "graph-category-split",
        #     [
        #         "total",
        #         "1 pos",
        #         "2 pos",
        #         "4 pos",
        #         "5 pos",
        #         "M.AG pos",
        #     ],
        # ),
        # (
        #     "graph-entity-split",
        #     [
        #         "total",
        #         "CH4 (AR6GWP100) pos",
        #         "CO2 (AR6GWP100) pos",
        #         "N2O (AR6GWP100) pos",
        #         "FGASES (AR6GWP100) pos",
        #     ],
        # ),
    )
    for figure_id, expected_legend_items in figures_expected_items:
        figure = dash_duo.driver.find_element(By.ID, figure_id)
        wait = WebDriverWait(dash_duo.driver, timeout=5)
        wait.until(lambda d: figure.find_elements(By.CLASS_NAME, "legend"))
        legend = figure.find_element(By.CLASS_NAME, "legend")
        traces = legend.find_elements(By.CLASS_NAME, "traces")
        legend_items = [trace.text for trace in traces]

        assert len(legend_items) == len(expected_legend_items)

        for i, (name, color, exp_dash, width) in enumerate(expected_legend_items):
            assert legend_items[i] == name
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


def test_009_category_buttons(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    dropdown_category = dash_duo.driver.find_element(By.ID, "dropdown-category")
    dropdown_category_select_element = dropdown_category.find_element(
        By.ID, "react-select-3--value-item"
    )
    assert dropdown_category_select_element.text == "M.0.EL"

    # Click next
    button_category_next = dash_duo.driver.find_element(By.ID, "next_category")
    button_category_next.click()

    # Country dropdown should update
    assert dropdown_category_select_element.text == "M.AG"

    # Click previous
    button_category_prev = dash_duo.driver.find_element(By.ID, "prev_category")
    button_category_prev.click()

    # Country dropdown should update back to where it started
    assert dropdown_category_select_element.text == "M.0.EL"


def test_010_entity_buttons(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(
        test_ds
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    dropdown_entity = dash_duo.driver.find_element(By.ID, "dropdown-entity")
    dropdown_entity_select_element = dropdown_entity.find_element(
        By.ID, "react-select-4--value-item"
    )
    assert dropdown_entity_select_element.text == "CO2"

    # Click previous
    button_entity_prev = dash_duo.driver.find_element(By.ID, "prev_entity")
    button_entity_prev.click()

    # Entity dropdown should update
    dash_duo.wait_for_text_to_equal("#react-select-4--value-item", "CH4", timeout=2)

    # Click next
    button_entity_next = dash_duo.driver.find_element(By.ID, "next_entity")
    button_entity_next.click()

    # Entity dropdown should update back to where it started
    dash_duo.wait_for_text_to_equal("#react-select-4--value-item", "CO2", timeout=2)


# TODO: re-use this in other tests too
def setup_app(
    dash_duo, ds: xr.Dataset, db_path: Path
) -> dash.testing.composite.DashComposite:
    """
    Setup the app
    """
    primap_visualisation_tool_stateless_app.dataset_holder.set_application_dataset(ds)
    primap_visualisation_tool_stateless_app.notes.set_application_notes_db_filepath(
        db_path
    )

    app = primap_visualisation_tool_stateless_app.create_app()
    primap_visualisation_tool_stateless_app.callbacks.register_callbacks(app)
    dash_duo.start_server(app)

    return dash_duo


def get_dropdown_value(
    dropdown_element: selenium.webdriver.remote.webelement.WebElement,
) -> str:
    """
    Dropdowns contain a clear element too, hence this isn't trivial
    """
    return dropdown_element.text.splitlines()[0]


def test_012_notes_save_no_input(dash_duo, tmp_path):
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "012_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

    # Click without anything in the field
    save_button = dash_duo.driver.find_element(By.ID, "save-button")
    save_button.click()

    # Should get no output
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert not note_saved_div.text


def test_013_notes_save_basic(dash_duo, tmp_path):
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "013_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

    # Add some input
    input_for_first_country = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(input_for_first_country)

    # Save
    save_button = dash_duo.driver.find_element(By.ID, "save-button")
    save_button.click()

    # Make sure database save operation has finished and been confirmed to the user
    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    current_country = get_dropdown_value(dropdown_country)
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {current_country} saved", timeout=2
    )
    # Output should now be in the database
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert (
        db.set_index("country")["notes"].loc[current_country] == input_for_first_country
    )
    # and user should be notified with path in which data is saved too
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert re.match(
        rf"Notes for {current_country} saved at .* in {tmp_db}", note_saved_div.text
    )


def test_014_notes_save_and_step(dash_duo, tmp_path):
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "014_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

    # Add some input
    note_to_save = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(note_to_save)

    # Save
    save_button = dash_duo.driver.find_element(By.ID, "save-button")
    save_button.click()

    # Make sure database save operation has finished and been confirmed to the user
    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    current_country = get_dropdown_value(dropdown_country)
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {current_country} saved", timeout=2
    )

    # Click forward one country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # We saved before clicking, hence inputs should be cleared and a confirmation shown
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    assert not input_for_notes.text
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert note_saved_div.text == f"Notes for {current_country} already saved"

    # Output should be in the database too
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert db.set_index("country")["notes"].loc[current_country] == note_to_save

    # Click back one country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # The previous note should be reloaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    current_country = get_dropdown_value(dropdown_country)
    assert note_saved_div.text == f"Loaded existing notes for {current_country}"


def test_015_notes_step_without_user_save(dash_duo, tmp_path):
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "015_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

    # Add some input
    note_to_save = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(note_to_save)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    country_before_click = get_dropdown_value(dropdown_country)

    # Click forward one country without saving
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # We saved without clicking,
    # hence a warming should appear,
    # the note should be saved automatically
    # and the inputs should be cleared.
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    assert not input_for_notes.text
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert re.match(
        f"WARNING: notes for {country_before_click} weren't saved before changing country, "
        "we have saved the notes for you. "
        rf"Notes for {country_before_click} saved at .* in {tmp_db}",
        note_saved_div.text,
    )

    # Output should be in the database too
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert db.set_index("country")["notes"].loc[country_before_click] == note_to_save

    # Click back one country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # The previous note should be reloaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    current_country = get_dropdown_value(dropdown_country)
    assert note_saved_div.text == f"Loaded existing notes for {current_country}"


def test_016_notes_step_without_input_is_quiet(dash_duo, tmp_path):
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "016_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

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

    # Save
    save_button = dash_duo.driver.find_element(By.ID, "save-button")
    save_button.click()

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    country_with_notes = get_dropdown_value(dropdown_country)

    # Click forward one country
    button_country_next.click()

    # We saved before clicking, hence inputs should be cleared
    # and a confirmation shown.
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    assert not input_for_notes.text
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert note_saved_div.text == f"Notes for {country_with_notes} already saved"

    # Output should be in the database too
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 1
    assert db.set_index("country")["notes"].loc[country_with_notes] == note_to_save

    # Click back one country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # The previous note should be reloaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    assert input_for_notes.text == note_to_save
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    assert note_saved_div.text == f"Loaded existing notes for {country_with_notes}"


def test_017_notes_load_from_dropdown_selection(dash_duo, tmp_path):
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "017_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

    # Go to a country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    for _ in range(5):
        button_country_next.click()

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    country_with_notes = get_dropdown_value(dropdown_country)

    # Save a note
    note_to_save = f"Note for {country_with_notes}"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(note_to_save)
    save_button = dash_duo.driver.find_element(By.ID, "save-button")
    save_button.click()
    dash_duo.wait_for_contains_text(
        "#note-saved-div", f"Notes for {country_with_notes} saved", timeout=2
    )

    # Go to a different country
    for _ in range(15):
        button_country_next.click()

    # Go back to the first country via the dropdown menu
    dropdown_country_input = dash_duo.find_element("#dropdown-country input")
    dropdown_country_input.send_keys(country_with_notes)
    dropdown_country_input.send_keys(Keys.ENTER)

    # Check that notes were loaded
    dash_duo.wait_for_text_to_equal("#input-for-notes", note_to_save, timeout=2)
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert note_saved_div.text == f"Loaded existing notes for {country_with_notes}"


def test_018_notes_multi_step_flow(dash_duo, tmp_path):
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "018_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    first_country = get_dropdown_value(dropdown_country)

    # Add some input for our first country
    input_for_first_country = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(input_for_first_country)

    # Save
    save_button = dash_duo.driver.find_element(By.ID, "save-button")
    save_button.click()

    # Click forward a few countries
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()
    second_country = get_dropdown_value(dropdown_country)

    # Add input
    input_for_second_country = "Not so good"
    input_for_notes.send_keys(input_for_second_country)

    # Save
    save_button.click()

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
        db.set_index("country")["notes"].loc[first_country] == input_for_first_country
    )
    assert (
        db.set_index("country")["notes"].loc[second_country] == input_for_second_country
    )

    # Click back to starting country
    button_country_previous = dash_duo.driver.find_element(By.ID, "prev_country")
    button_country_previous.click()

    # Previous input should reappear
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_first_country, timeout=2
    )
    assert input_for_notes.text == input_for_first_country
    note_saved_div = dash_duo.driver.find_element(By.ID, "note-saved-div")
    assert note_saved_div.text == (
        f"Notes for {second_country} already saved. "
        f"Loaded existing notes for {first_country}"
    )

    # Click back one more country
    button_country_previous.click()

    # Input field should be empty again
    dash_duo.wait_for_text_to_equal("#input-for-notes", "", timeout=2)
    assert not input_for_notes.text
    dash_duo.wait_for_text_to_equal(
        "#note-saved-div", f"Notes for {first_country} already saved", timeout=2
    )

    # Click forward two countries
    button_country_next.click()
    button_country_next.click()

    # Previous input should reappear
    dash_duo.wait_for_text_to_equal(
        "#input-for-notes", input_for_second_country, timeout=2
    )
    assert input_for_notes.text == input_for_second_country
    # Depending on how fast you click, the note about EARTH already
    # being saved may or may not appear, so don't check that here.
    assert f"Loaded existing notes for {second_country}" in note_saved_div.text


def test_019_auto_save_and_load_existing(dash_duo, tmp_path):
    """
    Test behaviour if changing country triggers both auto-saving and loading of an existing note
    """
    test_ds_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    test_ds = pm.open_dataset(test_ds_file)

    tmp_db = tmp_path / "019_notes_database.db"

    dash_duo = setup_app(dash_duo, ds=test_ds, db_path=tmp_db)
    dash_duo.wait_for_element_by_id("save-button", timeout=2)

    # Click forward a few countries
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    for _ in range(10):
        button_country_next.click()

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    first_country = get_dropdown_value(dropdown_country)

    # Add some input for our first country
    input_for_first_country = "All looks great!"
    input_for_notes = dash_duo.driver.find_element(By.ID, "input-for-notes")
    input_for_notes.send_keys(input_for_first_country)

    # Save
    save_button = dash_duo.driver.find_element(By.ID, "save-button")
    save_button.click()

    # Click forward a country
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()
    second_country = get_dropdown_value(dropdown_country)

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
        f"WARNING: notes for {second_country} weren't saved before changing country, "
        "we have saved the notes for you. "
        rf"Notes for {second_country} saved at .* in {tmp_db}. "
        f"Loaded existing notes for {first_country}",
        note_saved_div.text,
    )

    # Check that both notes are in the database
    db = primap_visualisation_tool_stateless_app.notes.read_country_notes_db_as_pd(
        tmp_db
    )
    assert db.shape[0] == 2
    assert (
        db.set_index("country")["notes"].loc[first_country] == input_for_first_country
    )
    assert (
        db.set_index("country")["notes"].loc[second_country] == input_for_second_country
    )
