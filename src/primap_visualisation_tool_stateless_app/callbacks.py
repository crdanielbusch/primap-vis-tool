"""
Callback definitions
"""
from __future__ import annotations

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
    get_country_options,
    get_entity_options,
)
from primap_visualisation_tool_stateless_app.dataset_holder import (
    get_application_dataset,
)
from primap_visualisation_tool_stateless_app.figures import create_overview_figure
from primap_visualisation_tool_stateless_app.notes import (
    get_application_notes_db_filepath,
    get_note_save_confirmation_string,
    get_notes_db_cursor,
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

    @app.callback(
        Output("note-saved-div", "children"),
        Output("input-for-notes", "value"),
        Input("save-button", "n_clicks"),
        # Input("memory", "data"),
        Input("dropdown-country", "value"),
        State("input-for-notes", "value"),
    )  # type:ignore
    def save_note(
        save_button_clicks: int,
        country: str,
        notes_value: str,
        db_filepath: str | None = None,
    ) -> tuple[str, str]:
        if db_filepath is None:
            db_filepath = get_application_notes_db_filepath()

        # TODO: split this if block out into its own function
        if ctx.triggered_id == "dropdown-country":
            if notes_value:
                # TODO: think about best behaviour here,
                # need to avoid losing notes without being annoying.
                msg = "Notes should be empty before changing country!"
                raise AssertionError(msg)

            with get_notes_db_cursor(db_filepath=db_filepath) as db_cursor:
                # I would abstract out the raw SQL, but doing it like this for learning purposes
                found_new_country = db_cursor.execute(
                    f"SELECT notes FROM country_notes WHERE country='{country}'"
                ).fetchall()

            if len(found_new_country) > 1:
                msg = "Should only be one entry per country"
                raise AssertionError(msg)

            if not found_new_country:
                # Nothing already in the database, do nothing
                return "", ""

            existing_notes = found_new_country[0]
            if len(existing_notes) != 1:
                msg = f"Number of notes isn't 1, received {len(existing_notes)=}"
                raise AssertionError(msg)

            return f"Loaded existing note for {country}", existing_notes[0]

        if not notes_value:
            # No input (e.g. at initial callback), hence do nothing
            return "", ""

        # Save the note
        with get_notes_db_cursor(db_filepath=db_filepath) as db_cursor:
            existing_country = db_cursor.execute(
                f"SELECT notes FROM country_notes WHERE country='{country}'"
            ).fetchall()

            if existing_country:
                db_cursor.execute(
                    f"UPDATE country_notes SET notes='{notes_value}' WHERE country='{country}'"
                )
            else:
                # I would abstract out the raw SQL, but doing it like this for learning purposes
                db_cursor.execute(
                    "INSERT INTO country_notes VALUES(?, ?)", (country, notes_value)
                )

        # Confirm save to the user
        return get_note_save_confirmation_string(db_filepath, country), notes_value
