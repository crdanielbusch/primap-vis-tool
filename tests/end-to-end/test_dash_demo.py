# 1. imports of your dash app
from pathlib import Path

import dash
from dash import html
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

import primap_visualisation_tool.app
from primap_visualisation_tool.app_state import get_default_app_starting_state


def test_001_dash_example(dash_duo_mp):
    # A test that the dash example runs. If this breaks things are really broken -issue beyond our code.
    app = dash.Dash(__name__)
    app.layout = html.Div(id="nully-wrapper", children=0)
    dash_duo_mp.start_server(app)
    dash_duo_mp.wait_for_text_to_equal("#nully-wrapper", "0", timeout=4)
    assert dash_duo_mp.find_element("#nully-wrapper").text == "0"


def test_002_app_starts(dash_duo_mp):
    # find package primap_visualisation_tool, find varibale app
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    app_state = get_default_app_starting_state(filename=test_file)
    app = primap_visualisation_tool.app.create_app(app_state=app_state)

    dash_duo_mp.start_server(app)

    dropdown_country = dash_duo_mp.driver.find_element(By.ID, "dropdown-country")
    assert (
        dropdown_country.find_element(By.ID, "react-select-2--value-item").text
        == "EARTH"
    )

    dropdown_category = dash_duo_mp.driver.find_element(By.ID, "dropdown-category")
    assert (
        dropdown_category.find_element(By.ID, "react-select-3--value-item").text
        == "M.0.EL"
    )

    dropdown_entity = dash_duo_mp.driver.find_element(By.ID, "dropdown-entity")
    assert (
        dropdown_entity.find_element(By.ID, "react-select-4--value-item").text
        == "KYOTOGHG (AR6GWP100)"
    )

    dropdown_source_scenario = dash_duo_mp.driver.find_element(
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
        button = dash_duo_mp.driver.find_element(By.ID, button_id)
        assert button.text == expected_text
        assert button.tag_name == "button"

    # Check that there is a notes field.
    # An error is raised by the `find_element` method
    # if no element with the expected ID can be found.
    dash_duo_mp.driver.find_element(By.ID, "input-for-notes")

    import time

    next_country_button = dash_duo_mp.driver.find_element(By.ID, "next_country")
    prev_country_button = dash_duo_mp.driver.find_element(By.ID, "prev_country")
    next_country_button.click()
    time.sleep(1)
    next_country_button.click()
    time.sleep(1)
    prev_country_button.click()
    time.sleep(1)
    prev_country_button.click()
    time.sleep(1)

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
        figure = dash_duo_mp.driver.find_element(By.ID, figure_id)
        wait = WebDriverWait(dash_duo_mp.driver, timeout=5)
        wait.until(lambda d: figure.find_elements(By.CLASS_NAME, "legend"))
        legend = figure.find_element(By.CLASS_NAME, "legend")
        traces = legend.find_elements(By.CLASS_NAME, "traces")
        legend_items = [trace.text for trace in traces]

        # Check that elements are the same,
        # worrying about ordering is a problem for another day.
        assert sorted(legend_items) == sorted(expected_legend_items)

    data_table = dash_duo_mp.driver.find_element(By.ID, "grid")
    header_cell_labels = data_table.find_elements(By.CLASS_NAME, "ag-header-cell-label")
    assert len(header_cell_labels) == 5, "Wrong number of columns in data table"


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


# # TODO: uncomment and use the tests below in a future MR
# def create_testing_dataset() -> xr.Dataset:
#     # our dimensions are:
#     # (time: 5, category (IPCC2006_PRIMAP): 24,
#     #  area (ISO3): 216, SourceScen: 17)
#     # data variables: CO2, HFCS (SARGWP100)
#     dimensions = ["time", "category (IPCC2006_PRIMAP)", "area (ISO3)", "SourceScen"]
#     categories = ["1", "2"]
#     area = ["ABW", "AFG"]
#     source_scen = ["PRIMAP_hist_2.5.1", "RCMIP", "EDGAR"]
#     time = np.array(["2000-01-01", "2001-01-01", "2002-01-01"], dtype="datetime64")
#
#     array_shape = [len(v) for v in [time, categories, area, source_scen]]
#     array_n_elements = np.product(array_shape)
#     co2 = np.arange(array_n_elements).reshape(array_shape)
#     hfcs = 1e-3 * np.arange(array_n_elements).reshape(array_shape)
#
#     test_ds = xr.Dataset(
#         data_vars={"CO2": (dimensions, co2), "HFCS (SARGWP100)": (dimensions, hfcs)},
#         coords={
#             "category (IPCC2006_PRIMAP)": categories,
#             "time": time,
#             "area (ISO3)": area,
#             "SourceScen": source_scen,
#         },
#         attrs={"area": "area (ISO3)", "cat": "category (IPCC2006_PRIMAP)"},
#     )
#
#     # Make sure that CO2 is NaN for RCMIP
#     test_ds["CO2"] = test_ds["CO2"].where(test_ds["CO2"]["SourceScen"] != "RCMIP")
#     # Make sure that HFCs are NaN for EDGAR
#     test_ds["HFCS (SARGWP100)"] = test_ds["HFCS (SARGWP100)"].where(
#         test_ds["HFCS (SARGWP100)"]["SourceScen"] != "EDGAR"
#     )
#
#     return test_ds
#
#
# def create_app_state(
#     dataset: xr.Dataset,
#     start_country: str | None = None,
#     start_category: str | None = None,
#     start_entity: str | None = None,
#     start_source_scenario: str | None = None,
#     filename: str = "testing_app_state",
#     present_index_cols: list[str] | None = None,
#     category_dimension: str = "category (IPCC2006_PRIMAP)",
#     source_scenario_dimension: str = "SourceScen",
# ) -> AppState:
#     country_name_iso_mapping = get_country_options(dataset)
#     country_dropdown_options = tuple(sorted(country_name_iso_mapping.keys()))
#
#     category_options = tuple(dataset[category_dimension].to_numpy())
#
#     entity_options = tuple(i for i in dataset.data_vars)
#
#     source_scenario_options = tuple(dataset[source_scenario_dimension].to_numpy())
#     source_scenario_visible = {
#         k: v
#         for (k, v) in zip(
#             source_scenario_options, [True] * len(source_scenario_options)
#         )
#     }
#
#     if present_index_cols is None:
#         present_index_cols = ["not", "used"]
#
#     app_state = AppState(
#         country_options=country_dropdown_options,
#         country_name_iso_mapping=country_name_iso_mapping,
#         country_index=country_dropdown_options.index(start_country),
#         category_options=category_options,
#         category_index=category_options.index(start_category),
#         entity_options=entity_options,
#         entity_index=entity_options.index(start_entity),
#         source_scenario_options=source_scenario_options,
#         source_scenario_index=source_scenario_options.index(start_source_scenario),
#         source_scenario_visible=source_scenario_visible,
#         ds=dataset,
#         filename=filename,
#         present_index_cols=present_index_cols,
#     )
#
#     return app_state
#
#
# def test_entity_click_one_forward_switch_from_co2_to_hfcs():
#     """
#     Turns out that (we think) the callbacks are wired together in JavaScript land
#
#     Hence you can't get the cascading callback effect
#     (output from one callback triggers another callback)
#     just running the tests directly from Python.
#     Hence we're abandoning this integration test idea, moving onto end-to-end testing instead.
#     """
#     starting_entity = "CO2"
#     dataset = create_testing_dataset()
#     app_state = create_app_state(
#         dataset,
#         start_country="Afghanistan",
#         start_category="1",
#         start_entity="CO2",
#         start_source_scenario="EDGAR",
#     )
#     # Not sure whether this should be in create_app_state,
#     # having to call this at all kind of feels wrong,
#     # but reproducing the logic for filtering out nans in the test
#     # also feels wrong.
#     # Probably points to a bug in get_default_app_starting_state,
#     # but doesn't really matter as the initial callbacks clean up the state.
#     app_state.update_source_scenario_options()
#
#     starting_categories = app_state.category_options
#     exp_categories = copy.deepcopy(starting_categories)
#
#     exp_source_starting_scenario_options = ("PRIMAP_hist_2.5.1", "EDGAR")
#     assert app_state.source_scenario_options == exp_source_starting_scenario_options
#
#     # We would have preferred to just update the entity value,
#     # then see what happens.
#     # However, we couldn't work out if an API for that exists
#     # so we're just doing it this way instead.
#     def run_callback():
#         context_value.set(
#             AttributeDict(**{"triggered_inputs": [{"prop_id": "next_entity.n_clicks"}]})
#         )
#
#         return handle_entity_click(
#             entity_in=starting_entity,
#             n_clicks_next_entity=1,
#             n_clicks_previous_entity=0,
#             app_state=app_state,
#         )
#
#     ctx = copy_context()
#     ctx.run(run_callback)
#
#     exp_new_entity = "HFCS (SARGWP100)"
#     assert app_state.entity == exp_new_entity
#
#     exp_source_scenario_options = ("PRIMAP_hist_2.5.1", "RCMIP")
#     assert app_state.source_scenario_options == exp_source_scenario_options
#
#     exp_source_scenario = "PRIMAP_hist_2.5.1"
#     assert app_state.source_scenario == exp_source_scenario
#
#     # TODO in future MR: update this so that the categories change to only available categories
#     # (x-ref timeseries selection section in #27)
#     assert app_state.category_options == exp_categories
#
#     assert app_state.entity_graph
#     assert False, "Figure out what we can test about this reliably"
#
#     assert app_state.category_graph
#     assert False, "Figure out what we can test about this reliably"
#
#     assert app_state.overview_graph
#     assert False, "Figure out what we can test about this reliably"
#
#     assert False, "Write test"
