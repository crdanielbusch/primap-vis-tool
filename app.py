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
from dash import Dash, dcc, html

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
    -----------
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

category_options = combined_ds["category (IPCC2006_PRIMAP)"].to_numpy()

entity_options = [i for i in combined_ds.data_vars]

external_stylesheets = [dbc.themes.MINTY]
# Tell dash that we're using bootstrap for our external stylesheets so
# that the Col and Row classes function properly
app = Dash(__name__, external_stylesheets=external_stylesheets)

# set a placeholder for now
placeholder = ["placeholder"] * 10

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
                        html.Button(id="prev_gas", children="prev. gas", n_clicks=0),
                        html.Button(id="next_gas", children="next gas", n_clicks=0),
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

if __name__ == "__main__":
    app.run(debug=True)
