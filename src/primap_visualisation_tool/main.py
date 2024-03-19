"""
Main entry point for running the app
"""
import argparse
import warnings

import primap_visualisation_tool.app_state
from primap_visualisation_tool.app import (
    app,
    get_filename,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Port number", required=False, default=8050)
    parser.add_argument("-f", help="Filename of data set", required=False)
    args = parser.parse_args()

    port = args.p
    filename = get_filename(user_input=args.f, test_ds=True)

    primap_visualisation_tool.app_state.APP_STATE = (
        primap_visualisation_tool.app_state.get_default_app_starting_state(
            filename=filename
        )
    )

    with warnings.catch_warnings(action="ignore"):  # type: ignore
        app.run(debug=True, port=port)
