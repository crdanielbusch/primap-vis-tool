"""
End to end testing of an app that doesn't use global state
"""
from pathlib import Path

import dash
import primap2 as pm
from dash import html
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import primap_visualisation_tool_stateless_app
import primap_visualisation_tool_stateless_app.callbacks
import primap_visualisation_tool_stateless_app.dataset_holder


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


def test_007_country_button_next(dash_duo):
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

    # Click next
    button_country_next = dash_duo.driver.find_element(By.ID, "next_country")
    button_country_next.click()

    # Country dropdown should update
    assert dropdown_country_select_element.text == "EU27BX"


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

            assert f"stroke: {color}" in js_line.get_attribute("style")

            # assert


# Things to try:
# 1. Try the 'pint-style', set application data, get application data
# 2. Try dash_br
# 3. Try putting the data as JSON in a dcc Store (nervous about performance here)
