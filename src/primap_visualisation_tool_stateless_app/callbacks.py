"""
Callback definitions
"""
from __future__ import annotations

import warnings
from collections.abc import Sequence

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
    get_country_code_mapping,
    get_country_options,
    get_entity_options,
)
from primap_visualisation_tool_stateless_app.dataset_holder import (
    get_application_dataset,
)
from primap_visualisation_tool_stateless_app.figures import (
    create_category_figure,
    create_entity_figure,
    create_overview_figure,
)


def update_dropdown(value_current: str, options: Sequence[str], increment: int) -> str:
    """
    Update a dropdown a given number of increments

    Parameters
    ----------
    value_current
        The current value of the dropdown

    options
        The dropdown's options

    increment
        The number of increments to move the dropdown.

    Returns
    -------
        The updated value of the dropdown.
    """
    current_index = options.index(value_current)

    new_index = (current_index + increment) % len(options)

    return options[new_index]


def update_dropdown_within_context(
    value_current: str,
    options: Sequence[str],
    context: ctx,
) -> str:
    """
    Update a dropdown within a given context.

    Assumes that a ``context.triggered_id`` which starts with "next" means increment one forward,
    a ``context.triggered_id`` which starts with "prev" means increment one backwards.

    Parameters
    ----------
    value_current
        The current value of the dropdown

    options
        The dropdown's options

    context
        The context from Dash

    Returns
    -------
        The updated value to show in the dropdown
    """
    if context.triggered_id is None:
        # Start up, just return the initial state
        return value_current

    if context.triggered_id.startswith("next"):
        # n_clicks_next_country is the number of clicks since the app started
        # We don't wnat that, just whether we need to go forwards or backwards.
        # We might want to do this differently in future for performance maybe.
        # For further discussion on possible future directions,
        # see https://github.com/crdanielbusch/primap-vis-tool/pull/4#discussion_r1444363726
        increment = 1

    elif context.triggered_id.startswith("prev"):
        increment = -1

    else:  # pragma: no cover
        # Should be impossible to get here
        msg = f"How did you get here? {context=}"
        raise AssertionError(msg)

    return update_dropdown(
        value_current=value_current,
        options=options,
        increment=increment,
    )


def update_source_scenario_options(
    country: str,
    category: str,
    entity: str,
    dataset: xr.Dataset,
) -> tuple[str]:
    """
    Update the source scenario dropdown options according to country, category and entity

    """
    country_code_mapping = get_country_code_mapping(dataset)

    iso_country = country_code_mapping[country]

    with warnings.catch_warnings(action="ignore"):  # type: ignore
        filtered = (
            dataset[entity]
            .pr.loc[
                {
                    "category": category,
                    "area (ISO3)": iso_country,
                }
            ]
            .squeeze()
        )

    filtered_pandas = filtered.to_dataframe().reset_index()

    null_source_scenario_options = filtered_pandas.groupby(by="SourceScen")[
        entity
    ].apply(lambda x: x.isna().all())

    null_source_scenario_options = null_source_scenario_options[
        list(null_source_scenario_options)
    ].index

    original_source_scenario_options = tuple(dataset["SourceScen"].to_numpy())

    new_source_scenario_options = [
        i
        for i in original_source_scenario_options
        if i not in null_source_scenario_options
    ]

    # TODO I'm not sure if that's the bevior we want
    # how do we end up with no available option?
    if not new_source_scenario_options:
        return None

    return tuple(new_source_scenario_options)


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

        return update_dropdown_within_context(
            value_current=dropdown_country_current,
            options=get_country_options(app_dataset),
            context=ctx,
        )

    @app.callback(
        Output("dropdown-entity", "value"),
        State("dropdown-entity", "value"),
        Input("next_entity", "n_clicks"),
        Input("prev_entity", "n_clicks"),
    )
    def update_dropdown_entity(
        dropdown_entity_current: str,
        n_clicks_next_entity: int,
        n_clicks_previous_entity: int,
        app_dataset: xr.Dataset | None = None,
    ) -> str:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        return update_dropdown_within_context(
            value_current=dropdown_entity_current,
            options=get_entity_options(app_dataset),
            context=ctx,
        )

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

        return update_dropdown_within_context(
            value_current=dropdown_category_current,
            options=get_category_options(app_dataset),
            context=ctx,
        )

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

    @app.callback(  # type: ignore
        Output("dropdown-source-scenario", "options"),
        Output("dropdown-source-scenario", "value"),
        Output("memory", "data"),
        Input("dropdown-country", "value"),
        Input("dropdown-category", "value"),
        Input("dropdown-entity", "value"),
        State("dropdown-source-scenario", "value"),
        State("dropdown-source-scenario", "options"),
        State("memory", "data"),
    )
    def update_source_scenario_dropdown(  # noqa: PLR0913
        country: str,
        category: str,
        entity: str,
        source_scenario: str,
        source_scenario_options: list[str],
        memory_data: dict[str, int],
        app_dataset: xr.Dataset | None = None,
    ) -> tuple[tuple[str, ...], str, dict[str, int]]:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if any(v is None for v in (country, category, entity)):
            # User cleared one of the selections in the dropdown, do nothing
            return (
                source_scenario_options,
                source_scenario,
                memory_data,
            )

        source_scenario_options_out = update_source_scenario_options(
            country=country, category=category, entity=entity, dataset=app_dataset
        )

        if not memory_data:
            memory_data = {"_": 0}
        else:
            memory_data["_"] += 1

        if not source_scenario_options_out:
            return (
                source_scenario_options,
                source_scenario,
                memory_data,
            )

        if source_scenario in source_scenario_options_out:
            source_scenario_out = source_scenario
        else:
            source_scenario_out = source_scenario_options_out[0]

        return (
            source_scenario_options_out,
            source_scenario_out,
            memory_data,
        )

    @app.callback(  # type: ignore
        Output("graph-category-split", "figure"),
        State("graph-category-split", "figure"),
        State("dropdown-country", "value"),
        State("dropdown-category", "value"),
        State("dropdown-entity", "value"),
        Input("dropdown-source-scenario", "value"),
        Input("memory", "data"),
        # Input("xyrange-category", "data"),
        # State("xyrange-entity", "data"),
    )
    def update_category_figure(  # noqa: PLR0913
        graph_figure_current: go.Figure,
        country: str,
        category: str,
        entity: str,
        source_scenario: str,
        memory_data: dict[str, int],
        # xyrange_data: str | None,
        # xyrange_data_entity: str | None,
        app_dataset: xr.Dataset | None = None,
    ) -> go.Figure:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if any(v is None for v in (country, category, entity)):
            # User cleared one of the selections in the dropdown, do nothing
            return graph_figure_current

        return create_category_figure(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            dataset=app_dataset,
        )

    @app.callback(  # type: ignore
        Output("graph-entity-split", "figure"),
        State("graph-entity-split", "figure"),
        State("dropdown-country", "value"),
        State("dropdown-category", "value"),
        State("dropdown-entity", "value"),
        Input("dropdown-source-scenario", "value"),
        Input("memory", "data"),
        # Input("xyrange-entity", "data"),
        # State("xyrange-category", "data"),
    )
    def update_entity_graph(  # noqa: PLR0913
        graph_figure_current: go.Figure,
        country: str,
        category: str,
        entity: str,
        source_scenario: str,
        memory_data: dict[str, int],
        app_dataset: xr.Dataset | None = None,
        # xyrange_data: str | None,
        # xyrange_data_category: str | None,
    ) -> go.Figure:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        # if ctx.triggered_id == "xyrange-entity" and xyrange_data :
        #     return app_state.update_entity_range(xyrange_data)

        if any(v is None for v in (country, category, entity, source_scenario)):
            # User cleared one of the selections in the dropdown, do nothing
            return graph_figure_current

        # app_state.source_scenario_index = app_state.source_scenario_options.index(
        #     source_scenario
        # )

        # in case user adjusts category figure layout
        # and then changes country, category or entity
        # if not xyrange_data :
        #     xyrange_data = xyrange_data_category

        return create_entity_figure(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            dataset=app_dataset,
        )
