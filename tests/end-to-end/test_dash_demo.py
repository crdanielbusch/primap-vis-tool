# 1. imports of your dash app
from pathlib import Path

import dash
from dash import html
from selenium.webdriver.common.by import By

import primap_visualisation_tool.app
from primap_visualisation_tool.app_state import get_default_app_starting_state


def test_001_dash_example(dash_duo):
    # A test that the dash example runs. If this breaks things are really broken -issue beyond our code.
    app = dash.Dash(__name__)
    app.layout = html.Div(id="nully-wrapper", children=0)
    dash_duo.start_server(app)
    dash_duo.wait_for_text_to_equal("#nully-wrapper", "0", timeout=4)
    assert dash_duo.find_element("#nully-wrapper").text == "0"


def test_002_app_starts(dash_duo):
    # find package primap_visualisation_tool, find varibale app
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    app_state = get_default_app_starting_state(filename=test_file)
    # app = import_app("primap_visualisation_tool.app", application_name="app")
    app = primap_visualisation_tool.app.create_app(app_state=app_state)
    dash_duo.start_server(app)

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    assert (
        dropdown_country.find_element(By.ID, "react-select-2--value-item").text
        == "EARTH"
    )

    dropdown_category = dash_duo.driver.find_element(By.ID, "dropdown-category")
    assert (
        dropdown_category.find_element(By.ID, "react-select-3--value-item").text
        == "M.0.EL"
    )

    dropdown_entity = dash_duo.driver.find_element(By.ID, "dropdown-entity")
    assert (
        dropdown_entity.find_element(By.ID, "react-select-4--value-item").text
        == "KYOTOGHG (AR6GWP100)"
    )

    dropdown_source_scenario = dash_duo.driver.find_element(
        By.ID, "dropdown-source-scenario"
    )
    assert (
        dropdown_source_scenario.find_element(By.ID, "react-select-5--value-item").text
        == "PRIMAP-hist_v2.5_final_nr, HISTCR"
    )

    for button_id, expected_text in [
        ("prev_country", "prev country"),
        ("next_country", "next country"),
        ("prev_category", "prev category"),
        ("next_category", "next category"),
        ("prev_entity", "prev entity"),
        ("next_entity", "next entity"),
        ("save_button", "Save"),
        ("select-AR4GWP100", "AR4GWP100"),
        ("select-AR5GWP100", "AR5GWP100"),
        ("select-AR6GWP100", "AR6GWP100"),
        ("select-SARGWP100", "SARGWP100"),
    ]:
        button = dash_duo.driver.find_element(By.ID, button_id)
        assert button.text == expected_text
        assert button.tag_name == "button"

    # Check that there is a notes field.
    # An error is raised by the `find_element` method
    # if no element with the expected ID can be found.
    dash_duo.driver.find_element(By.ID, "input-for-notes")

    figures_expected_items = (
        (
            "graph-overview",
            [
                "PRIMAP-hist_v2.5_final_nr, HISTTP",
                "PRIMAP-hist_v2.5_final_nr, HISTCR",
                "CRF 2022, 230510",
                "CRF 2023, 230926",
                "EDGAR 7.0, HISTORY",
                "UNFCCC NAI, 231015",
            ],
        ),
        (
            "graph-category-split",
            [
                "total",
                "1 pos",
                "2 pos",
                "4 pos",
                "5 pos",
                "M.AG pos",
            ],
        ),
        (
            "graph-entity-split",
            [
                "total",
                "CH4 (AR6GWP100) pos",
                "CO2 (AR6GWP100) pos",
                "N2O (AR6GWP100) pos",
                "FGASES (AR6GWP100) pos",
            ],
        ),
    )
    for figure_id, expected_legend_items in figures_expected_items:
        figure = dash_duo.driver.find_element(By.ID, figure_id)
        legend = figure.find_element(By.CLASS_NAME, "legend")
        traces = legend.find_elements(By.CLASS_NAME, "traces")
        legend_items = [trace.text for trace in traces]

        # Check that elements are the same,
        # worrying about ordering is a problem for another day.
        assert sorted(legend_items) == sorted(expected_legend_items)

    data_table = dash_duo.driver.find_element(By.ID, "grid")
    header_cell_labels = data_table.find_elements(By.CLASS_NAME, "ag-header-cell-label")
    assert len(header_cell_labels) == 5, "Wrong number of columns in data table"
