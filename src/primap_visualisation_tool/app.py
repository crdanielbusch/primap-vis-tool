"""
Launch plotly app.

Author: Daniel Busch, Date: 2023-12-21
"""
from __future__ import annotations

from collections.abc import Sized
from pathlib import Path

import dash_ag_grid as dag  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import primap2 as pm  # type: ignore
import pycountry
import xarray as xr
from attrs import define
from dash import Dash, Input, Output, State, callback, ctx, dcc, html  # type: ignore

from primap_visualisation_tool.definitions import SUBENTITIES, index_cols
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

    source_scenario_index: int
    """Index of the current source-scenario"""

    ds: xr.Dataset
    """Dataset to plot from"""

    overview_graph: go.Figure | None = None  # type: ignore
    """Main graph"""

    category_graph: go.Figure | None = None  # type: ignore
    """Graph showing breakdown within the selected category"""

    entity_graph: go.Figure | None = None  # type: ignore
    """Graph showing breakdown within the selected entity"""

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

    @property
    def source_scenario(self) -> str:
        """
        Get source_scenario for current index.

        Returns
        -------
            source_scenario.
        """
        return self.source_scenario_options[self.source_scenario_index]

    def update_source_scenario_options(self) -> None:
        """
        Update the source scenario dropdown options according to country, category and entity

        """
        iso_country = self.country_name_iso_mapping[self.country]

        filtered = (
            self.ds[self.entity]
            .pr.loc[
                {
                    "category": self.category,
                    "area (ISO3)": iso_country,
                }
            ]
            .squeeze()
        )

        filtered_pandas = filtered.to_dataframe().reset_index()

        null_source_scenario_options = filtered_pandas.groupby(by="SourceScen")[
            self.entity
        ].apply(lambda x: x.isna().all())

        null_source_scenario_options = null_source_scenario_options[
            list(null_source_scenario_options)
        ].index

        original_source_scenario_options = tuple(self.ds["SourceScen"].to_numpy())

        new_source_scenario_options = [
            i
            for i in original_source_scenario_options
            if i not in null_source_scenario_options
        ]

        if not new_source_scenario_options:
            return

        self.source_scenario_options = tuple(new_source_scenario_options)

    def update_all_indexes(
        self, country: str, category: str, entity: str, source_scenario: str
    ) -> None:
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

        source_scenario
            Source-scenario value to use to determine the new entity index
        """
        # store value of source_scenario

        self.country_index = self.country_options.index(country)
        self.category_index = self.category_options.index(category)
        self.entity_index = self.entity_options.index(entity)

        # filter source scenario index
        self.update_source_scenario_options()
        # update source scenario list
        # when value is not part of new options list, take the first
        if source_scenario in self.source_scenario_options:
            self.source_scenario_index = self.source_scenario_options.index(
                source_scenario
            )
        else:
            self.source_scenario_index = 0

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

        Returns
        -------
            Overview figure. A plotly graph object.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        filtered = (
            self.ds[self.entity]
            .pr.loc[
                {
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
                    "category": categories_plot,
                    "area (ISO3)": iso_country,
                    "SourceScen": self.source_scenario,
                }
            ]
            .squeeze()
        )

        filtered_pandas = filtered.to_dataframe().reset_index()

        # TODO! Either delete this or implement exception for all-nan subcategories
        if filtered_pandas[self.entity].isna().all():
            print(f"All sub-categories in category {self.category} are nan")

        # Fix for figure not loading at start
        # https://github.com/plotly/plotly.py/issues/3441
        fig = go.Figure(layout=dict(template="plotly"))

        fig = px.area(
            filtered_pandas,
            x="time",
            y=self.entity,
            color="category (IPCC2006_PRIMAP)",
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=0, b=0),  # distance to next element
        )

        self.category_graph = fig

        return self.category_graph

    def update_entity_figure(self) -> go.Figure:  # type: ignore
        """
        Update the main figure based on the input in the dropdown menus.

        Returns
        -------
            Entity figure.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        entities_to_plot = sorted(SUBENTITIES[self.entity])

        drop_parent = False
        if self.entity not in entities_to_plot:
            # need the parent entity for GWP conversion
            entities_to_plot = [*entities_to_plot, self.entity]
            drop_parent = True

        filtered = self.ds[entities_to_plot].pr.loc[
            {
                "category": [self.category],
                "area (ISO3)": [iso_country],
                "SourceScen": [self.source_scenario],
            }
        ]

        filtered = apply_gwp(filtered, self.entity)

        # Drop the parent entity out before plotting (as otherwise the
        # area plot doesn't make sense)
        # TODO! Check if there is a nicer logic for that
        if drop_parent:
            filtered = filtered.drop_vars(self.entity)

        stacked = filtered.pr.to_interchange_format().melt(
            id_vars=index_cols, var_name="time", value_name="value"
        )

        stacked["time"] = stacked["time"].apply(pd.to_datetime)

        fig = px.area(
            stacked,
            x="time",
            y="value",
            color="entity",
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=0, b=0),  # distance to next element
        )

        self.entity_graph = fig

        return self.entity_graph

    def update_category_xrange(self, layout_data: dict[str, list[str]]) -> go.Figure:  # type: ignore
        """
        Update x-range of category figure according to main figure x-range.

        Parameters
        ----------
        layout_data
            The information about the xrange of the main figure.

        """
        fig = self.category_graph

        fig["layout"].update(  # type: ignore
            xaxis_range=layout_data["xaxis.range"],
        )

        return fig

    def update_entity_xrange(self, layout_data: dict[str, list[str]]) -> go.Figure:  # type: ignore
        """
        Update x-range of entity figure according to main figure x-range.

        Parameters
        ----------
        layout_data
            The information about the xrange of the main figure.

        """
        fig = self.entity_graph

        fig["layout"].update(  # type: ignore
            xaxis_range=layout_data["xaxis.range"],
        )

        return fig


def get_default_app_starting_state(
    current_version: str = "v2.5_final",
    old_version: str = "v2.4.2_final",
    start_values: dict[str, str] = {
        "country": "EARTH",
        "category": "M.0.EL",
        "entity": "KYOTOGHG (AR6GWP100)",
        "source_scenario": "PRIMAP-hist_v2.5_final_nr, HISTCR",
    },
    test_ds: bool = False,
) -> AppState:
    """
    Get default starting state for the application

    Parameters
    ----------
    start_values
        Intitial values for country, category and entity.

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

    combined_ds = combined_ds.drop_vars("provenance")

    country_name_iso_mapping = get_country_options(combined_ds)
    country_dropdown_options = tuple(sorted(country_name_iso_mapping.keys()))

    category_options = tuple(combined_ds["category (IPCC2006_PRIMAP)"].to_numpy())

    entity_options = tuple(i for i in combined_ds.data_vars)

    source_scenario_options = tuple(combined_ds["SourceScen"].to_numpy())

    app_state = AppState(
        country_options=country_dropdown_options,
        country_name_iso_mapping=country_name_iso_mapping,
        country_index=country_dropdown_options.index(start_values["country"]),
        category_options=category_options,
        category_index=category_options.index(start_values["category"]),
        entity_options=entity_options,
        entity_index=entity_options.index(start_values["entity"]),
        source_scenario_options=source_scenario_options,
        source_scenario_index=source_scenario_options.index(
            start_values["source_scenario"]
        ),
        ds=combined_ds,
    )

    return app_state


@callback(  # type: ignore
    Output(
        "dropdown-country",
        "value",
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
    Output("dropdown-source-scenario", "options"),
    Output("dropdown-source-scenario", "value"),
    Output("memory", "data"),
    Input("dropdown-country", "value"),
    Input("dropdown-category", "value"),
    Input("dropdown-entity", "value"),
    State("dropdown-source-scenario", "value"),
    State("memory", "data"),
)
def update_source_scenario_dropdown(  # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
    memory_data: dict[str, int],
    app_state: AppState | None = None,
) -> tuple[tuple[str, ...], str, dict[str, int]]:
    """
    Update source scenario options in dropdown and, if necessary, source scenario value in dropdown.

    Parameters
    ----------
    country
        The currently selected country in the dropdown menu

    category
        The currently selected category in the dropdown menu

    entity
        The currently selected entity in the dropdown menu

    source_scenario
        The currently selected source scenario option.

    memory_data
        Data stored in browser memory.

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
    New source scenario dropdown options, source scenario value and browser memory state
    """
    if app_state is None:
        app_state = APP_STATE

    if any(v is None for v in (country, category, entity, source_scenario)):
        # User cleared one of the selections in the dropdown, do nothing
        return (
            app_state.source_scenario_options,
            app_state.source_scenario,
            memory_data,
        )

    app_state.update_all_indexes(country, category, entity, source_scenario)

    if not memory_data:
        memory_data = {"_": 0}
    else:
        memory_data["_"] += 1

    return (
        app_state.source_scenario_options,
        app_state.source_scenario,
        memory_data,
    )


@callback(  # type: ignore
    Output("graph-overview", "figure"),
    State("dropdown-country", "value"),
    State("dropdown-category", "value"),
    State("dropdown-entity", "value"),
    Input("memory", "data"),
)
def update_overview_graph(
    country: str,
    category: str,
    entity: str,
    memory_data: dict[str, int],
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

    memory_data
        Data stored in browser memory.

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

    return app_state.update_main_figure()


@callback(  # type: ignore
    Output("graph-category-split", "figure"),
    State("dropdown-country", "value"),
    State("dropdown-category", "value"),
    State("dropdown-entity", "value"),
    Input("dropdown-source-scenario", "value"),
    Input("memory", "data"),
    Input("graph-overview", "relayoutData"),
)
def update_category_graph(  # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
    memory_data: dict[str, int],
    layout_data: dict[str, list[str]],
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

    source_scenario
        The currently selected source-scenario in the dropdown menu

    memory_data
        Data stored in browser memory.

    layout_data
        The information about the main figure's layout.

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Category figure.
    """
    if app_state is None:
        app_state = APP_STATE

    # when the second condition is not met, the overview graph uses automatic x range values
    # That's the case when the app starts -> we don't want to update the other figures then
    if (ctx.triggered_id == "graph-overview") and ("xaxis.range" in layout_data):
        return app_state.update_category_xrange(layout_data)

    if any(v is None for v in (country, category, entity, source_scenario)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.category_graph

    app_state.source_scenario_index = app_state.source_scenario_options.index(
        source_scenario
    )

    return app_state.update_category_figure()


@callback(  # type: ignore
    Output("graph-entity-split", "figure"),
    State("dropdown-country", "value"),
    State("dropdown-category", "value"),
    State("dropdown-entity", "value"),
    Input("dropdown-source-scenario", "value"),
    Input("memory", "data"),
    Input("graph-overview", "relayoutData"),
)
def update_entity_graph(  # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
    memory_data: dict[str, int],
    layout_data: dict[str, list[str]],
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

    source_scenario
        The currently selected source-scenario in the dropdown menu

    memory_data
        Data stored in browser memory.

    layout_data
        The information about the main figure's layout.

    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.

    Returns
    -------
        Entity figure.
    """
    if app_state is None:
        app_state = APP_STATE

    # when the second condition is not met, the overview graph uses automatic x-range values
    # That's the case when the app starts -> we don't want to update the other figures then
    if (ctx.triggered_id == "graph-overview") and ("xaxis.range" in layout_data):
        return app_state.update_entity_xrange(layout_data)

    if any(v is None for v in (country, category, entity, source_scenario)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.entity_graph

    app_state.source_scenario_index = app_state.source_scenario_options.index(
        source_scenario
    )

    return app_state.update_entity_figure()


if __name__ == "__main__":
    APP_STATE = get_default_app_starting_state(test_ds=True)

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
                            dcc.Store(id="memory"),
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
                            html.H4(
                                children="Source-Scenario",
                                style={"textAlign": "center"},
                            ),
                            dcc.Dropdown(
                                APP_STATE.source_scenario_options,
                                value=APP_STATE.source_scenario,
                                id="dropdown-source-scenario",
                            ),
                            html.Br(),
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
