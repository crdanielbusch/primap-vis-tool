# 1. imports of your dash app
from pathlib import Path

import dash
from dash import html
from selenium.webdriver.common.by import By

import primap_visualisation_tool.app
from primap_visualisation_tool.app_state import get_default_app_starting_state


# 2. give each testcase a test case ID, and pass the fixture
# dash_duo as a function argument
def test_001_child_with_0(dash_duo):
    # 3. define your app inside the test function
    app = dash.Dash(__name__)
    app.layout = html.Div(id="nully-wrapper", children=0)
    # 4. host the app locally in a thread, all dash server configs could be
    # passed after the first app argument
    dash_duo.start_server(app)
    # 5. use wait_for_* if your target element is the result of a callback,
    # keep in mind even the initial rendering can trigger callbacks
    dash_duo.wait_for_text_to_equal("#nully-wrapper", "0", timeout=4)

    # 6. use this form if its present is expected at the action point
    assert dash_duo.find_element("#nully-wrapper").text == "0"
    # 7. to make the checkpoint more readable, you can describe the
    # acceptance criterion as an assert message after the comma.
    assert dash_duo.get_logs() == [], "browser console should contain no error"


def test_002_app_starts(dash_duo):
    # find package primap_visualisation_tool, find varibale app
    test_file = Path(__file__).parent.parent.parent / "data" / "test_ds.nc"
    app_state = get_default_app_starting_state(filename=test_file)
    # app = import_app("primap_visualisation_tool.app", application_name="app")
    app = primap_visualisation_tool.app.create_app(app_state=app_state)
    dash_duo.start_server(app)

    # use for different test
    # prev_country_button = dash_duo.driver.find_element(By.ID, "prev_country")

    dropdown_country = dash_duo.driver.find_element(By.ID, "dropdown-country")
    # TODO better to use wait_for_*(), see dash docs
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
