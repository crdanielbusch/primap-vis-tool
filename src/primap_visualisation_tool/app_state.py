"""
Definition of our app's state
"""
import csv
import datetime
import json
import warnings
from collections.abc import Sized
from pathlib import Path
from typing import Any

import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import primap2 as pm  # type: ignore
import pycountry
import xarray as xr
from attrs import define
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


# For now, hard-code path to test data set.
# TODO: fix this, bad pattern
test_ds = Path(__file__).parent.parent.parent / "data" / "20240212_test_ds.nc"
APP_STATE = get_default_app_starting_state(filename=test_ds)
