"""
Main entry point for running the app
"""
import argparse
import warnings
from pathlib import Path

import primap_visualisation_tool.app_state
from primap_visualisation_tool.app import (
    create_app,
    get_filename,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Port number", required=False, default=8050)
    parser.add_argument("-f", help="Filename of data set", required=False)
    args = parser.parse_args()

    port = args.p
    filename = get_filename(user_input=args.f, test_ds=True)

    app_state = primap_visualisation_tool.app_state.get_default_app_starting_state(
        filename=Path(filename)
    )
    app = create_app(app_state=app_state)

    with warnings.catch_warnings(action="ignore"):
        app.run(debug=True, port=port)
