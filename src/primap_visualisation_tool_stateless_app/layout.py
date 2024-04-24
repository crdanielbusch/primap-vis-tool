"""
Layout for the app
"""
from __future__ import annotations

from typing import Any

import dash_bootstrap_components as dbc  # type: ignore
from dash import dcc, html  # type: ignore

BUTTON_STYLING_INITIAL: dict[str, Any] = dict(
    color="light",
    n_clicks=0,
    style={
        "fontSize": 12,
        "height": "37px",
    },
)
"""Initial styling to use for buttons"""


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
    dropdowns_and_buttons = [
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
        dbc.ButtonGroup(
            [
                dbc.Button(
                    id="prev_country", children="prev country", **BUTTON_STYLING_INITIAL
                ),
                dbc.Button(
                    id="next_country", children="next country", **BUTTON_STYLING_INITIAL
                ),
            ]
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
        dbc.ButtonGroup(
            [
                dbc.Button(
                    id="prev_category",
                    children="prev category",
                    **BUTTON_STYLING_INITIAL,
                ),
                dbc.Button(
                    id="next_category",
                    children="next category",
                    **BUTTON_STYLING_INITIAL,
                ),
            ]
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
        dbc.ButtonGroup(
            [
                dbc.Button(
                    id="prev_entity", children="prev entity", **BUTTON_STYLING_INITIAL
                ),
                dbc.Button(
                    id="next_entity", children="next entity", **BUTTON_STYLING_INITIAL
                ),
            ]
        ),
    ]

    notes = [
        html.B(
            children="Notes",
            style={"textAlign": "left", "fontSize": 14},
        ),
        dcc.Textarea(
            id="input-for-notes",
            placeholder="No notes for this country yet",
            style={"width": "100%"},
            rows=8,  # used to define height of text area
        ),
        dbc.Button(
            children="Save",
            id="save-button",
            n_clicks=0,
            color="light",
            style={"fontsize": 12, "height": "37px"},
        ),
        html.H4(
            id="note-saved-div",
            children="",
            style={
                "textAlign": "center",
                "color": "grey",
                "fontSize": 12,
            },
        ),
    ]

    overview_figure = [
        html.B(children="Overview", style={"textAlign": "center"}),
        dcc.Graph(id="graph-overview"),
    ]

    return [
        dbc.Row(
            [
                dbc.Col(
                    dbc.Stack(dropdowns_and_buttons)
                ),  # first column with dropdown menus
                dbc.Col(dbc.Stack(notes)),
                dbc.Col(
                    overview_figure,
                    width=8,
                ),
            ]
        )
    ]
