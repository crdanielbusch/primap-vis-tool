"""
Launch plotly app.

Author: Daniel Busch, Date: 2023-12-21
"""
from __future__ import annotations

from typing import Any

import dash_ag_grid as dag  # type: ignore
import dash_bootstrap_components as dbc  # type: ignore
import plotly.graph_objects as go  # type: ignore
import pycountry
import xarray as xr
from dash import Dash, Input, Output, State, callback, ctx, dcc, html  # type: ignore
from dash.exceptions import PreventUpdate  # type: ignore

from primap_visualisation_tool.app_state import APP_STATE, AppState


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


def get_filename(
    user_input: str | None,
    test_ds: bool = False,
    current_version: str = "v2.5_final",
    old_version: str = "v2.4.2_final",
    test_ds_name: str = "test_ds.nc",
) -> str:
    """
    Get the filename of the dataset.

    Parameters
    ----------
    user_input
        The filename from the command line.

    test_ds
        Should we load a test dataset instead? This is much
        faster to load.

    current_version
        Current version of PRIMAP-hist to inspect

    old_version
        Previous version of PRIMAP-hist to compare against

    Returns
    -------
        Filename. The name of the data set to read in.
    """
    if user_input:
        return user_input
    elif test_ds:
        return test_ds_name
    else:
        return f"combined_data_{current_version}_{old_version}.nc"


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
        # We don't want that, just whether we need to go forwards or backwards.
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
        A variable stored in the browser that changes whenever country, category or entity changes.
        It is needed to execute the callbacks sequentially. The actual values are irrelevant for the app.

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
    Input("xyrange-overview", "data"),
)
def update_overview_graph(  # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    memory_data: dict[str, int],
    xyrange_data: str | None,
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
        A variable stored in the browser that changes whenever country, category or entity changes.
        It is needed to execute the callbacks sequentially. The actual values are irrelevant for the app.

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Overview figure.
    """
    print("Called the overview graph update callback")
    if app_state is None:
        app_state = APP_STATE

    if any(v is None for v in (country, category, entity)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.overview_graph

    if ctx.triggered_id == "xyrange-overview" and xyrange_data:
        return app_state.update_overview_range(xyrange_data)

    return app_state.update_overview_figure(xyrange_data)


@callback(  # type: ignore
    Output("graph-category-split", "figure"),
    State("dropdown-country", "value"),
    State("dropdown-category", "value"),
    State("dropdown-entity", "value"),
    Input("dropdown-source-scenario", "value"),
    Input("memory", "data"),
    Input("xyrange-category", "data"),
    State("xyrange-entity", "data"),
)
def update_category_graph(  # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
    memory_data: dict[str, int],
    xyrange_data: str | None,
    xyrange_data_entity: str | None,
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
        A variable stored in the browser that changes whenever country, category or entity changes.
        It is needed to execute the callbacks sequentially. The actual values are irrelevant for the app.

    xyrange_data
        X- and y-axis range to which the category figure is to be updated.

    xyrange_data_entity
        X- and y-axis range to which the entity figure is to be updated.

    app_state
        The app state to update. If not provided, we use `APP_STATE` i.e.
        the value from the global namespace.

    Returns
    -------
        Category figure.
    """
    if app_state is None:
        app_state = APP_STATE

    if ctx.triggered_id == "xyrange-category" and xyrange_data:
        return app_state.update_category_range(xyrange_data)

    if any(v is None for v in (country, category, entity, source_scenario)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.category_graph

    app_state.source_scenario_index = app_state.source_scenario_options.index(
        source_scenario
    )

    # in case user adjusts category figure layout
    # and then changes country, category or entity
    if not xyrange_data:
        xyrange_data = xyrange_data_entity

    return app_state.update_category_figure(xyrange_data)


@callback(  # type: ignore
    Output("graph-entity-split", "figure"),
    State("dropdown-country", "value"),
    State("dropdown-category", "value"),
    State("dropdown-entity", "value"),
    Input("dropdown-source-scenario", "value"),
    Input("memory", "data"),
    Input("xyrange-entity", "data"),
    State("xyrange-category", "data"),
)
def update_entity_graph(  # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
    memory_data: dict[str, int],
    xyrange_data: str | None,
    xyrange_data_category: str | None,
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
        A variable stored in the browser that changes whenever country, category or entity changes.
        It is needed to execute the callbacks sequentially. The actual values are irrelevant for the app.

    xyrange_data
        X- and y-axis range to which the category figure is to be updated.

    xyrange_data_category
        X- and y-axis range to which the category figure is to be updated.

    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.

    Returns
    -------
        Entity figure.
    """
    if app_state is None:
        app_state = APP_STATE

    if ctx.triggered_id == "xyrange-entity" and xyrange_data:
        return app_state.update_entity_range(xyrange_data)

    if any(v is None for v in (country, category, entity, source_scenario)):
        # User cleared one of the selections in the dropdown, do nothing
        return app_state.entity_graph

    app_state.source_scenario_index = app_state.source_scenario_options.index(
        source_scenario
    )

    # in case user adjusts category figure layout
    # and then changes country, category or entity
    if not xyrange_data:
        xyrange_data = xyrange_data_category

    return app_state.update_entity_figure(xyrange_data)


@callback(  # type: ignore
    Output("memory_visible_lines", "data"),
    Input("graph-overview", "restyleData"),
    State("graph-overview", "figure"),
    prevent_initial_call=True,
)
def update_visible_lines_dict(
    legend_value: list[Any],
    figure_data: dict[str, Any],
    app_state: AppState | None = None,
) -> None:
    """
    Update which lines are selected in the legend of overview plot.

    Parameters
    ----------
    legend_value
        Information about which line was clicked in legend
    figure_data
        The overview plot
    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.
    """
    if app_state is None:
        app_state = APP_STATE

    app_state.update_source_scenario_visible(legend_value, figure_data)


@callback(  # type: ignore
    Output("grid", "rowData"),
    Output("grid", "columnDefs"),
    Input("memory", "data"),
)
def update_table(
    memory_data: dict[str, int],
    app_state: AppState | None = None,
) -> tuple[list[dict[str, object]], Any]:
    """
    Update the table when dropdown selection changes.

    Parameters
    ----------
    memory_data
        A variable stored in the browser that changes whenever country, category or entity changes.
        It is needed to execute the callbacks sequentially. The actual values are irrelevant for the app.
    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.

    Returns
    -------
        Data to show in table and column specifications

    """
    if app_state is None:
        app_state = APP_STATE

    return (app_state.get_row_data(), app_state.get_column_defs())


@callback(  # type: ignore
    Output(
        "note-saved-div",
        "children",
    ),
    Output("input-for-notes", "value"),
    Input("save_button", "n_clicks"),
    Input("memory", "data"),
    State("input-for-notes", "value"),
)
def save_note(
    save_button_clicks: int,
    memory_data: dict[str, int],
    text_input: str,
    app_state: AppState | None = None,
) -> tuple[str, str]:
    """
    Save a note and app_state to disk.

    Parameters
    ----------
    save_button_clicks
        The number of clicks on the save button to trigger the callback.
    memory_data
        A variable stored in the browser that changes whenever country, category or entity changes.
        It is needed to execute the callbacks sequentially. The actual values are irrelevant for the app.
    text_input
        The note from the user in the input field.
    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.

    Returns
    -------
        A text to let the user know the note was saved.

    """
    if app_state is None:
        app_state = APP_STATE

    # Do nothing when Input is empty (initial callback) or
    # clear input when memory variable changes
    # (triggered by change country or category or entity)
    if not text_input or ctx.triggered_id == "memory":
        return "", ""

    app_state.save_note_to_csv(text_input)

    return (app_state.get_notification(), text_input)


@callback(  # type: ignore
    Output("xyrange-overview", "data"),
    Input("graph-overview", "relayoutData"),
    Input("graph-category-split", "relayoutData"),
    Input("graph-entity-split", "relayoutData"),
    State("graph-overview", "figure"),
    State("graph-category-split", "figure"),
    State("graph-entity-split", "figure"),
)
def update_xyrange_overview_figure(  # noqa: PLR0913 PLR0912
    layout_data_overview: dict[str, Any],
    layout_data_category: dict[str, Any],
    layout_data_entity: dict[str, Any],
    figure_overview_dict: dict[str, Any],
    figure_category_dict: dict[str, Any],
    figure_entity_dict: dict[str, Any],
    app_state: AppState | None = None,
) -> str:
    """
    Set the x- and y-range of overview figure according to category or entity figure.

    Parameters
    ----------
    layout_data_overview
        Information how the user interacted with the layout options in the overview figure.
    layout_data_category
        Information how the user interacted with the layout options in the category figure.
    layout_data_entity
        Information how the user interacted with the layout options in the entity figure.
    figure_overview_dict
        The overview figure as dictionary.
    figure_category_dict
        The category figure as dictionary.
    figure_entity_dict
        The entity figure as dictionary.
    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.

    Returns
    -------
        The x- and y-limits to which the overview figure is updated.
    """
    if app_state is None:
        app_state = APP_STATE

    if any(
        v is None
        for v in (
            layout_data_overview,
            layout_data_category,
            layout_data_entity,
            figure_overview_dict,
            figure_category_dict,
            figure_entity_dict,
        )
    ):
        raise PreventUpdate

    if ctx.triggered_id == "graph-overview":
        # User changes rangeslider selection in overview figure
        if "xaxis.range" in layout_data_overview:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_overview_dict,
                y_source_figure=figure_overview_dict,
                autorange=False,
            )
        elif "xaxis.autorange" in layout_data_overview:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_overview_dict,
                y_source_figure=figure_overview_dict,
                autorange=True,
            )
        else:
            raise PreventUpdate
    elif ctx.triggered_id == "graph-category-split":
        if (
            all(
                keys in layout_data_category
                for keys in ("xaxis.range[0]", "xaxis.range[1]")
            )
        ) or (
            all(
                keys in layout_data_category
                for keys in ("yaxis.range[0]", "yaxis.range[1]")
            )
        ):
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_category_dict,
                y_source_figure=figure_category_dict,
                autorange=False,
            )
        elif "xaxis.autorange" in layout_data_category:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_category_dict,
                y_source_figure=figure_category_dict,
                autorange=True,
            )
        else:
            raise PreventUpdate
    elif ctx.triggered_id == "graph-entity-split":
        if (
            all(
                keys in layout_data_entity
                for keys in ("xaxis.range[0]", "xaxis.range[1]")
            )
        ) or (
            all(
                keys in layout_data_entity
                for keys in ("yaxis.range[0]", "yaxis.range[1]")
            )
        ):
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_entity_dict,
                y_source_figure=figure_entity_dict,
                autorange=False,
            )
        elif "xaxis.autorange" in layout_data_entity:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_entity_dict,
                y_source_figure=figure_entity_dict,
                autorange=True,
            )
        else:
            raise PreventUpdate


@callback(  # type: ignore
    Output("xyrange-category", "data"),
    Input("graph-overview", "relayoutData"),
    # Input("graph-category-split", "relayoutData"),
    Input("graph-entity-split", "relayoutData"),
    State("graph-overview", "figure"),
    State("graph-category-split", "figure"),
    State("graph-entity-split", "figure"),
)
def update_xyrange_category_figure(  # noqa: PLR0913
    layout_data_overview: dict[str, Any],
    layout_data_entity: dict[str, Any],
    figure_overview_dict: dict[str, Any],
    figure_category_dict: dict[str, Any],
    figure_entity_dict: dict[str, Any],
    app_state: AppState | None = None,
) -> str:
    """
    Set the x- and y-range of category figure according to overview or entity figure.

    Parameters
    ----------
    layout_data_overview
        Information how the user interacted with the layout options in the overview figure.
    layout_data_entity
        Information how the user interacted with the layout options in the entity figure.
    figure_overview_dict
        The overview figure as dictionary.
    figure_category_dict
        The category figure as dictionary.
    figure_entity_dict
        The entity figure as dictionary.
    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.

    Returns
    -------
        The x- and y-limits to which the category figure is updated.
    """
    if app_state is None:
        app_state = APP_STATE

    if any(
        v is None
        for v in (
            layout_data_overview,
            layout_data_entity,
            figure_overview_dict,
            figure_category_dict,
            figure_entity_dict,
        )
    ):
        raise PreventUpdate

    elif ctx.triggered_id == "graph-overview":
        if (
            all(
                keys in layout_data_overview
                for keys in ("xaxis.range[0]", "xaxis.range[1]")
            )
        ) or ("xaxis.range" in layout_data_overview):
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_overview_dict,
                y_source_figure=figure_category_dict,  # note that Y is from the category plot
                autorange=False,
            )
        elif "xaxis.autorange" in layout_data_overview:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_overview_dict,
                y_source_figure=figure_category_dict,
                autorange=True,
            )
        else:
            raise PreventUpdate
    elif ctx.triggered_id == "graph-entity-split":
        if (
            all(
                keys in layout_data_entity
                for keys in ("xaxis.range[0]", "xaxis.range[1]")
            )
        ) or (
            all(
                keys in layout_data_entity
                for keys in ("yaxis.range[0]", "yaxis.range[1]")
            )
        ):
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_entity_dict,
                y_source_figure=figure_entity_dict,
                autorange=False,
            )
        elif "xaxis.autorange" in layout_data_entity:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_entity_dict,
                y_source_figure=figure_entity_dict,
                autorange=True,
            )
        else:
            raise PreventUpdate


@callback(  # type: ignore
    Output("xyrange-entity", "data"),
    Input("graph-overview", "relayoutData"),
    Input("graph-category-split", "relayoutData"),
    State("graph-overview", "figure"),
    State("graph-category-split", "figure"),
    State("graph-entity-split", "figure"),
)
def update_xyrange_entity_figure(  # noqa: PLR0913
    layout_data_overview: dict[str, Any],
    layout_data_category: dict[str, Any],
    figure_overview_dict: dict[str, Any],
    figure_category_dict: dict[str, Any],
    figure_entity_dict: dict[str, Any],
    app_state: AppState | None = None,
) -> str:
    """
    Set the x- and y-range of category figure according to overview or entity figure.

    Parameters
    ----------
    layout_data_overview
        Information how the user interacted with the layout options in the overview figure.
    layout_data_category
        Information how the user interacted with the layout options in the category figure.
    figure_overview_dict
        The overview figure as dictionary.
    figure_category_dict
        The category figure as dictionary.
    figure_entity_dict
        The entity figure as dictionary.
    app_state
        Application state. If not provided, we use `APP_STATE` from the global namespace.

    Returns
    -------
        The x- and y-limits to which the category figure is updated.
    """
    if app_state is None:
        app_state = APP_STATE

    if any(
        v is None
        for v in (
            layout_data_overview,
            layout_data_category,
            figure_overview_dict,
            figure_category_dict,
            figure_entity_dict,
        )
    ):
        raise PreventUpdate

    if ctx.triggered_id == "graph-overview":
        if all(
            keys in layout_data_overview
            for keys in ("xaxis.range[0]", "xaxis.range[1]")
        ) or ("xaxis.range" in layout_data_overview):
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_overview_dict,
                y_source_figure=figure_entity_dict,  # note that Y is from the category plot
                autorange=False,
            )
        elif "xaxis.autorange" in layout_data_overview:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_overview_dict,
                y_source_figure=figure_entity_dict,
                autorange=True,
            )
        else:
            raise PreventUpdate
    elif ctx.triggered_id == "graph-category-split":
        if all(
            keys in layout_data_category
            for keys in ("xaxis.range[0]", "xaxis.range[1]")
        ) or all(
            keys in layout_data_category
            for keys in ("yaxis.range[0]", "yaxis.range[1]")
        ):
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_category_dict,
                y_source_figure=figure_category_dict,
                autorange=False,
            )
        elif "xaxis.autorange" in layout_data_category:
            return app_state.get_xyrange_from_figure(
                x_source_figure=figure_category_dict,
                y_source_figure=figure_category_dict,
                autorange=True,
            )
        else:
            raise PreventUpdate


def create_app(app_state: AppState) -> Dash:
    """
    Create an instance of the app

    Parameters
    ----------
    app_state
        The starting app state to use

    Returns
    -------
        App instance
    """
    # Hack the global namespace, not ideal but ok
    external_stylesheets = [dbc.themes.SIMPLEX]

    # Tell dash that we're using bootstrap for our external stylesheets so
    # that the Col and Row classes function properly
    app = Dash(__name__, external_stylesheets=external_stylesheets)

    # define layout
    # to be adjusted once everything is running
    app.layout = dbc.Container(
        [
            dbc.Row(  # first row
                [
                    dbc.Col(  # first column with dropdown menus
                        dbc.Stack(
                            [
                                dcc.Store(id="memory"),  # invisible
                                dcc.Store(
                                    id="memory_visible_lines",
                                    data=app_state.source_scenario_visible,
                                ),
                                dcc.Store(id="xyrange-overview"),
                                dcc.Store(id="xyrange-category"),
                                dcc.Store(id="xyrange-entity"),
                                html.B(
                                    children="Country",
                                    style={"textAlign": "left", "fontSize": 14},
                                ),
                                dcc.Dropdown(
                                    options=app_state.country_options,
                                    value=app_state.country,
                                    id="dropdown-country",
                                ),
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            id="prev_country",
                                            children="prev country",
                                            color="light",
                                            n_clicks=0,
                                            style={
                                                "fontSize": 12,
                                                "height": "37px",
                                            },
                                        ),
                                        dbc.Button(
                                            id="next_country",
                                            children="next country",
                                            color="light",
                                            n_clicks=0,
                                            style={
                                                "fontSize": 12,
                                                "height": "37px",
                                            },
                                        ),
                                    ]
                                ),
                                html.B(
                                    children="Category",
                                    style={
                                        "textAlign": "left",
                                        "fontSize": 14,
                                        "margin-top": 20,  # distance to element above
                                    },
                                ),
                                dcc.Dropdown(
                                    app_state.category_options,
                                    value=app_state.category,
                                    id="dropdown-category",
                                ),
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            id="prev_category",
                                            children="prev category",
                                            color="light",
                                            n_clicks=0,
                                            style={
                                                "fontSize": 12,
                                                "height": "37px",
                                            },
                                        ),
                                        dbc.Button(
                                            id="next_category",
                                            children="next category",
                                            color="light",
                                            n_clicks=0,
                                            style={
                                                "fontSize": 12,
                                                "height": "37px",
                                            },
                                        ),
                                    ]
                                ),
                                html.B(
                                    children="Entity",
                                    style={
                                        "textAlign": "left",
                                        "fontSize": 14,
                                        "margin-top": 20,
                                    },
                                ),
                                dcc.Dropdown(
                                    app_state.entity_options,
                                    value=app_state.entity,
                                    id="dropdown-entity",
                                ),
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            id="prev_entity",
                                            children="prev entity",
                                            color="light",
                                            n_clicks=0,
                                            style={
                                                "fontSize": 12,
                                                "height": "37px",
                                            },
                                        ),
                                        dbc.Button(
                                            id="next_entity",
                                            children="next entity",
                                            color="light",
                                            n_clicks=0,
                                            style={
                                                "fontSize": 12,
                                                "height": "37px",
                                            },
                                        ),
                                    ]
                                ),
                                html.B(
                                    children="Source-Scenario",
                                    style={
                                        "textAlign": "left",
                                        "fontSize": 14,
                                        "marginTop": 20,
                                    },
                                ),
                                dcc.Dropdown(
                                    app_state.source_scenario_options,
                                    value=app_state.source_scenario,
                                    id="dropdown-source-scenario",
                                ),
                            ],
                            gap=1,  # spacing between each item (0 - 5)
                        ),
                        width=2,  # Column will span this many of the 12 grid columns
                        style={"fontSize": 14},
                    ),
                    dbc.Col(
                        dbc.Stack(
                            [
                                html.B(
                                    children="Notes",
                                    style={"textAlign": "left", "fontSize": 14},
                                ),
                                dcc.Textarea(
                                    id="input-for-notes",
                                    placeholder="Add notes and press save..",
                                    style={"width": "100%"},
                                    rows=8,  # used to define height of text area
                                ),
                                dbc.Button(
                                    children="Save",
                                    id="save_button",
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
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                id="select-AR4GWP100",
                                                children="AR4GWP100",
                                                color="light",
                                                n_clicks=0,
                                                style={
                                                    "fontSize": 12,
                                                    "height": "37px",
                                                },
                                            ),
                                            width=6,
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                id="select-AR5GWP100",
                                                children="AR5GWP100",
                                                color="light",
                                                n_clicks=0,
                                                style={
                                                    "fontSize": 12,
                                                    "height": "37px",
                                                },
                                            ),
                                            width=6,
                                        ),
                                    ]
                                ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            dbc.Button(
                                                id="select-AR6GWP100",
                                                children="AR6GWP100",
                                                color="light",
                                                n_clicks=0,
                                                style={
                                                    "fontSize": 12,
                                                    "height": "37px",
                                                },
                                            ),
                                            width=6,
                                        ),
                                        dbc.Col(
                                            dbc.Button(
                                                id="select-SARGWP100",
                                                children="SARGWP100",
                                                active=True,
                                                class_name="me-md-2",
                                                color="light",
                                                n_clicks=0,
                                                style={
                                                    "fontSize": 12,
                                                    "height": "37px",
                                                },
                                            ),
                                            width=4,
                                        ),
                                    ]
                                ),
                            ],
                            gap=1,
                        ),
                        width=2,
                    ),
                    dbc.Col(
                        [
                            html.B(children="Overview", style={"textAlign": "center"}),
                            dcc.Graph(id="graph-overview"),
                        ],
                        width=8,
                    ),
                ]
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Br(),
                            html.B(
                                children="Category split", style={"textAlign": "center"}
                            ),
                            dcc.Graph(id="graph-category-split"),
                        ],
                        width=6,
                    ),
                    dbc.Col(
                        [
                            html.Br(),
                            html.B(
                                children="Entity split", style={"textAlign": "center"}
                            ),
                            dcc.Graph(id="graph-entity-split"),
                        ],
                        width=6,
                    ),
                ]
            ),
            dbc.Row(
                dbc.Col(
                    dag.AgGrid(
                        id="grid",
                        columnDefs=[],
                        # continually resize columns to fit the width of the grid
                        columnSize="responsiveSizeToFit",
                        defaultColDef={"filter": "agTextColumnFilter"},
                        style={"marginTop": "5em"},
                    )
                )
            ),
        ],
        style={"max-width": "none", "width": "100%"},
    )

    return app
