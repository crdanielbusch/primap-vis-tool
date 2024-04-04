"""
End to end testing of an app that doesn't use global state
"""
from pathlib import Path

import dash
import primap2 as pm
from dash import html
from selenium.webdriver.common.by import By

import primap_visualisation_tool_stateless_app


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

    primap_visualisation_tool_stateless_app.set_application_dataset(test_ds)

    app = primap_visualisation_tool_stateless_app.create_app()
    dash_duo.start_server(app)


def test_003_dropdown_country(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.set_application_dataset(test_ds)

    app = primap_visualisation_tool_stateless_app.create_app()
    dash_duo.start_server(app)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    assert (
        dropdown_country.find_element(By.ID, "react-select-2--value-item").text
        == "EARTH"
    )


def test_004_dropdown_country_earth_not_present(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)
    test_ds = test_ds.pr.loc[{"area (ISO3)": ["AUT", "AUS"]}]

    primap_visualisation_tool_stateless_app.set_application_dataset(test_ds)

    app = primap_visualisation_tool_stateless_app.create_app()
    dash_duo.start_server(app)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    assert (
        dropdown_country.find_element(By.ID, "react-select-2--value-item").text
        == "Australia"
    )


def test_005_dropdown_category(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.set_application_dataset(test_ds)

    app = primap_visualisation_tool_stateless_app.create_app()
    dash_duo.start_server(app)

    dropdown_category = dash_duo.driver.find_element(By.ID, "dropdown-category")
    assert (
        dropdown_category.find_element(By.ID, "react-select-3--value-item").text
        == "M.0.EL"
    )


def test_006_dropdown_entity(dash_duo):
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"

    test_ds = pm.open_dataset(test_file)

    primap_visualisation_tool_stateless_app.set_application_dataset(test_ds)

    app = primap_visualisation_tool_stateless_app.create_app()
    dash_duo.start_server(app)

    dropdown_entity = dash_duo.driver.find_element(By.ID, "dropdown-entity")
    assert (
        dropdown_entity.find_element(By.ID, "react-select-4--value-item").text == "CO2"
    )


# Things to try:
# 1. Try the 'pint-style', set application data, get application data
# 2. Try dash_br
# 3. Try putting the data as JSON in a dcc Store (nervous about performance here)
