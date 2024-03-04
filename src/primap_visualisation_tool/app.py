"""
Launch plotly app.

Author: Daniel Busch, Date: 2023-12-21
"""
from __future__ import annotations

import argparse
import csv
import json
import warnings
from collections.abc import Sized
from datetime import datetime
from pathlib import Path
from typing import Any

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
from dash.exceptions import PreventUpdate  # type: ignore
from filelock import FileLock

from primap_visualisation_tool.definitions import (
    LINES_LAYOUT,
    LINES_ORDER,
    SUBENTITIES,
    index_cols,
)
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

    source_scenario_visible: dict[str, bool]
    """Selected source scenarios in the overview plot legend"""

    ds: xr.Dataset
    """Dataset to plot from"""

    filename: str
    """The name of the data set."""

    present_index_cols: list[str]
    """index cols that are actually present in the loaded dataset"""

    overview_graph: go.Figure | None = None  # type: ignore
    """Overview graph"""

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

        with warnings.catch_warnings(action="ignore"):  # type: ignore
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

    # TODO: remove based on discussion here
    # https://github.com/crdanielbusch/primap-vis-tool/pull/22/files#r1474566618
    def update_source_scenario_visible(
        self,
        legend_value: list[Any],  # TODO if possible, give more detailed type hint
        figure_data: dict[str, Any],
    ) -> None:
        """
        Update the selected lines in the overview plot legend.

        Parameters
        ----------
        legend_value
            The legend value that was clicked and triggered the callback.
        figure_data
            The overview plot figure.
        """
        lines_in_figure = [i["name"] for i in figure_data["data"]]

        lines_to_change = [lines_in_figure[i] for i in legend_value[1]]

        for source_scenario, new_value in zip(
            lines_to_change, legend_value[0]["visible"]
        ):
            self.source_scenario_visible[source_scenario] = new_value

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

    def update_overview_figure(self, xyrange_data: str | None) -> Any:
        """
        Update the overview figure based on the input in the dropdown menus.

        Returns
        -------
            Overview figure. A plotly graph object.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        with warnings.catch_warnings(action="ignore"):  # type: ignore
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

        source_scenario_sorted = list(self.source_scenario_options)
        # move primap source scenarios to the front of the list
        # in the same order as specified in LINES_ORDER
        for i in [j for j in LINES_ORDER if j in self.source_scenario_options]:
            source_scenario_sorted.insert(
                0, source_scenario_sorted.pop(source_scenario_sorted.index(i))
            )

        for source_scenario in source_scenario_sorted:
            # check if layout is defined
            if source_scenario in LINES_LAYOUT:
                line_layout = LINES_LAYOUT[source_scenario]
            else:
                line_layout = {}  # empty dict creates random layout

            df_source_scenario = filtered_pandas.loc[
                filtered_pandas["SourceScen"] == source_scenario
            ]

            df_source_scenario = df_source_scenario.reset_index()
            # find start and end of time series for SourceScenario
            first_idx = df_source_scenario[self.entity].first_valid_index()
            last_idx = df_source_scenario[self.entity].last_valid_index()
            # check if time series has data gaps
            if any(df_source_scenario[self.entity].loc[first_idx:last_idx].isna()):
                mode = "lines+markers"
            else:
                mode = "lines"

            fig.add_trace(
                go.Scatter(
                    x=list(df_source_scenario["time"]),
                    y=list(df_source_scenario[self.entity]),
                    mode=mode,
                    marker_symbol="cross",
                    marker_size=10,
                    name=source_scenario,
                    line=line_layout,
                    visible=self.source_scenario_visible[source_scenario],
                    hovertemplate="%{y:.2e} ",
                )
            )

        fig.update_layout(
            xaxis=dict(
                rangeslider=dict(visible=True, thickness=0.05),
                type="date",
            ),
            yaxis=dict(
                autorange=True,
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=0, b=0),  # distance to next element
            hovermode="x",
        )

        # In the initial callback this property will be None
        if xyrange_data:
            xyrange_data_dict = json.loads(xyrange_data)
            fig.update_layout(
                xaxis=dict(
                    range=xyrange_data_dict["xaxis"],
                    autorange=False,
                ),
                yaxis=dict(
                    autorange=True,
                ),
            )

        self.overview_graph = fig

        return self.overview_graph

    def update_category_figure(self, xyrange_data: str | None) -> Any:
        """
        Update the overview figure based on the input in the dropdown menus.

        Returns
        -------
            Category figure. A plotly express object.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        categories_plot = select_cat_children(self.category, self.category_options)

        with warnings.catch_warnings(action="ignore"):  # type: ignore
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

        if filtered_pandas[self.entity].isna().all():
            # filter again but only for parent category
            with warnings.catch_warnings(action="ignore"):  # type: ignore
                filtered = (
                    self.ds[self.entity]
                    .pr.loc[
                        {
                            "category": self.category,
                            "area (ISO3)": iso_country,
                            "SourceScen": self.source_scenario,
                        }
                    ]
                    .squeeze()
                )

            filtered_pandas = filtered.to_dataframe().reset_index()

        # Fix for figure not loading at start
        # https://github.com/plotly/plotly.py/issues/3441
        fig = go.Figure(layout=dict(template="plotly"))

        # save xrange in case last values are NaN and cut off
        xrange = [min(filtered_pandas["time"]), max(filtered_pandas["time"])]
        filtered_pandas = filtered_pandas.dropna(subset=[self.entity])

        # bring df in right format for plotting
        _df = filtered_pandas
        _df = _df.set_index("time")
        # If we need better performance, there's probably a pandas function for this loop
        # which may help (the loop may also not be that slow)
        # TODO! Remove hard-coded category column name
        _df = pd.concat(
            [
                _df[_df["category (IPCC2006_PRIMAP)"] == c][self.entity].rename(c)
                for c in categories_plot
            ],
            axis=1,
        )
        print(f"{_df=}")

        # determine where positive and negative emissions
        _df_pos = _df.map(lambda x: max(x, 0))
        _df_neg = _df.map(lambda x: min(x, 0))

        # TODO! Check different color schemes.
        # https://plotly.com/python/discrete-color/#color-sequences-in-plotly-express
        # Set colors for areas per category
        defaults = iter(px.colors.qualitative.Vivid)
        colors = {}
        for key in _df.columns:
            color = next(defaults)
            colors[key] = color

        fig = go.Figure()

        # plot all positive emissions
        lower = [0] * len(_df_pos)
        for c in reversed(_df_pos.columns):
            if sum(_df_pos[c].fillna(0)) == 0:
                continue

            upper = _df_pos[c].fillna(0) + lower
            fig.add_trace(
                go.Scatter(
                    y=upper,
                    x=_df_pos.index,
                    mode="lines",
                    showlegend=False,
                    line=dict(
                        color=colors[c],
                        width=0,
                    ),
                    text=list(_df_pos[c]),
                    customdata=list(_df_pos.index.year),
                    hovertemplate="%{customdata}, %{text:.2e}",
                    name=f"{c} pos",
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=lower,
                    x=_df_pos.index,
                    fill="tonexty",  # fill area between trace0 and trace1
                    fillcolor=colors[c],
                    mode="lines",
                    line=dict(
                        width=0,
                    ),
                    hoverinfo="skip",
                    name=f"{c} pos",
                )
            )
            lower = upper

        # plot all negative emissions
        upper = [0] * len(_df_neg)
        for c in _df_neg.columns:
            if sum(_df_neg[c]) == 0:
                continue

            lower = _df_neg[c].fillna(0) + upper
            fig.add_trace(
                go.Scatter(
                    y=upper,
                    x=_df_neg.index,
                    mode="lines",
                    line=dict(
                        color=colors[c],
                        width=0,
                    ),
                    showlegend=False,
                    name=f"{c} neg",
                    text=f"Category {c}",
                    hoverinfo="skip",
                )
            )

            fig.add_trace(
                go.Scatter(
                    y=lower,
                    x=_df_neg.index,
                    fill="tonexty",  # fill area between trace0 and trace1
                    mode="lines",
                    line=dict(
                        color=colors[c],
                        width=0,
                    ),
                    fillcolor=colors[c],
                    text=list(_df_neg[c]),
                    customdata=list(_df_neg.index.year),
                    hovertemplate="%{customdata}, %{text:.2e}",
                    name=f"{c} neg",
                )
            )
            upper = lower

        # plot line for sum
        fig.add_trace(
            go.Scatter(
                y=_df.sum(axis=1),
                x=_df.index,
                mode="lines",
                line=dict(
                    color="black",
                    width=3,
                ),
                name="total",
                customdata=list(_df.index.year),
                hovertemplate="%{customdata}, %{y:.2e}",
            )
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=40, b=40),
            hovermode="x",
            # in some cases the last values will be nan and must be dropped
            # the xrange, however, should remain
            xaxis=dict(
                range=xrange,
            ),
        )

        # In the initial callback xyrange_data will be None
        if xyrange_data:
            xyrange_data_dict = json.loads(xyrange_data)
            fig.update_layout(
                xaxis=dict(
                    range=xyrange_data_dict["xaxis"],
                ),
            )

        self.category_graph = fig

        return self.category_graph

    def update_entity_figure(self, xyrange_data: str | None) -> Any:  # noqa: PLR0915
        """
        Update the overview figure based on the input in the dropdown menus.

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

        with warnings.catch_warnings(action="ignore"):  # type: ignore
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

        with warnings.catch_warnings(action="ignore"):  # type: ignore
            stacked = filtered.pr.to_interchange_format().melt(
                id_vars=index_cols, var_name="time", value_name="value"
            )

        # if all values are NaN
        if stacked["value"].isna().all():
            print(f"All sub-entities for {self.entity} are nan")
            # filter again but only for parent entity
            with warnings.catch_warnings(action="ignore"):  # type: ignore
                filtered = self.ds[self.entity].pr.loc[
                    {
                        "category": [self.category],
                        "area (ISO3)": [iso_country],
                        "SourceScen": [self.source_scenario],
                    }
                ]

            filtered_df = filtered.to_dataframe().reset_index()
            stacked = filtered_df.rename(columns={self.entity: "value"})
            stacked["entity"] = self.entity
        stacked["time"] = stacked["time"].apply(pd.to_datetime)

        # save xrange in case last values are NaN and cut off
        xrange = [min(stacked["time"]), max(stacked["time"])]
        stacked = stacked.dropna(subset=["value"])

        # bring df in right format for plotting
        _df = stacked
        _df = _df.set_index("time")
        # TODO! There's probably a pandas function for this loop
        # TODO! Remove hard-coded category column name
        _df = pd.concat(
            [
                _df[_df["entity"] == c]["value"].rename(c)
                for c in _df["entity"].unique()
            ],
            axis=1,
        )
        print("entity")
        print(_df)

        # TODO: reduce duplication with category plot in future PR
        # determine where positive and negative emissions
        _df_pos = _df.map(lambda x: max(x, 0))
        _df_neg = _df.map(lambda x: min(x, 0))

        # TODO! Check different color schemes.
        # https://plotly.com/python/discrete-color/#color-sequences-in-plotly-express
        # Set colors for areas per category
        defaults = iter(px.colors.qualitative.Vivid)
        colors = {}
        for key in _df.columns:
            color = next(defaults)
            colors[key] = color

        fig = go.Figure()

        # plot all positive emissions
        lower = [0] * len(_df_pos)
        for c in reversed(_df_pos.columns):
            if sum(_df_pos[c].fillna(0)) == 0:
                continue

            upper = _df_pos[c].fillna(0) + lower
            fig.add_trace(
                go.Scatter(
                    y=upper,
                    x=_df_pos.index,
                    mode="lines",
                    showlegend=False,
                    line=dict(
                        color=colors[c],
                        width=0,
                    ),
                    text=list(_df_pos[c]),
                    customdata=list(_df_pos.index.year),
                    hovertemplate="%{customdata}, %{text:.2e}",
                    name=f"{c} pos",
                )
            )
            fig.add_trace(
                go.Scatter(
                    y=lower,
                    x=_df_pos.index,
                    fill="tonexty",  # fill area between trace0 and trace1
                    fillcolor=colors[c],
                    mode="lines",
                    line=dict(
                        width=0,
                    ),
                    hoverinfo="skip",
                    name=f"{c} pos",
                )
            )
            lower = upper

        # plot all negative emissions
        upper = [0] * len(_df_neg)
        for c in _df_neg.columns:
            if sum(_df_neg[c]) == 0:
                continue

            lower = _df_neg[c].fillna(0) + upper
            fig.add_trace(
                go.Scatter(
                    y=upper,
                    x=_df_neg.index,
                    mode="lines",
                    line=dict(
                        color=colors[c],
                        width=0,
                    ),
                    showlegend=False,
                    name=f"{c} neg",
                    text=f"Category {c}",
                    hoverinfo="skip",
                )
            )

            fig.add_trace(
                go.Scatter(
                    y=lower,
                    x=_df_neg.index,
                    fill="tonexty",  # fill area between trace0 and trace1
                    mode="lines",
                    line=dict(
                        color=colors[c],
                        width=0,
                    ),
                    fillcolor=colors[c],
                    text=list(_df_neg[c]),
                    customdata=list(_df_neg.index.year),
                    hovertemplate="%{customdata}, %{text:.2e}",
                    name=f"{c} neg",
                )
            )
            upper = lower

        # plot line for sum
        fig.add_trace(
            go.Scatter(
                y=_df.sum(axis=1),
                x=_df.index,
                mode="lines",
                line=dict(
                    color="black",
                    width=3,
                ),
                name="total",
                customdata=list(_df.index.year),
                hovertemplate="%{customdata}, %{y:.2e}",
            )
        )

        fig.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
            margin=dict(l=0, r=0, t=40, b=40),  # distance to next element
            hovermode="x",
            # in some cases the last values will be NaN and must be dropped
            # the xrange, however, should remain
            xaxis=dict(
                range=xrange,
            ),
        )

        # fig.update_traces(
        #     hovertemplate="%{y:.2e} ",
        # )

        # In the initial callback xyrange_data will be None
        if xyrange_data:
            xyrange_data_dict = json.loads(xyrange_data)
            fig.update_layout(
                xaxis=dict(
                    range=xyrange_data_dict["xaxis"],
                ),
            )

        self.entity_graph = fig

        return self.entity_graph

    def update_x_range(
        self, fig: Any, xyrange: dict[str, list[str | float | bool]]
    ) -> Any:
        """
        Update the x-axis limits in the plot.

        Parameters
        ----------
        fig
            The figure that should be updated.
        xrange
            The minimum and maximum value for the x- and y-axis.

        Returns
        -------
            The same figure with update x-axis
        """
        fig["layout"].update(
            xaxis=dict(
                range=[
                    xyrange["xaxis"][0],
                    xyrange["xaxis"][1],
                ],
                autorange=False,
            ),
        )

        return fig

    def update_y_range(self, fig: Any, xyrange: dict[str, list[str | float]]) -> Any:
        """
        Update the y-axis limits in the plot.

        Parameters
        ----------
        fig
            The figure that should be updated.
        xyrange
            The minimum and maximum value for the x- and y-axis.


        Returns
        -------
            The same figure with updated y-axis.
        """
        fig["layout"].update(
            yaxis=dict(
                range=[
                    xyrange["yaxis"][0],
                    xyrange["yaxis"][1],
                ],
                autorange=False,
            ),
        )

        return fig

    def update_overview_range(self, xyrange_data: str) -> Any:
        """
        Update xy-range of overview figure according to stored xy-range.

        Parameters
        ----------
        xyrange_data
            X- and y-axis range to which the figure is to be updated.

        Returns
        -------
            Updated figure.

        """
        fig = self.overview_graph

        layout_data = json.loads(xyrange_data)

        # autorange indicates user clicked on Autoscale or Reset axes
        if "autorange" in layout_data.keys():
            fig["layout"].update(  # type: ignore
                yaxis=dict(
                    autorange=True,
                ),
                xaxis=dict(
                    autorange=True,
                ),
            )
        else:
            fig = self.update_x_range(fig, layout_data)
            fig = self.update_y_range(fig, layout_data)

        return fig

    def update_category_range(self, xyrange_data: str) -> Any:
        """
        Update xy-range of category figure according to stored xy-range.

        Parameters
        ----------
        xyrange_data
            X- and y-axis range to which the figure is to be updated.

        Returns
        -------
            Updated figure.

        """
        layout_data = json.loads(xyrange_data)

        fig = self.category_graph

        # autorange indicates user clicked on Autoscale or Reset axes
        if "autorange" in layout_data.keys():
            fig["layout"].update(  # type: ignore
                yaxis=dict(
                    autorange=True,
                ),
                xaxis=dict(
                    autorange=True,
                ),
            )
        else:
            fig = self.update_x_range(fig, layout_data)
            fig = self.update_y_range(fig, layout_data)

        return fig

    def update_entity_range(self, xyrange_data: str) -> Any:
        """
        Update xy-range of entity figure according to stored xy-range.

        Parameters
        ----------
        xyrange_data
            X- and y-axis range to which the figure is to be updated.

        Returns
        -------
            Updated figure.
        """
        layout_data = json.loads(xyrange_data)

        fig = self.entity_graph

        # autorange indicates user clicked on Autoscale or Reset axes
        if "autorange" in layout_data.keys():
            fig["layout"].update(  # type: ignore
                yaxis=dict(
                    autorange=True,
                ),
                xaxis=dict(
                    autorange=True,
                ),
            )
        else:
            fig = self.update_x_range(fig, layout_data)
            fig = self.update_y_range(fig, layout_data)

        return fig

    def get_xyrange_from_figure(
        self,
        x_source_figure: dict[str, Any] | None = None,
        y_source_figure: dict[str, Any] | None = None,
        autorange: bool = False,
    ) -> str:
        """
        Get x- and y-axis limits from a figure and set autorange.

        Parameters
        ----------
        x_source_figure
            Figure from which to extract x-axis limits.
        y_source_figure
            Figure from which to ectract y-axis limits.
        autorange
            Ignore x- and y-axis limits in the current plot and set to autorange.

        Returns
        -------
            Information about x- and y-axis limits.

        """
        xy_range = {}

        if x_source_figure:
            xy_range["xaxis"] = x_source_figure["layout"]["xaxis"]["range"]
        if y_source_figure:
            xy_range["yaxis"] = y_source_figure["layout"]["yaxis"]["range"]
        if autorange:
            xy_range["autorange"] = True

        return json.dumps(xy_range)

    def save_note_to_csv(self, text_input: str) -> None:
        """
        Save the text from the text area input to disk in a csv file.

        Parameters
        ----------
        text_input
            Text that the user wrote in the input box.
        """
        filename = f"{self.filename[:-3]}_notes.csv"

        new_row = [
            self.country_name_iso_mapping[self.country],
            self.category,
            self.entity,
            text_input,
        ]

        lock = FileLock(f"{filename}.lock")

        # open file in append mode with 'a'
        with lock:
            with open(filename, "a") as f:
                writer = csv.writer(f)
                # add a header if the file has zero rows
                if f.seek(0, 2) == 0:
                    writer.writerow(["country", "category", "entity", "note"])
                writer.writerow(new_row)

    def get_notification(self) -> str:
        """
        Create a text that lets the user know what was saved.

        Returns
        -------
            Information about saved notes.
        """
        now = datetime.now()
        now_str = now.strftime("%Y-%m-%d-%H-%M-%S")

        return (
            f"Note saved for {self.country} / {self.category} /"
            f" {self.entity}  at {now_str}"
        )

    def get_row_data(self) -> Any:
        """
        Get the content for data table.

        Returns
        -------
            Data to show in table.
        """
        iso_country = self.country_name_iso_mapping[self.country]

        with warnings.catch_warnings(action="ignore"):  # type: ignore
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

        # drop rows where SourceScen is NaN and sort by SourceScen name
        filtered_pandas = filtered_pandas.dropna(subset=[self.entity]).sort_values(
            by=["SourceScen"]
        )

        row_data = filtered_pandas.to_dict("records")

        # change format
        for i in row_data:
            i["time"] = i["time"].strftime("%Y")
            i[self.entity] = f"{i[self.entity]:.2e}"

        return row_data

    def get_column_defs(self) -> list[dict[str, object]]:
        """
        Get the column definitions for the data table.

        Returns
        -------
            Column definitions.
        """
        column_defs = [
            {"field": "time", "sortable": True, "filter": "agNumberColumnFilter"},
            {"field": "area (ISO3)", "sortable": True},
            {"field": "category (IPCC2006_PRIMAP)", "sortable": True},
            {"field": "SourceScen", "sortable": True},
            {
                "headerName": f"{self.entity} [{self.ds[self.entity].pint.units}]",
                "field": self.entity,
                "sortable": True,
                "filter": "agNumberColumnFilter",
                "minWidth": 300,
            },
        ]

        return column_defs


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


def get_default_app_starting_state(
    filename: str,
    start_values: dict[str, str] = {
        "country": "EARTH",
        "category": "M.0.EL",
        "entity": "KYOTOGHG (AR6GWP100)",
        "source_scenario": "PRIMAP-hist_v2.5_final_nr, HISTCR",
    },
) -> AppState:
    """
    Get default starting state for the application

    Parameters
    ----------
    filename
        The name of the file to read in.

    start_values
        Intitial values for country, category and entity.

    Returns
    -------
        Default starting state
    """
    root_folder = Path(__file__).parent.parent.parent
    data_folder = Path("data")

    present_index_cols = index_cols

    print(f"Reading data set {filename}")
    combined_ds = pm.open_dataset(root_folder / data_folder / filename)
    print("Finished reading data set")

    if "provenance" in combined_ds.coords:
        combined_ds = combined_ds.drop_vars("provenance")
    else:
        present_index_cols.remove("provenance")
    # drop_vars only drops the coord not the dimension.
    # TODO: remove provenance completely from index_cols it's just kept here to run
    #  with the legacy datasets which contain provenance ("measured" only)

    country_name_iso_mapping = get_country_options(combined_ds)
    country_dropdown_options = tuple(sorted(country_name_iso_mapping.keys()))

    category_options = tuple(combined_ds["category (IPCC2006_PRIMAP)"].to_numpy())

    entity_options = tuple(i for i in combined_ds.data_vars)

    source_scenario_options = tuple(combined_ds["SourceScen"].to_numpy())

    source_scenario_visible = {
        k: v
        for (k, v) in zip(
            source_scenario_options, [True] * len(source_scenario_options)
        )
    }

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
        source_scenario_visible=source_scenario_visible,
        ds=combined_ds,
        filename=filename,
        present_index_cols=present_index_cols,
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", help="Port number", required=False, default=8050)
    parser.add_argument("-f", help="Filename of data set", required=False)
    args = parser.parse_args()

    port = args.p
    filename = get_filename(user_input=args.f, test_ds=True)

    APP_STATE = get_default_app_starting_state(filename=filename)

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
                                    data=APP_STATE.source_scenario_visible,
                                ),
                                dcc.Store(id="xyrange-overview"),
                                dcc.Store(id="xyrange-category"),
                                dcc.Store(id="xyrange-entity"),
                                html.B(
                                    children="Country",
                                    style={"textAlign": "left", "fontSize": 14},
                                ),
                                dcc.Dropdown(
                                    options=APP_STATE.country_options,
                                    value=APP_STATE.country,
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
                                    APP_STATE.category_options,
                                    value=APP_STATE.category,
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
                                    APP_STATE.entity_options,
                                    value=APP_STATE.entity,
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
                                    APP_STATE.source_scenario_options,
                                    value=APP_STATE.source_scenario,
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
                                                children="AR46WP100",
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

    with warnings.catch_warnings(action="ignore"):  # type: ignore
        app.run(debug=True, port=port)
