"""
Launch plotly app.

Author: Daniel Busch, Date: 2023-12-21
"""

from pathlib import Path

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import primap2 as pm  # type: ignore
import pycountry
import xarray as xr
from dash import Dash, Input, Output, State, callback, ctx, dcc, html

#  define folders
print("Reading data set")
root_folder = Path(__file__).parent
data_folder = Path("data")
primaphist_data_folder = Path("data") / "PRIMAP-hist_data"

#  data reading
current_version = "v2.5_final"
old_version = "v2.4.2_final"
combined_ds = pm.open_dataset(
    root_folder / data_folder / f"combined_data_{current_version}_{old_version}.nc"
)


def get_country_options(inds: xr.Dataset) -> dict[str, str]:
    """
    Get ISO3 country codes.

    Parameters
    ----------
    inds
        Input :obj:`xr.Dataset` from which we want to extract country names

    Returns
    -------
        :obj:`dict` with ISO3 codes as keys and full country name as values
    """
    all_countries = inds.coords["area (ISO3)"].to_numpy()
    country_options = {}
    for code in all_countries:
        try:
            country_options[code] = pycountry.countries.get(alpha_3=code).name
        # use ISO3 code as name if pycountry cannot find a match
        except Exception:
            country_options[code] = code  # implement custom mapping later (Johannes)

    return country_options


country_options = get_country_options(combined_ds)

category_options = list(combined_ds["category (IPCC2006_PRIMAP)"].to_numpy())

entity_options = [i for i in combined_ds.data_vars]

external_stylesheets = [dbc.themes.MINTY]
# Tell dash that we're using bootstrap for our external stylesheets so
# that the Col and Row classes function properly
app = Dash(__name__, external_stylesheets=external_stylesheets)

# define table that will show filtered data set
table = dag.AgGrid(id="grid")

# define layout
# to be adjusted once everything is running
app.layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1(
                            children="Primap-hist data explorer",
                            style={"textAlign": "center"},
                        ),
                        html.H4(children="Country", style={"textAlign": "center"}),
                        dcc.Dropdown(
                            options=country_options,
                            value=list(country_options.keys())[0],
                            id="dropdown-country",
                        ),
                        html.Button(
                            id="prev_count", children="prev. country", n_clicks=0
                        ),
                        html.Button(
                            id="next_count", children="next country", n_clicks=0
                        ),
                        html.H4(children="Category", style={"textAlign": "center"}),
                        dcc.Dropdown(
                            category_options,
                            value=category_options[0],
                            id="dropdown-category",
                        ),
                        html.Button(
                            id="prev_cat", children="prev. category", n_clicks=0
                        ),
                        html.Button(
                            id="next_cat", children="next category", n_clicks=0
                        ),
                        html.H4(children="Entity", style={"textAlign": "center"}),
                        dcc.Dropdown(
                            entity_options,
                            value=entity_options[0],
                            id="dropdown-entity",
                        ),
                        html.Button(id="prev_ent", children="prev. entity", n_clicks=0),
                        html.Button(id="next_ent", children="next entity", n_clicks=0),
                    ]
                ),
                dbc.Col(
                    [
                        html.H4(children="Overview", style={"textAlign": "center"}),
                        dcc.Graph(id="graph-overview"),
                    ]
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H4(
                            children="Category split", style={"textAlign": "center"}
                        ),
                        dcc.Graph(id="graph-category-split"),
                    ]
                ),
                dbc.Col(
                    [
                        html.H4(children="Entity split", style={"textAlign": "center"}),
                        dcc.Graph(id="graph-entity-split"),
                    ]
                ),
            ]
        ),
        dbc.Row(dbc.Col(table)),
    ]
)

country_options_codes = list(country_options.keys())


def prev_dropdown_value(options: list[str], value: str) -> str:
    """
    Move to previous value in dropdown options.

    Parameters
    ----------
    options
        Input :obj:`list` a list of all possible dropdown menu options.
    value
        Input :obj:`str` the current value in the dropdown menu.


    Returns
    -------
        :obj:`str` the previous value in the dropdown menu.
    """
    index = options.index(value)
    index = index - 1
    if index < 0:
        index = len(options) - 1
    return options[index]


def next_dropdown_value(options: list[str], value: str) -> str:
    """
    Move to next value in dropdown options.

    Parameters
    ----------
    options
        Input :obj:`list` a list of all possible dropdown menu options.
    value
        Input :obj:`str` the current value in the dropdown menu.


    Returns
    -------
        :obj:`str` the next value in the dropdown menu.
    """
    index = options.index(value)
    index = index + 1
    if index > len(options) - 1:
        index = 0
    return options[index]


# A change of Input - click on thr button - triggers the callback.
# Current value is State object, so it does not trigger
# the callback when changed via dropdown menu.
@callback(
    Output("dropdown-country", "value"),
    Output("dropdown-category", "value"),
    Output("dropdown-entity", "value"),
    State("dropdown-country", "value"),
    State("dropdown-category", "value"),
    State("dropdown-entity", "value"),
    Input("prev_count", "n_clicks"),
    Input("next_count", "n_clicks"),
    Input("prev_cat", "n_clicks"),
    Input("next_cat", "n_clicks"),
    Input("prev_ent", "n_clicks"),
    Input("next_ent", "n_clicks"),
)
# ruff will complain about too many arguments in the next function
# I am not sure if there is a better way to do it.
def update_dropdown_value(  # noqa: PLR0913
    count_in,
    cat_in,
    ent_in,
    n_clicks_count_prev,
    n_clicks_count_next,
    n_clicks_cat_prev,
    n_clicks_cat_next,
    n_clicks_ent_prev,
    n_clicks_ent_next,
):
    """
    Update values in dropdown when button is clicked.

    Parameters
    ----------
    count_in
        Input :obj:`str` current value for country in dropdown.
    cat_in
        Input :obj:`str` current value for category in dropdown.
    ent_in
        Input :obj:`str` current value for entity in dropdown.
    n_clicks_count_prev
        Input :obj:`int` number of clicks for previous country button.
    n_clicks_count_next
            Input :obj:`int` number of clicks for next country button.
    n_clicks_cat_prev
            Input :obj:`int` number of clicks for previous category button.
    n_clicks_cat_next
            Input :obj:`int` number of clicks for next category button.
    n_clicks_ent_prev
            Input :obj:`int` number of clicks for previous entity button.
    n_clicks_ent_next
            Input :obj:`int` number of clicks for next entity button.


    Returns
    -------
        :obj:`str` the updated value in the country dropdown menu.
        :obj:`str` the updated value in the category dropdown menu.
        :obj:`str` the updated value in the entity dropdown menu.
    """
    count_out, cat_out, ent_out = count_in, cat_in, ent_in
    if "prev_count" == ctx.triggered_id:
        count_out = prev_dropdown_value(country_options_codes, count_in)
    elif "next_count" == ctx.triggered_id:
        count_out = next_dropdown_value(country_options_codes, count_in)
    elif "prev_cat" == ctx.triggered_id:
        cat_out = prev_dropdown_value(category_options, cat_in)
    elif "next_cat" == ctx.triggered_id:
        cat_out = next_dropdown_value(category_options, cat_in)
    elif "prev_ent" == ctx.triggered_id:
        ent_out = prev_dropdown_value(entity_options, ent_in)
    elif "next_ent" == ctx.triggered_id:
        ent_out = next_dropdown_value(entity_options, ent_in)

    return count_out, cat_out, ent_out


if __name__ == "__main__":
    app.run(debug=True)
