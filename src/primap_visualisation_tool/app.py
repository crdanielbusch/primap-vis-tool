"""
Launch plotly app.

Author: Daniel Busch, Date: 2023-12-21
"""
from __future__ import annotations

from collections.abc import Sized
from pathlib import Path

import dash_ag_grid as dag  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import primap2 as pm  # type: ignore
import pycountry
import xarray as xr
from attrs import define
from dash import Dash, Input, Output, State, callback, ctx, dcc, html  # type: ignore

from primap_visualisation_tool.definitions import index_cols, subentities
from primap_visualisation_tool.functions import apply_gwp, select_cat_children


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
            country_options[pycountry.countries.get(alpha_3=code).name] = code
        # use ISO3 code as name if pycountry cannot find a match
        except Exception:
            country_options[code] = code  # implement custom mapping later (Johannes)

    return country_options


# Define app state
@define
class AppState:  # type: ignore
    """
    State of the application

    This object constains all of the application's state and methods to control it.
    The application's state should only be modified by its methods to avoid
    unintended side-effects.
    """

    country_options: tuple[str, ...]
    """Options for the country drop-down"""

    country_name_iso_mapping: dict[str, str]
    """Mapping between country names and their ISO codes"""

    country_index: int
    """Index of current country"""

    category_options: tuple[str, ...]
    """Options for the category drop-down"""

    category_index: int
    """Index of the current category"""

    entity_options: tuple[str, ...]
    """Options for the entity drop-down"""

    entity_index: int
    """Index of the current entity"""

    source_scenario_options: tuple[str, ...]
    """Options for the source-scenario drop-down"""

    ds: xr.Dataset
    """Dataset to plot from"""

    overview_graph: go.Figure | None = None  # type: ignore
    """Main graph"""

    category_graph: go.Figure | None = None  # type: ignore
    """Graph showing breakdown within the selected category"""

    @property
    def country(self) -> str:
        """
        Get country for current index.

        Returns
        -------
            country.
        """
        return self.country_options[self.country_index]

    @property
    def category(self) -> str:
        """
        Get category for current index.

        Returns
        -------
            category.
        """
        return self.category_options[self.category_index]

    @property
    def entity(self) -> str:
        """
        Get entity for current index.

        Returns
        -------
            Entity.
        """
        return self.entity_options[self.entity_index]

    def update_all_indexes(self, country: str, category: str, entity: str) -> None:
        """
        Update all indexes based on the current selection.

        Parameters
        ----------
        country
            Country value to use to determine the new country index

        category
            Category value to use to determine the new category index

        entity
            Entity value to use to determine the new entity index
        """
        self.country_index = self.country_options.index(country)
        self.category_index = self.category_options.index(category)
        self.entity_index = self.entity_options.index(entity)

    def update_country(self, n_steps: int) -> str:
        """
        Update the country in the dropdown selection.

        Parameters
        ----------
        n_steps
            The number of clicks on a button. 1 is one step forward. -1 is one step back.

        Returns
        -------
            Updated country.
        """
        self.country_index = self.update_dropdown(
            start_index=self.country_index,
            options=self.country_options,
            n_steps=n_steps,
        )

        return self.country

    def update_category(self, n_steps: int) -> str:
        """
        Update the category in the dropdown selection.

        Parameters
        ----------
        n_steps
            The number of clicks on a button. 1 is one step forward. -1 is one step back.

        Returns
        -------
            Updated  category.
        """
        self.category_index = self.update_dropdown(
            start_index=self.category_index,
            options=self.category_options,
            n_steps=n_steps,
        )

        return self.category

    def update_entity(self, n_steps: int) -> str:
        """
        Update the entity in the dropdown selection.

        Parameters
        ----------
        n_steps
            The number of clicks on a button. 1 is one step forward. -1 is one step back.

        Returns
        -------
            Updated Entity.
        """
        self.entity_index = self.update_dropdown(
            start_index=self.entity_index,
            options=self.entity_options,
            n_steps=n_steps,
        )

        return self.entity

    @staticmethod
    def update_dropdown(start_index: int, options: Sized, n_steps: int) -> int:
        """
        Update the index of the dropdown options list.

        Parameters
        ----------
        start_index
            The current index in the dropdown selection.

        options
            A list of possible options for the dropdown menu.

        n_steps
            The number of clicks on a button. 1 is one step forward. -1 is one step back.

        Returns
        -------
            Updated index.
        """
        new_index = start_index + n_steps

        new_index = new_index % len(options)

        return new_index

    def update_main_figure(self) -> go.Figure:  # type: ignore
        """
        Update the main figure based on the input in the dropdown menus.

        Parameters
        ----------
        country
            Country value to use to determine the new country index

        category
            Category value to use to determine the new category index

        entity
            Entity value to use to determine the new entity index

        Returns
        -------
            Overview figure. A plotly graph object.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        filtered = (
            self.ds[self.entity]
            .pr.loc[
                {
                    "provenance": ["measured"],
                    "category": self.category,
                    "area (ISO3)": iso_country,
                }
            ]
            .squeeze()
        )

        filtered_pandas = filtered.to_dataframe().reset_index()

        fig = go.Figure()

        for source_scenario in self.source_scenario_options:
            df_source_scenario = filtered_pandas.loc[
                filtered_pandas["SourceScen"] == source_scenario
            ]
            fig.add_trace(
                go.Scatter(
                    x=list(df_source_scenario["time"]),
                    y=list(df_source_scenario[self.entity]),
                    mode="lines",
                    name=source_scenario,
                )
            )

        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True, thickness=0.05), type="date"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=0, b=0),  # distance to next element
        )

        self.overview_graph = fig

        return self.overview_graph

    def update_category_figure(self) -> go.Figure:  # type: ignore
        """
        Update the main figure based on the input in the dropdown menus.

        Parameters
        ----------
        country
            Country value to use to determine the new country index

        category
            Category value to use to determine the new category index

        entity
            Entity value to use to determine the new entity index

        Returns
        -------
            Category figure. A plotly express object.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        categories_plot = select_cat_children(self.category, self.category_options)

        filtered = (
            self.ds[self.entity]
            .pr.loc[
                {
                    "provenance": ["measured"],
                    "category": categories_plot,
                    "area (ISO3)": iso_country,
                    # TODO! dropdown for source/scenario in a following PR
                    "SourceScen": ["PRIMAP-hist_v2.5_final_nr, HISTCR"],
                }
            ]
            .squeeze()
        )

        filtered_pandas = filtered.to_dataframe().reset_index()

        fig = px.area(
            filtered_pandas,
            x="time",
            y=self.entity,
            color="category (IPCC2006_PRIMAP)",
        )

        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=0, b=0),  # distance to next element
        )

        self.category_graph = fig

        return self.category_graph

    def update_entity_figure(self) -> go.Figure:  # type: ignore
        """
        Update the main figure based on the input in the dropdown menus.

        Parameters
        ----------
        country
            Country value to use to determine the new country index

        category
            Category value to use to determine the new category index

        entity
            Entity value to use to determine the new entity index

        Returns
        -------
            Category figure. A plotly express object.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        entities_to_plot = sorted(subentities[self.entity])

        if self.entity not in entities_to_plot:
            entities_to_plot = [
                *entities_to_plot,
                self.entity,
            ]  # need the parent entity for GWP conversion

        filtered = self.ds[entities_to_plot].pr.loc[
            {
                "provenance": ["measured"],
                "category": [self.category],
                "area (ISO3)": [iso_country],
                "SourceScen": ["PRIMAP-hist_v2.5_final_nr, HISTCR"],
            }
        ]

        filtered = apply_gwp(filtered, self.entity)

        stacked = filtered.pr.to_interchange_format().melt(
            id_vars=index_cols, var_name="time", value_name="value"
        )

        fig = px.area(
            stacked,
            x="time",
            y="value",
            color="entity",
        )

        fig.update_layout(
            xaxis=dict(rangeslider=dict(visible=True), type="date"),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=0, b=0),  # distance to next element
        )

        return fig


def get_default_app_starting_state(
    current_version: str = "v2.5_final",
    old_version: str = "v2.4.2_final",
    test_ds: bool = False,
) -> AppState:
    """
    Get default starting state for the application

    Parameters
    ----------
    current_version
        Current version of PRIMAP-hist to inspect

    old_version
        Previous version of PRIMAP-hist to compare against

    test_ds
        Should we load a test dataset instead? This is much
        faster to load.

    Returns
    -------
        Default starting state
    """
    root_folder = Path(__file__).parent.parent.parent
    data_folder = Path("data")

    print("Reading data set")
    if test_ds:
        combined_ds = pm.open_dataset(root_folder / data_folder / "test_ds.nc")
    else:
        combined_ds = pm.open_dataset(
            root_folder
            / data_folder
            / f"combined_data_{current_version}_{old_version}.nc"
        )
    print("Finished reading data set")

    country_name_iso_mapping = get_country_options(combined_ds)
    country_dropdown_options = tuple(sorted(country_name_iso_mapping.keys()))

    category_options = tuple(combined_ds["category (IPCC2006_PRIMAP)"].to_numpy())

    entity_options = tuple(i for i in combined_ds.data_vars)

    source_scenario_options = tuple(combined_ds["SourceScen"].to_numpy())

    app_state = AppState(
        country_options=country_dropdown_options,
        country_name_iso_mapping=country_name_iso_mapping,
        country_index=0,
        category_options=category_options,
        category_index=0,
        entity_options=entity_options,
        entity_index=0,
        source_scenario_options=source_scenario_options,
        ds=combined_ds,
    )

    return app_state


@callback(  # type: ignore
    Output(
        "dropdown-country",
        "value",
        # allow_duplicate=True # this did not work hence one callback not two
    ),
    State("dropdown-country", "value"),
    Input("next_country", "n_clicks"),
    Input("prev_country", "n_clicks"),
)
def handle_country_click(
    country_in: str,
    n_clicks_next_country: int,
    n_clicks_previous_country: int,
    app_state: AppState | None = None,
) -> str:
    """
    Handle a click on next or previous country button

    Parameters
    ----------
    n_clicks_next_country
        Number of clicks on the next country button

    n_clicks_previous_country
        Number of clicks on the previous country button

    country_in
        Country dropdown value when the button is clicked

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Value to update the country dropdown to
    """
    if app_state is None:
        app_state = APP_STATE

    if ctx.triggered_id == "next_country":
        # n_clicks_next_country is the number of clicks since the app started
        # We don't wnat that, just whether we need to go forwards or backwards.
        # We might want to do this differently in future for performance maybe.
        # For further discussion on possible future directions,
        # see https://github.com/crdanielbusch/primap-vis-tool/pull/4#discussion_r1444363726
        return app_state.update_country(n_steps=1)

    if ctx.triggered_id == "prev_country":
        # As above re why -1 not n_clicks_previous_country
        return app_state.update_country(n_steps=-1)

    if ctx.triggered_id is None:
        # Start up, just return current state
        return app_state.country

    raise NotImplementedError(ctx.triggered_id)


@callback(  # type: ignore
    Output(
        "dropdown-category",
        "value",
        # allow_duplicate=True # this did not work hence one callback not two
    ),
    State("dropdown-category", "value"),
    Input("next_category", "n_clicks"),
    Input("prev_category", "n_clicks"),
)
def handle_category_click(
    category_in: str,
    n_clicks_next_category: int,
    n_clicks_previous_category: int,
    app_state: AppState | None = None,
) -> str:
    """
    Handle a click on next or previous category button

    Parameters
    ----------
    n_clicks_next_category
        Number of clicks on the next category button

    n_clicks_previous_category
        Number of clicks on the previous category button

    category_in
        Country dropdown value when the button is clicked

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Value to update the category dropdown to
    """
    if app_state is None:
        app_state = APP_STATE

    if ctx.triggered_id == "next_category":
        # n_clicks_next_category is the number of clicks since the app started
        # We don't wnat that, just whether we need to go forwards or backwards.
        # We might want to do this differently in future for performance maybe.
        return app_state.update_category(n_steps=1)

    if ctx.triggered_id == "prev_category":
        # As above re why -1 not n_clicks_previous_category
        return app_state.update_category(n_steps=-1)

    if ctx.triggered_id is None:
        # Start up, just return current state
        return app_state.category

    raise NotImplementedError(ctx.triggered_id)


@callback(  # type: ignore
    Output(
        "dropdown-entity",
        "value",
        # allow_dupliente=True # this did not work hence one callback not two
    ),
    State("dropdown-entity", "value"),
    Input("next_entity", "n_clicks"),
    Input("prev_entity", "n_clicks"),
)
def handle_entity_click(
    entity_in: str,
    n_clicks_next_entity: int,
    n_clicks_previous_entity: int,
    app_state: AppState | None = None,
) -> str:
    """
    Handle a click on next or previous entity button

    Parameters
    ----------
    n_clicks_next_entity
        Number of clicks on the next entity button

    n_clicks_previous_entity
        Number of clicks on the previous entity button

    entity_in
        Country dropdown value when the button is clicked

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Value to update the entity dropdown to
    """
    if app_state is None:
        app_state = APP_STATE

    if ctx.triggered_id == "next_entity":
        # n_clicks_next_entity is the number of clicks since the app started
        # We don't wnat that, just whether we need to go forwards or backwards.
        # We might want to do this differently in future for performance maybe.
        return app_state.update_entity(n_steps=1)

    if ctx.triggered_id == "prev_entity":
        # As above re why -1 not n_clicks_previous_entity
        return app_state.update_entity(n_steps=-1)

    if ctx.triggered_id is None:
        # Start up, just return current state
        return app_state.entity

    raise NotImplementedError(ctx.triggered_id)


@callback(  # type: ignore
    Output("graph-overview", "figure"),
    Input("dropdown-country", "value"),
    Input("dropdown-category", "value"),
    Input("dropdown-entity", "value"),
)
def update_overview_graph(
    country: str,
    category: str,
    entity: str,
    app_state: AppState | None = None,
) -> go.Figure:
    """
    Update the overview graph.

    Parameters
    ----------
    country
        The currently selected country in the dropdown menu

    category
        The currently selected category in the dropdown menu

    entity
        The currently selected entity in the dropdown menu

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Overview figure.
    """
    if app_state is None:
        app_state = APP_STATE

    if any(v is None for v in (country, category, entity)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.overview_graph

    app_state.update_all_indexes(country, category, entity)

    return app_state.update_main_figure()


@callback(  # type: ignore
    Output("graph-category-split", "figure"),
    Input("dropdown-country", "value"),
    Input("dropdown-category", "value"),
    Input("dropdown-entity", "value"),
)
def update_category_graph(
    country: str,
    category: str,
    entity: str,
    app_state: AppState | None = None,
) -> go.Figure:
    """
    Update the category graph.

    Parameters
    ----------
    country
        The currently selected country in the dropdown menu

    category
        The currently selected category in the dropdown menu

    entity
        The currently selected entity in the dropdown menu

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Category figure.
    """
    if app_state is None:
        app_state = APP_STATE

    if any(v is None for v in (country, category, entity)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.overview_graph

    app_state.update_all_indexes(country, category, entity)

    return app_state.update_category_figure()


@callback(  # type: ignore
    Output("graph-entity-split", "figure"),
    Input("dropdown-country", "value"),
    Input("dropdown-category", "value"),
    Input("dropdown-entity", "value"),
)
def update_entity_graph(
    country: str,
    category: str,
    entity: str,
    app_state: AppState | None = None,
) -> go.Figure:
    """
    Update the entity graph.

    Parameters
    ----------
    country
        The currently selected country in the dropdown menu
    category
        The currently selected category in the dropdown menu
    entity
        The currently selected entity in the dropdown menu

    Returns
    -------
        Entity figure.
    """
    if app_state is None:
        app_state = APP_STATE

    if any(v is None for v in (country, category, entity)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.overview_graph

    app_state.update_all_indexes(country, category, entity)

    return app_state.update_entity_figure()


if __name__ == "__main__":
    APP_STATE = get_default_app_starting_state(test_ds=False)

    external_stylesheets = [dbc.themes.MINTY]

    # define table that will show filtered data set
    table = dag.AgGrid(id="grid")

    # Tell dash that we're using bootstrap for our external stylesheets so
    # that the Col and Row classes function properly
    app = Dash(__name__, external_stylesheets=external_stylesheets)

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
                                options=APP_STATE.country_options,
                                value=APP_STATE.country,
                                id="dropdown-country",
                            ),
                            # this is a line break element
                            # (apparently bad html practice - replace with style param. later)
                            html.Br(),
                            html.Button(
                                id="prev_country", children="prev country", n_clicks=0
                            ),
                            html.Button(
                                id="next_country", children="next country", n_clicks=0
                            ),
                            html.H4(children="Category", style={"textAlign": "center"}),
                            dcc.Dropdown(
                                APP_STATE.category_options,
                                value=APP_STATE.category,
                                id="dropdown-category",
                            ),
                            html.Br(),
                            html.Button(
                                id="prev_category", children="prev category", n_clicks=0
                            ),
                            html.Button(
                                id="next_category", children="next category", n_clicks=0
                            ),
                            html.H4(children="Entity", style={"textAlign": "center"}),
                            dcc.Dropdown(
                                APP_STATE.entity_options,
                                value=APP_STATE.entity,
                                id="dropdown-entity",
                            ),
                            html.Br(),
                            html.Button(
                                id="prev_entity", children="prev entity", n_clicks=0
                            ),
                            html.Button(
                                id="next_entity", children="next entity", n_clicks=0
                            ),
                        ],
                        width=3,  # Column will span this many of the 12 grid columns
                    ),
                    dbc.Col(
                        [
                            html.H4(children="Overview", style={"textAlign": "center"}),
                            dcc.Graph(id="graph-overview"),
                        ],
                        width=9,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Br(),
                            html.H4(
                                children="Category split", style={"textAlign": "center"}
                            ),
                            dcc.Graph(id="graph-category-split"),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Br(),
                            html.H4(
                                children="Entity split", style={"textAlign": "center"}
                            ),
                            dcc.Graph(id="graph-entity-split"),
                        ],
                        width=6,
                    ),
                ]
            ),
            dbc.Row(dbc.Col(table)),
        ],
        style={"max-width": "none", "width": "100%"},
    )

    app.run(debug=True)
