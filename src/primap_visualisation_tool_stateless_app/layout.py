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

DROPDOWN_STYLING_INITIAL: dict[str, Any] = dict(
    style={
        "fontSize": 12,
    },
)
"""Initial styling to use for dropdowns"""

HEADLINES_STYLING_INITIAL: dict[str, Any] = dict(
    style={"textAlign": "left", "fontSize": 12}
)
"""Initial styling to use for headlines"""


def create_layout(  # type: ignore  # noqa: PLR0913
    country: str,
    country_options: tuple[str, ...],
    category: str,
    category_options: tuple[str, ...],
    entity: str,
    entity_options: tuple[str, ...],
    source_scenario: str,
    source_scenario_options: tuple[str, ...],
) -> list[dcc.Store | dbc.Row]:
    """
    Create the layout for our app
    """
    stores = [
        dcc.Store(id="country-dropdown-store", storage_type="memory"),
        dcc.Store(id="xyrange", storage_type="memory"),
    ]
    country_category_entity_dropdowns = [
        html.B(children="Country", **HEADLINES_STYLING_INITIAL),
        dcc.Dropdown(
            # TODO: try passing in a dict here and see if keys
            # are used for display while values are passed around the app.
            options=country_options,
            value=country,
            id="dropdown-country",
            **DROPDOWN_STYLING_INITIAL,
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
        html.B(children="Category", **HEADLINES_STYLING_INITIAL),
        dcc.Dropdown(
            options=category_options,
            value=category,
            id="dropdown-category",
            **DROPDOWN_STYLING_INITIAL,
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
        html.B(children="Entity", **HEADLINES_STYLING_INITIAL),
        dcc.Dropdown(
            options=entity_options,
            value=entity,
            id="dropdown-entity",
            **DROPDOWN_STYLING_INITIAL,
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
    other_dropdowns = [
        html.B(children="Source Scenario", **HEADLINES_STYLING_INITIAL),
        dcc.Dropdown(
            source_scenario_options,
            value=source_scenario,
            id="dropdown-source-scenario",
            **DROPDOWN_STYLING_INITIAL,
        ),
        # html.Br(),
        html.B(children="Source Scenario dashed", **HEADLINES_STYLING_INITIAL),
        dcc.Dropdown(
            source_scenario_options,
            value=source_scenario,
            id="dropdown-source-scenario-dashed",
            **DROPDOWN_STYLING_INITIAL,
        ),
        # html.Br(),
        html.B(children="GWP to use", **HEADLINES_STYLING_INITIAL),
        dcc.Dropdown(
            ["placeholder"],
            value="placeholder",
            id="dropdown-gwp",
            **DROPDOWN_STYLING_INITIAL,
        ),
    ]

    notes = [
        html.B(children="Notes", **HEADLINES_STYLING_INITIAL),
        dcc.Textarea(
            id="input-for-notes",
            placeholder="No notes for this country yet",
            style={"width": "90%", "margin-left": "10px"},
            rows=4,  # used to define height of text area
        ),
        dbc.Button(
            children="Save",
            id="save-button",
            color="light",
            n_clicks=0,
            style={
                "fontSize": 12,
                "height": "37px",
                "width": "90%",
                "margin-left": "10px",
                "margin-right": "10px",
            },
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
        html.B(children="Overview", **HEADLINES_STYLING_INITIAL),
        dcc.Graph(id=dict(name="graph-overview", type="graph")),
    ]

    category_figure = [
        # html.Br(),
        html.B(children="Category split", **HEADLINES_STYLING_INITIAL),
        dcc.Graph(id=dict(name="graph-category-split", type="graph")),
    ]

    entity_figure = [
        # html.Br(),
        html.B(children="Entity split", **HEADLINES_STYLING_INITIAL),
        dcc.Graph(id=dict(name="graph-entity-split", type="graph")),
    ]

    return [
        dcc.Store(id="memory"),
        dbc.Row(
            [
                # first column with dropdown menus
                dbc.Col(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.Stack(
                                        [
                                            *stores,
                                            *country_category_entity_dropdowns,
                                        ],
                                        gap=1,
                                    ),
                                ),
                                dbc.Col(
                                    dbc.Stack([*other_dropdowns], gap=1),
                                ),
                            ]
                        ),
                        dbc.Row(notes),
                    ]
                ),
                # third column with overview figure
                dbc.Col(
                    overview_figure,
                    width=8,
                ),
            ]
        ),
        dbc.Row(
            [
                dbc.Col(
                    category_figure,
                    width=6,
                ),
                dbc.Col(
                    entity_figure,
                    width=6,
                ),
            ],
        ),
    ]
