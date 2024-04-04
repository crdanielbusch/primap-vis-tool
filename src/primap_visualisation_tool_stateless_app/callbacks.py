from dash import Input, Output, State, callback
import plotly.graph_objects as go  # type: ignore

@callback(  # type: ignore
    Output("graph-overview", "figure"),
    Input("dropdown-country", "value"),
    Input("dropdown-category", "value"),
    Input("dropdown-entity", "value"),
    # Input("memory", "data"),
    # Input("xyrange-overview", "data"),
)
def update_overview_figure(  # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    # memory_data: dict[str, int],
    # xyrange_data: str | None,
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