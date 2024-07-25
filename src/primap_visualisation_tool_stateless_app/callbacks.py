"""
Callback definitions
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Any

import plotly.graph_objects as go  # type: ignore
import xarray as xr
from dash import (  # type: ignore
    Dash,
    Input,
    Output,
    State,
    ctx,
)
from dash.dependencies import ALL  # type: ignore

import primap_visualisation_tool_stateless_app.notes.db_filepath_holder
from primap_visualisation_tool_stateless_app.dataset_handling import (
    get_category_options,
    get_country_code_mapping,
    get_country_options,
    get_entity_options,
    get_not_all_nan_source_scenario_dfs,
)
from primap_visualisation_tool_stateless_app.dataset_holder import (
    get_application_dataset,
)
from primap_visualisation_tool_stateless_app.figure_views import update_xy_range
from primap_visualisation_tool_stateless_app.figures import (
    create_category_figure,
    create_entity_figure,
    create_overview_figure,
)
from primap_visualisation_tool_stateless_app.notes import (
    get_country_notes_from_notes_db,
    get_note_save_confirmation_string,
    notes_db_cursor,
    save_country_notes_in_notes_db,
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


def update_dropdown_within_context(  # type: ignore
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
) -> tuple[str, ...] | None:
    """
    Update the source scenario dropdown options according to country, category and entity

    """
    country_code_mapping = get_country_code_mapping(dataset)

    iso_country = country_code_mapping[country]

    source_scenarios_with_data = get_not_all_nan_source_scenario_dfs(
        inp=dataset.pr.loc[
            {
                "category": category,
                "area (ISO3)": iso_country,
            }
        ],
        entity=entity,
    )

    new_source_scenario_options = list(source_scenarios_with_data.keys())

    if not new_source_scenario_options:
        return None

    return tuple(new_source_scenario_options)


def register_callbacks(app: Dash) -> None:  # type: ignore  # noqa: PLR0915
    """
    Register callbacks onto an app

    Parameters
    ----------
    app
        App with which to register the callbacks
    """

    @app.callback(  # type: ignore
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

        new_country = update_dropdown_within_context(
            value_current=dropdown_country_current,
            options=get_country_options(app_dataset),
            context=ctx,
        )

        return new_country

    @app.callback(  # type: ignore
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

    @app.callback(  # type: ignore
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
        Output(dict(name="graph-overview", type="graph"), "figure"),
        Input("dropdown-country", "value"),
        Input("dropdown-category", "value"),
        Input("dropdown-entity", "value"),
        Input("xyrange", "data"),
        State(dict(name="graph-overview", type="graph"), "figure"),
    )
    def update_overview_figure(  # noqa: PLR0913
        country: str,
        category: str,
        entity: str,
        xyrange: dict[str, int],
        figure_current: go.Figure,
        app_dataset: xr.Dataset | None = None,
    ) -> go.Figure:
        """
        Update the overview figure.

        Parameters
        ----------
        country
            The currently selected country in the dropdown menu

        category
            The currently selected category in the dropdown menu

        entity
            The currently selected entity in the dropdown menu

        xyrange
            The x- and y-range to apply to the figure

        figure_current
            Current state of the figure

        app_dataset
            The app dataset to use. If not provided, we use get_app_dataset()

        Returns
        -------
            Overview figure.
        """
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if ctx.triggered_id == "xyrange" and xyrange:
            return update_xy_range(xyrange=xyrange, figure=figure_current)

        if any(v is None for v in (country, category, entity)):
            # User cleared one of the selections in the dropdown, do nothing
            return figure_current

        return create_overview_figure(
            country=country,
            category=category,
            entity=entity,
            dataset=app_dataset,
        )

    @app.callback(  # type: ignore
        Output("dropdown-source-scenario", "options"),
        Output("dropdown-source-scenario", "value"),
        Output("dropdown-source-scenario-dashed", "options"),
        Output("dropdown-source-scenario-dashed", "value"),
        Output("memory", "data"),
        Input("dropdown-country", "value"),
        Input("dropdown-category", "value"),
        Input("dropdown-entity", "value"),
        State("dropdown-source-scenario", "value"),
        State("dropdown-source-scenario", "options"),
        State("dropdown-source-scenario-dashed", "value"),
        State("dropdown-source-scenario-dashed", "options"),
        State("memory", "data"),
    )
    def update_source_scenario_dropdown(  # noqa: PLR0913
        country: str,
        category: str,
        entity: str,
        source_scenario: str,
        source_scenario_options: tuple[str, ...],
        source_scenario_dashed: str,
        source_scenario_options_dashed: tuple[str, ...],
        memory_data: dict[str, int],
        app_dataset: xr.Dataset | None = None,
    ) -> tuple[tuple[str, ...], str, tuple[str, ...], str, dict[str, int]]:
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if any(v is None for v in (country, category, entity)):
            # User cleared one of the selections in the dropdown, do nothing
            return (
                source_scenario_options,
                source_scenario,
                source_scenario_options_dashed,
                source_scenario_dashed,
                memory_data,
            )

        source_scenario_options_out = update_source_scenario_options(
            country=country, category=category, entity=entity, dataset=app_dataset
        )

        # memory_data shares information between callbacks
        # to make sure they are executed sequentially.
        # When the user changes country, category, entity
        # first the dropdown will be updated and then category and
        # entity figure.
        # The actual value of memory_data is irrelevant, but it must be JSON enumerable
        if not memory_data:
            memory_data = {"_": 0}
        else:
            memory_data["_"] += 1

        if not source_scenario_options_out:
            return (
                source_scenario_options,
                source_scenario,
                source_scenario_options_dashed,
                source_scenario_dashed,
                memory_data,
            )

        if source_scenario in source_scenario_options_out:
            source_scenario_out = source_scenario
        else:
            source_scenario_out = source_scenario_options_out[0]

        if source_scenario_dashed in source_scenario_options_out:
            source_scenario_out_dashed = source_scenario_dashed
        else:
            source_scenario_out_dashed = source_scenario_options_out[0]

        return (
            source_scenario_options_out,
            source_scenario_out,
            source_scenario_options_out,
            source_scenario_out_dashed,
            memory_data,
        )

    @app.callback(  # type: ignore
        Output(dict(name="graph-category-split", type="graph"), "figure"),
        Input("dropdown-country", "value"),
        Input("dropdown-category", "value"),
        Input("dropdown-entity", "value"),
        Input("dropdown-source-scenario", "value"),
        Input("dropdown-source-scenario-dashed", "value"),
        Input("xyrange", "data"),
        State(dict(name="graph-category-split", type="graph"), "figure"),
    )
    def update_category_figure(  # noqa: PLR0913
        country: str,
        category: str,
        entity: str,
        source_scenario: str,
        source_scenario_dashed: str,
        xyrange: dict[str, int],
        figure_current: go.Figure,
        app_dataset: xr.Dataset | None = None,
    ) -> go.Figure:
        """
        Update the category figure.

        Parameters
        ----------
        country
            The currently selected country in the dropdown menu

        category
            The currently selected category in the dropdown menu

        entity
            The currently selected entity in the dropdown menu

        source_scenario
            Source-scenario to plot with a solid line

        source_scenario_dashed
            Source-scenario to plot with a dashed line

        xyrange
            The x- and y-range to apply to the figure

        figure_current
            Current state of the figure

        app_dataset
            The app dataset to use. If not provided, we use get_app_dataset()

        Returns
        -------
            category figure.
        """
        if app_dataset is None:
            app_dataset = get_application_dataset()
        if ctx.triggered_id == "xyrange" and xyrange:
            fig = update_xy_range(xyrange=xyrange, figure=figure_current)
            return fig

        if any(
            v is None
            for v in (
                country,
                category,
                entity,
                source_scenario,
                source_scenario_dashed,
            )
        ):
            # User cleared one of the selections in the dropdown, do nothing
            return figure_current

        return create_category_figure(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            source_scenario_dashed=source_scenario_dashed,
            dataset=app_dataset,
        )

    @app.callback(  # type: ignore
        Output(dict(name="graph-entity-split", type="graph"), "figure"),
        Input("dropdown-country", "value"),
        Input("dropdown-category", "value"),
        Input("dropdown-entity", "value"),
        Input("dropdown-source-scenario", "value"),
        Input("dropdown-source-scenario-dashed", "value"),
        Input("xyrange", "data"),
        State(dict(name="graph-entity-split", type="graph"), "figure"),
    )
    def update_entity_graph(  # noqa: PLR0913
        country: str,
        category: str,
        entity: str,
        source_scenario: str,
        source_scenario_dashed: str,
        xyrange: dict[str, int],
        figure_current: go.Figure,
        app_dataset: xr.Dataset | None = None,
    ) -> go.Figure:
        """
        Update the entity figure.

        Parameters
        ----------
        country
            The currently selected country in the dropdown menu

        category
            The currently selected category in the dropdown menu

        entity
            The currently selected entity in the dropdown menu

        source_scenario
            Source-scenario to plot with a solid line

        source_scenario_dashed
            Source-scenario to plot with a dashed line

        xyrange
            The x- and y-range to apply to the figure

        figure_current
            Current state of the figure

        app_dataset
            The app dataset to use. If not provided, we use get_app_dataset()

        Returns
        -------
            entity figure.
        """
        if app_dataset is None:
            app_dataset = get_application_dataset()

        if ctx.triggered_id == "xyrange" and xyrange:
            return update_xy_range(xyrange=xyrange, figure=figure_current)

        if any(
            v is None
            for v in (
                country,
                category,
                entity,
                source_scenario,
                source_scenario_dashed,
            )
        ):
            # User cleared one of the selections in the dropdown, do nothing
            return figure_current

        return create_entity_figure(
            country=country,
            category=category,
            entity=entity,
            source_scenario=source_scenario,
            source_scenario_dashed=source_scenario_dashed,
            dataset=app_dataset,
        )

    @app.callback(  # type: ignore
        Output("xyrange", "data"),
        Output("relayout-store", "data"),
        Input({"type": "graph", "name": ALL}, "relayoutData"),
        State({"type": "graph", "name": ALL}, "figure"),
        State("relayout-store", "data"),
        prevent_initial_call=True,
    )
    def update_shared_xy_range(
        all_relayout_data: list[None | dict[str, str | bool]],
        all_figures: list[dict[str, Any]],
        all_relayout_data_prev: list[None | dict[str, str | bool]],
    ) -> tuple[dict[str, str], list[Any] | Any]:
        # first time this callback runs, set current relayout data as reference
        if all_relayout_data_prev is None:
            all_relayout_data_prev = all_relayout_data

        # find out which figure triggered the callback
        # relayoutData of that figure is now different to the previous version
        unique_data = [
            j for i, j in zip(all_relayout_data_prev, all_relayout_data) if i != j
        ]

        res = {}
        if unique_data:
            # choose the figure according to relayout data
            idx = all_relayout_data.index(unique_data[0])
            figure_of_interest = all_figures[idx]
            if figure_of_interest["layout"]["xaxis"].get("autorange"):
                res["xaxis"] = "autorange"
            else:
                res["xaxis"] = figure_of_interest["layout"]["xaxis"]["range"]

            if figure_of_interest["layout"]["yaxis"].get("autorange"):
                res["yaxis"] = "autorange"
            else:
                res["yaxis"] = figure_of_interest["layout"]["yaxis"]["range"]

            return res, all_relayout_data

        return res, all_relayout_data

    @app.callback(
        Output("note-saved-div", "children"),
        Output("input-for-notes", "value"),
        Output("country-dropdown-store", "data"),
        State("input-for-notes", "value"),
        State("country-dropdown-store", "data"),
        Input("save-button", "n_clicks"),
        Input("dropdown-country", "value"),
    )  # type:ignore
    def save_note(
        notes_value: str,
        country_store: dict[str, str],
        save_button_clicks: int,
        dropdown_country_current: str,
        notes_db_filepath: Path | None = None,
    ) -> tuple[str, str, dict[str, str]]:
        """
        Save notes

        Parameters
        ----------
        notes_value
            The notes to save

        country_store
            The country store value.

            We use this to store the country dropdown value before it was changed.
            This is required because the country dropdown has already changed
            by the time this callback is triggered.

        save_button_clicks
            The number of times the save button was pressed.

        dropdown_country_current
            The current value of the country dropdown.

        notes_db_filepath
            The path to the notes database file.
            If not supplied, we use
            {py:const}`primap_visualisation_tool_stateless_app.notes.db_filepath_holder.APPLICATION_NOTES_DB_PATH_HOLDER`.

        Returns
        -------
            Information about which notes were saved/loaded (first element),
            the new value to show in the notes input field (second element)
            and the new value of ``country_store``.
        """
        if notes_db_filepath is None:
            notes_db_filepath = (
                primap_visualisation_tool_stateless_app.notes.db_filepath_holder.APPLICATION_NOTES_DB_PATH_HOLDER
            )
            if notes_db_filepath is None:
                msg = "Notes database filepath must be set at this point"
                raise ValueError(msg)

        if not country_store:
            # Initial callback so just set sensible starting value
            country_store = {"country": dropdown_country_current}

        if ctx.triggered_id == "dropdown-country":
            (
                note_saved_div,
                input_field_value,
            ) = save_notes_and_load_existing_notes_after_dropdown_country_change(
                notes_value=notes_value,
                country_notes=country_store["country"],
                country_current=dropdown_country_current,
                notes_db_filepath=notes_db_filepath,
            )

            country_store["country"] = dropdown_country_current

            return (note_saved_div, input_field_value, country_store)

        # If we get here, the user pressed save
        if not notes_value:
            # User hit save with no input (e.g. at initial callback),
            # hence do nothing.
            return "", "", country_store

        with notes_db_cursor(db_filepath=notes_db_filepath) as db_cursor:
            save_country_notes_in_notes_db(
                db_cursor=db_cursor,
                country=dropdown_country_current,
                notes_to_save=notes_value,
            )

        return (
            get_note_save_confirmation_string(
                db_filepath=notes_db_filepath, country=dropdown_country_current
            ),
            notes_value,
            country_store,
        )


def save_notes_and_load_existing_notes_after_dropdown_country_change(
    notes_value: str,
    country_notes: str,
    country_current: str,
    notes_db_filepath: Path,
) -> tuple[str, str]:
    """
    Save the notes and load existing notes following a change in the country dropdown

    Parameters
    ----------
    notes_value
        Notes to save

    country_before_dropdown_change
        The country to which the notes apply

    country_current
        The current country showing in the dropdown
        (this is not the country to which the notes apply,
        because the dropdown is updated before we save the notes).

    notes_db_filepath
        The file path to the notes database

    Returns
    -------
        Information about which notes were saved/loaded (first element)
        and the new value to show in the notes input field (second element).
    """
    if not notes_value:
        note_saved_info = ""

    else:
        note_saved_info = ensure_existing_note_saved(
            notes_value=notes_value,
            country_notes=country_notes,
            notes_db_filepath=notes_db_filepath,
        )

    # Load any notes for the country that is now being displayed
    with notes_db_cursor(db_filepath=notes_db_filepath) as db_cursor:
        new_country_notes_value_in_db = get_country_notes_from_notes_db(
            db_cursor=db_cursor, country=country_current
        )

    if new_country_notes_value_in_db is None:
        new_input_for_notes_value = ""
        note_loaded_info = ""

    else:
        new_input_for_notes_value = new_country_notes_value_in_db
        note_loaded_info = f"Loaded existing notes for {country_current}"

    note_saved_div_new_value_l = [v for v in [note_saved_info, note_loaded_info] if v]
    if note_saved_div_new_value_l:
        note_saved_div_new_value = ". ".join(note_saved_div_new_value_l)
    else:
        note_saved_div_new_value = ""

    return note_saved_div_new_value, new_input_for_notes_value


def ensure_existing_note_saved(
    notes_value: str,
    country_notes: str,
    notes_db_filepath: Path,
) -> str:
    """
    Ensure that notes are saved in the notes database

    This makes sure that users don't lose notes,
    even if they change country from the dropdown without saving.

    Parameters
    ----------
    notes_value
        Notes to save

    country_notes
        The country to which the notes apply

    notes_db_filepath
        The file path to the notes database

    Returns
    -------
        Information about how the notes were saved.
    """
    with notes_db_cursor(db_filepath=notes_db_filepath) as db_cursor:
        current_country_notes_value_in_db = get_country_notes_from_notes_db(
            db_cursor=db_cursor, country=country_notes
        )
        if notes_value == current_country_notes_value_in_db:
            # The note has already been saved, don't need to do anything more
            note_saved_info = f"Notes for {country_notes} already saved"

        else:
            # Note differs, hence must save first
            save_country_notes_in_notes_db(
                db_cursor=db_cursor,
                country=country_notes,
                notes_to_save=notes_value,
            )

            note_saved_info = ". ".join(
                [
                    f"Autosaved notes for {country_notes}",
                    get_note_save_confirmation_string(
                        db_filepath=notes_db_filepath, country=country_notes
                    ),
                ]
            )

    return note_saved_info
