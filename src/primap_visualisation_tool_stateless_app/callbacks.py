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
    get_country_note_from_notes_db,
    get_note_save_confirmation_string,
    save_country_note_in_notes_db,
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
        db_filepath: str | None = None,
    ) -> str:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if db_filepath is None:
            db_filepath = get_application_notes_db_filepath()

        new_country = update_dropdown_within_context(
            value_current=dropdown_country_current,
            options=get_country_options(app_dataset),
            context=ctx,
        )

        return new_country

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
        Output("country-dropdown-store", "data"),
        State("input-for-notes", "value"),
        State("country-dropdown-store", "data"),
        Input("save-button", "n_clicks"),
        Input("dropdown-country", "value"),
        # Input("memory", "data"),
        prevent_initial_call=True,
    )  # type:ignore
    def save_note(
        notes_value: str,
        country_stored: dict[str, str],
        save_button_clicks: int,
        dropdown_country_current: str,
        db_filepath: str | None = None,
    ) -> tuple[str, str, dict[str, str]]:
        if db_filepath is None:
            db_filepath = get_application_notes_db_filepath()

        if not country_stored:
            country_stored = {"country": dropdown_country_current}

        if ctx.triggered_id == "dropdown-country":
            note_saved_div, input_field_value = save_note_after_dropdown_country_change(
                notes_value=notes_value,
                country_before_dropdown_change=country_stored["country"],
                country_current=dropdown_country_current,
                db_filepath=db_filepath,
            )

            country_stored["country"] = dropdown_country_current

            return (note_saved_div, input_field_value, country_stored)

        if not notes_value:
            # User hit save with no input (e.g. at initial callback),
            # hence do nothing.
            return "", "", country_stored

        save_country_note_in_notes_db(
            db_filepath=db_filepath,
            country=dropdown_country_current,
            note=notes_value,
        )

        return (
            get_note_save_confirmation_string(db_filepath, dropdown_country_current),
            notes_value,
            country_stored,
        )


def save_note_after_dropdown_country_change(
    notes_value: str,
    country_before_dropdown_change: str,
    country_current: str,
    db_filepath: str,
) -> tuple[str, str]:
    if not notes_value:
        note_saved_info = ""

    else:
        current_country_notes_value_in_db = get_country_note_from_notes_db(
            db_filepath=db_filepath, country=country_before_dropdown_change
        )

        if notes_value == current_country_notes_value_in_db:
            # The note has already been saved, don't need to do anything more
            note_saved_info = "Note already saved, input field cleared"

        else:
            # Note differs, hence must save first
            save_country_note_in_notes_db(
                db_filepath=db_filepath,
                country=country_before_dropdown_change,
                note=notes_value,
            )
            note_saved_info = ". ".join(
                [
                    "WARNING: notes weren't saved before changing country, we have saved the notes for you",
                    get_note_save_confirmation_string(
                        db_filepath=db_filepath, country=country_before_dropdown_change
                    ),
                ]
            )

    new_country_notes_value_in_db = get_country_note_from_notes_db(
        db_filepath=db_filepath, country=country_current
    )
    if new_country_notes_value_in_db is None:
        new_input_for_notes_value = ""
    else:
        new_input_for_notes_value = new_country_notes_value_in_db
        msg = f"Loaded existing notes for {country_current}"
        if note_saved_info:
            note_saved_info = ". ".join([note_saved_info, msg])
        else:
            note_saved_info = msg

    return note_saved_info, new_input_for_notes_value
