"""
Layout for the app
"""
from __future__ import annotations

import dash_bootstrap_components as dbc  # type: ignore
from dash import dcc, html  # type: ignore


def create_layout(  # noqa: PLR0913
    country: str,
    country_options: tuple[str, ...],
    category: str,
    category_options: tuple[str, ...],
    entity: str,
    entity_options: tuple[str, ...],
) -> dbc.Container:
    """
    Create the layout for our app
    """
    return [
        dbc.Col(  # first column with dropdown menus
            dbc.Stack(
                [
                    html.B(
                        children="Country",
                        style={"textAlign": "left", "fontSize": 14},
                    ),
                    dcc.Dropdown(
                        # TODO: try passing in a dict here and see if keys
                        # are used for display while values are passed around the app.
                        options=country_options,
                        value=country,
                        id="dropdown-country",
                    ),
                    html.B(
                        children="Category",
                        style={"textAlign": "left", "fontSize": 14},
                    ),
                    dcc.Dropdown(
                        options=category_options,
                        value=category,
                        id="dropdown-category",
                    ),
                    html.B(
                        children="Entity",
                        style={"textAlign": "left", "fontSize": 14},
                    ),
                    dcc.Dropdown(
                        options=entity_options,
                        value=entity,
                        id="dropdown-entity",
                    ),
                ]
            )
        )
    ]
