# 1. imports of your dash app
from pathlib import Path

import dash
from dash import html

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
    test_file = Path(__file__).parent.parent.parent / "data" / "20240212_test_ds.nc"
    app_state = get_default_app_starting_state(filename=test_file)
    # app = import_app("primap_visualisation_tool.app", application_name="app")
    app = primap_visualisation_tool.app.create_app(app_state=app_state)
    dash_duo.start_server(app)

    prev_country_button = dash_duo.driver.find_element("prev_country")
    dash_duo.multiple_click(prev_country_button, 1)

    assert False, "Write more tests of state"
