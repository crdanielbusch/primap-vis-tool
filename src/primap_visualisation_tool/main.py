import primap_visualisation_tool.app
import argparse
from primap_visualisation_tool.app import get_filename, get_default_app_starting_state, app
import warnings

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Port number", required=False, default=8050)
    parser.add_argument("-f", help="Filename of data set", required=False)
    args = parser.parse_args()

    port = args.p
    filename = get_filename(user_input=args.f, test_ds=True)

    primap_visualisation_tool.app.APP_STATE = get_default_app_starting_state(filename=filename)

    with warnings.catch_warnings(action="ignore"):  # type: ignore
        app.run(debug=True, port=port)