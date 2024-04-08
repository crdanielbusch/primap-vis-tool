"""
Callback definitions
"""
from __future__ import annotations

import plotly.graph_objects as go  # type: ignore
import xarray as xr
from dash import (
    Dash,  # type: ignore
    Input,
    Output,
    State,
    ctx,
)

from primap_visualisation_tool_stateless_app.dataset_handling import (
    get_category_options,
    get_country_options,
)
from primap_visualisation_tool_stateless_app.dataset_holder import (
    get_application_dataset,
)
from primap_visualisation_tool_stateless_app.figures import create_overview_figure


def register_callbacks(app: Dash) -> None:
    """
    Register callbacks onto an app

    Parameters
    ----------
    app
        App with which to register the callbacks
    """

    @app.callback(
        Output("dropdown-country", "value"),
        State("dropdown-country", "value"),
        Input("next_country", "n_clicks"),
        Input("prev_country", "n_clicks"),
    )
    def update_dropdown_country(
        dropdown_country_current: str,
        n_clicks_next_country: int,
        n_clicks_previous_country: int,
        app_dataset: xr.Dataset | None = None,
    ) -> str:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if ctx.triggered_id is None:
            # Start up, just return the initial state
            return dropdown_country_current

        country_options = get_country_options(app_dataset)
        # Probably want to split this logic out so we can re-use over
        # different dropdowns.
        current_index = country_options.index(dropdown_country_current)
        if ctx.triggered_id == "next_country":
            # n_clicks_next_country is the number of clicks since the app started
            # We don't wnat that, just whether we need to go forwards or backwards.
            # We might want to do this differently in future for performance maybe.
            # For further discussion on possible future directions,
            # see https://github.com/crdanielbusch/primap-vis-tool/pull/4#discussion_r1444363726
            increment = 1

        elif ctx.triggered_id == "prev_country":
            increment = -1

        else:  # pragma: no cover
            # Should be impossible to get here
            msg = f"How did you get here? {ctx=}"
            raise AssertionError(msg)

        new_index = (current_index + increment) % len(country_options)

        return country_options[new_index]

    @app.callback(
        Output("dropdown-category", "value"),
        State("dropdown-category", "value"),
        Input("next_category", "n_clicks"),
        Input("prev_category", "n_clicks"),
    )
    def update_dropdown_category(
        dropdown_category_current: str,
        n_clicks_next_category: int,
        n_clicks_previous_category: int,
        app_dataset: xr.Dataset | None = None,
    ) -> str:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if ctx.triggered_id is None:
            # Start up, just return the initial state
            return dropdown_category_current

        category_options = get_category_options(app_dataset)
        # Probably want to split this logic out so we can re-use over
        # different dropdowns.
        current_index = category_options.index(dropdown_category_current)
        if ctx.triggered_id == "next_category":
            increment = 1

        elif ctx.triggered_id == "prev_category":
            increment = -1

        else:  # pragma: no cover
            # Should be impossible to get here
            msg = f"How did you get here? {ctx=}"
            raise AssertionError(msg)

        new_index = (current_index + increment) % len(category_options)

        return category_options[new_index]

    @app.callback(  # type: ignore
        Output("graph-overview", "figure"),
        Input("dropdown-country", "value"),
        Input("dropdown-category", "value"),
        Input("dropdown-entity", "value"),
        State("graph-overview", "figure"),
        # Input("memory", "data"),
        # Input("xyrange-overview", "data"),
    )
    def update_overview_figure(
        country: str,
        category: str,
        entity: str,
        graph_figure_current: go.Figure,
        # memory_data: dict[str, int],
        # xyrange_data: str | None,
        app_dataset: xr.Dataset | None = None,
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
            A variable stored in the browser that changes whenever country, category or entity changes.
            It is needed to execute the callbacks sequentially.
            The actual values are irrelevant for the app.

        app_dataset
            The app dataset to use. If not provided, we use get_app_dataset()

        Returns
        -------
            Overview figure.
        """
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if any(v is None for v in (country, category, entity)):
            # User cleared one of the selections in the dropdown, do nothing
            return graph_figure_current

        # if ctx.triggered_id == "xyrange-overview" and xyrange_data:
        #    return app_state.update_overview_range(xyrange_data)

        return create_overview_figure(
            country=country, category=category, entity=entity, dataset=app_dataset
        )
