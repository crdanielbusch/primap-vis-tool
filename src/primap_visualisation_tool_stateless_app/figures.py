"""
Figure handling and creation
"""
import warnings
from collections.abc import Iterable

import climate_categories as cc
import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import xarray as xr

from primap_visualisation_tool_stateless_app.dataset_handling import (
    get_country_code_mapping,
)

LINES_ORDER: tuple[str, ...] = (
    "PRIMAP-hist_v2.5_final_nr, HISTCR",
    "PRIMAP-hist_v2.5_final_nr, HISTTP",
    "PRIMAP-hist_v2.4.2_final_nr, HISTCR",
    "PRIMAP-hist_v2.4.2_final_nr, HISTTP",
)
"""The order to plot the lines in the main figure, from background to foreground"""

LINES_LAYOUT: dict[str, dict[str, str | int]] = {
    "Andrew cement, HISTORY": {"color": "rgb(0,0,255)", "dash": "solid"},
    "CDIAC 2020, HISTORY": {"color": "rgb(50,200,255)", "dash": "solid"},
    "CEDS 2020, HISTORY": {"color": "rgb(0, 0, 255)", "dash": "solid"},
    "CRF 2022, 230510": {"color": "rgb(60, 179, 113)", "dash": "solid"},
    "CRF 2023, 230926": {"color": "rgb(238, 130, 238)", "dash": "solid"},
    "EDGAR 7.0, HISTORY": {"color": "rgb(255, 165, 0)", "dash": "solid"},
    "EDGAR-HYDE 1.4, HISTORY": {"color": "rgb(106, 90, 205)", "dash": "solid"},
    "EI 2023, HISTORY": {"color": "rgb(50,0,255)", "dash": "solid"},
    "FAOSTAT 2022, HISTORY": {"color": "rgb(100,0,255)", "dash": "solid"},
    "Houghton, HISTORY": {"color": "rgb(150,0,255)", "dash": "solid"},
    "MATCH, HISTORY": {"color": "rgb(200,0,255)", "dash": "solid"},
    "PRIMAP-hist_v2.4.2_final_nr, HISTCR": {
        "color": "rgb(0, 0, 0)",
        "dash": "dot",
        "width": 3,
    },
    "PRIMAP-hist_v2.4.2_final_nr, HISTTP": {
        "color": "rgb(166, 166, 166)",
        "dash": "dot",
        "width": 3,
    },
    "PRIMAP-hist_v2.5_final_nr, HISTCR": {
        "color": "rgb(0, 0, 0)",
        "dash": "solid",
        "width": 3,
    },
    "PRIMAP-hist_v2.5_final_nr, HISTTP": {
        "color": "rgb(166, 166, 166)",
        "dash": "solid",
        "width": 3,
    },
    "RCP hist, HISTORY": {"color": "rgb(50,50,255)", "dash": "solid"},
    "UNFCCC NAI, 231015": {"color": "rgb(255,0,0)", "dash": "solid"},
}
"""Layout for the line plot in the main figure - Add new source scenarios for each release!"""

SUBENTITIES: dict[str, list[str]] = {
    "CO2": ["CO2"],
    "CH4": ["CH4"],
    "N2O": ["N2O"],
    "SF6": ["SF6"],
    "NF3": ["NF3"],
    "HFCS (SARGWP100)": ["HFCS (SARGWP100)"],
    "PFCS (SARGWP100)": ["PFCS (SARGWP100)"],
    "FGASES (SARGWP100)": ["HFCS (SARGWP100)", "PFCS (SARGWP100)", "NF3", "SF6"],
    "KYOTOGHG (SARGWP100)": ["CO2", "CH4", "N2O", "FGASES (SARGWP100)"],
    "HFCS (AR4GWP100)": ["HFCS (AR4GWP100)"],
    "PFCS (AR4GWP100)": ["PFCS (AR4GWP100)"],
    "FGASES (AR4GWP100)": ["HFCS (AR4GWP100)", "PFCS (AR4GWP100)", "NF3", "SF6"],
    "KYOTOGHG (AR4GWP100)": ["CO2", "CH4", "N2O", "FGASES (AR4GWP100)"],
    "HFCS (AR5GWP100)": ["HFCS (AR5GWP100)"],
    "PFCS (AR5GWP100)": ["PFCS (AR5GWP100)"],
    "FGASES (AR5GWP100)": ["HFCS (AR5GWP100)", "PFCS (AR5GWP100)", "NF3", "SF6"],
    "KYOTOGHG (AR5GWP100)": ["CO2", "CH4", "N2O", "FGASES (AR5GWP100)"],
    "HFCS (AR6GWP100)": ["HFCS (AR6GWP100)"],
    "PFCS (AR6GWP100)": ["PFCS (AR6GWP100)"],
    "FGASES (AR6GWP100)": ["HFCS (AR6GWP100)", "PFCS (AR6GWP100)", "NF3", "SF6"],
    "KYOTOGHG (AR6GWP100)": ["CO2", "CH4", "N2O", "FGASES (AR6GWP100)"],
}
"""Mapping between entities and their components"""

index_cols: list[str] = [
    # "source",
    # "scenario (PRIMAP-hist)",
    "SourceScen",
    "provenance",
    "area (ISO3)",
    "entity",
    "unit",
    "category (IPCC2006_PRIMAP)",
]
"""Columns to use as the index when creating stacked plots"""


def sort_source_scenario_options(
    inp_options: Iterable[str],
    lines_order: tuple[str, ...] | None = None,
) -> list[str]:
    """
    Sort source scenario options according to definition.

    Parameters
    ----------
    inp_options
        Source scenario options to sort.

    lines_order
        Definition of source scenario order.

    Returns
    -------
        Sorted source scenario options.
    """
    if lines_order is None:
        lines_order = LINES_ORDER

    out = [line for line in lines_order if line in inp_options]

    remaining_lines = [line for line in inp_options if line not in out]

    out.extend(sorted(remaining_lines))

    return out


def select_cat_children(
    parent_category: str, existing_categories: tuple[str, ...]
) -> list[str]:
    """
    Find children categories of a category.

    Parameters
    ----------
    parent_category
        The selected category.

    existing_categories
        All existing categories in the data set.

    Returns
    -------
        Children categories. If there are no children for the
        category, `parent_category` is simply returned.
    """
    parent = cc.IPCC2006_PRIMAP[parent_category]
    # There are two ways to break down category 3
    # We use the children M.AG and M.LULUCF for category 3.
    if parent_category == "3":
        children = parent.children[1]
    else:
        try:
            children = parent.children[0]
        except IndexError:
            return [parent_category]

    output_categories = [
        i.codes[0] for i in children if i.codes[0] in existing_categories
    ]

    if not output_categories:
        return [parent_category]

    return output_categories


def apply_gwp(
    inp: xr.Dataset, entity_to_match: str, unit: str = "Gg CO2 / year"
) -> xr.Dataset:
    """
    Convert all entities to the same GWP and unit.

    All entities in the dataset are converted to the same GWP and unit as
    `entity_to_match`.

    Parameters
    ----------
    inp
        Input data set.

    entity_to_match
        The entity in the data set which defines the GWP all other variables
        in `inp` should be converted to.

    unit
        Unit to convert to

    Returns
    -------
        Dataset with all variables converted to the same GWP as `entity_to_match`
        and unit converted to `unit`. If ``inp[entity_to_match]`` doesn't have a
        GWP context, ``inp`` is simply returned.
    """
    if "gwp_context" in inp[entity_to_match].attrs.keys():
        entities = inp.data_vars
        outp = inp.copy()
        for entity in entities:
            converted = outp[entity].pr.convert_to_gwp_like(inp[entity_to_match])
            outp[converted.name] = converted
            if converted.name != entity:
                # works without the str() function but mypy will complain
                outp = outp.drop_vars(str(entity))
            outp[converted.name] = outp[converted.name].pint.to(unit)

        return outp

    return inp


def create_overview_figure(  # type: ignore
    country: str,
    category: str,
    entity: str,
    dataset: xr.Dataset,
    lines_layout: dict[str, dict[str, str | int]] | None = None,
) -> go.Figure:
    """
    Create the overview (i.e. main) figure

    Parameters
    ----------
    country
        Country to show

    category
        Category to show

    entity
        Entity to show

    dataset
        Dataset from which to generate the figure

    lines_layout
        Layout for the line plot in the main figure.

    Returns
    -------
        Created figure
    """
    if lines_layout is None:
        lines_layout = LINES_LAYOUT

    iso_country = get_country_code_mapping(dataset)[country]

    with warnings.catch_warnings(action="ignore"):
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

    fig = go.Figure()

    source_scenario_sorted = sort_source_scenario_options(
        list(new_source_scenario_options)
    )

    for source_scenario in source_scenario_sorted:
        # check if layout is defined
        if source_scenario in lines_layout:
            line_layout = lines_layout[source_scenario]
        else:
            line_layout = {}  # empty dict creates random layout
        df_source_scenario = filtered_pandas.loc[
            filtered_pandas["SourceScen"] == source_scenario
        ]

        df_source_scenario = df_source_scenario.reset_index()
        # find start and end of time series for SourceScenario
        first_idx = df_source_scenario[entity].first_valid_index()
        last_idx = df_source_scenario[entity].last_valid_index()
        # check if time series has data gaps
        if any(df_source_scenario[entity].loc[first_idx:last_idx].isna()):
            mode = "lines+markers"
        else:
            mode = "lines"

        fig.add_trace(
            go.Scatter(
                x=list(df_source_scenario["time"]),
                y=list(df_source_scenario[entity]),
                mode=mode,
                marker_symbol="cross",
                marker_size=10,
                name=source_scenario,
                line=line_layout,
                # visible=self.source_scenario_visible[source_scenario],
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
    # if xyrange_data :
    #     xyrange_data_dict = json.loads(xyrange_data)
    #     fig.update_layout(
    #         xaxis=dict(
    #             range=xyrange_data_dict["xaxis"],
    #             autorange=False,
    #         ),
    #         yaxis=dict(
    #             autorange=True,
    #         ),
    #     )

    return fig


def get_category_split(  # noqa: PLR0913
    categories_to_plot: list[str],
    iso_country: str,
    category: str,
    entity: str,
    source_scenario: str,
    dataset: xr.Dataset,
) -> pd.DataFrame:
    """
    Filter the data set according to selection in the dropdowns.

    Parameters
    ----------
    categories_to_plot
        The categories to show in the plot.
    iso_country
        Country to show
    category
        Category to show
    entity
        The selected entity in the entity dropdown
    source_scenario
        Source scenario to show
    dataset
        Dataset from which to generate the figure

    Returns
    -------
        Filtered data set for category figure.
    """
    with warnings.catch_warnings(action="ignore"):
        filtered = (
            dataset[entity]
            .pr.loc[
                {
                    "category": categories_to_plot,
                    "area (ISO3)": iso_country,
                    "SourceScen": source_scenario,
                }
            ]
            .squeeze()
        )

    filtered_pandas = filtered.to_dataframe().reset_index()

    if filtered_pandas[entity].isna().all():
        # filter again but only for parent category
        with warnings.catch_warnings(action="ignore"):
            filtered = (
                dataset[entity]
                .pr.loc[
                    {
                        "category": category,
                        "area (ISO3)": iso_country,
                        "SourceScen": source_scenario,
                    }
                ]
                .squeeze()
            )

        return filtered.to_dataframe().reset_index()

    return filtered_pandas


def get_entity_split(  # noqa: PLR0913
    entities_to_plot: list[str],
    entity: str,
    dataset: xr.Dataset,
    category: str,
    source_scenario: str,
    iso_country: str,
) -> pd.DataFrame:
    """
    Filter the data set according to selection in the dropdowns.

    Parameters
    ----------
    entities_to_plot
        The entities to show in the plot
    entity
        The selected entity in the entity dropdown
    dataset
        Dataset from which to generate the figure
    category
        Category to show
    source_scenario
        Source scenario to show
    iso_country
        Country to show

    Returns
    -------
    Filtered data set for entity figure.
    """
    drop_parent = False
    if entity not in entities_to_plot:
        # need the parent entity for GWP conversion
        entities_to_plot = [*entities_to_plot, entity]
        drop_parent = True

    with warnings.catch_warnings(action="ignore"):
        filtered = dataset[entities_to_plot].pr.loc[
            {
                "category": [category],
                "area (ISO3)": [iso_country],
                "SourceScen": [source_scenario],
            }
        ]

    filtered = apply_gwp(filtered, entity)

    # Drop the parent entity out before plotting (as otherwise the
    # area plot doesn't make sense)
    # TODO! Check if there is a nicer logic for that
    if drop_parent:
        filtered = filtered.drop_vars(entity)

    with warnings.catch_warnings(action="ignore"):
        stacked = filtered.pr.to_interchange_format().melt(
            id_vars=index_cols, var_name="time", value_name="value"
        )

    # if all values are NaN
    if stacked["value"].isna().all():
        # filter again but only for parent entity
        with warnings.catch_warnings(action="ignore"):
            filtered = dataset[entity].pr.loc[
                {
                    "category": [category],
                    "area (ISO3)": [iso_country],
                    "SourceScen": [source_scenario],
                }
            ]

        filtered_df = filtered.to_dataframe().reset_index()
        stacked = filtered_df.rename(columns={entity: "value"})
        stacked["entity"] = entity

    stacked["time"] = stacked["time"].apply(pd.to_datetime)

    return stacked


def plot_stacked_area(  # noqa: PLR0913
    fig: go.Figure,
    df_plot: pd.DataFrame,
    categories_to_plot: list[str],
    entity: str,
    colors: dict[str, str],
    sub_plot: str,
    dashed: bool = False,
) -> go.Figure:
    """
    Plot stacked area chart in a figure.

    Parameters
    ----------
    fig
        The figure that should contain the stacked area plot
    df_plot
        The data frame to plot
    categories_to_plot
        The categories to plot. Only needed for category figure
    entity
        The entity to plot
    colors
        The colors for the areas in the plot
    sub_plot
        Either category or entity plot
    dashed
        If True, function will return dashed lines instead of filled areas

    Returns
    -------
        The figure with the stacked area plot
    -------

    """
    # bring df in right format for plotting
    df_plot = df_plot.set_index("time")

    if sub_plot == "entity":
        # TODO! Remove hard-coded category column name
        # TODO! Will fail for some combinations
        df_plot = pd.concat(
            [
                df_plot[df_plot["entity"] == c]["value"].rename(c)
                for c in df_plot["entity"].unique()
            ],
            axis=1,
        )
    elif sub_plot == "category":
        # If we need better performance, there's probably a pandas function for this loop
        # which may help (the loop may also not be that slow)
        # TODO! Remove hard-coded category column name
        df_plot = pd.concat(
            [
                df_plot[df_plot["category (IPCC2006_PRIMAP)"] == c][entity].rename(c)
                for c in categories_to_plot
            ],
            axis=1,
        )

    # determine where positive and negative emissions
    _df_pos = df_plot.map(lambda x: max(x, 0))
    _df_neg = df_plot.map(lambda x: min(x, 0))

    if dashed:
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
                    line=dict(color="black", width=0.5, dash="dot"),
                    text=list(_df_pos[c]),
                    customdata=list(_df_pos.index.year),
                    hovertemplate="%{customdata}, %{text:.2e}",
                    name=f"{c} dashed pos",
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
                    line=dict(color="black", width=0.5, dash="dot"),
                    showlegend=False,
                    text=list(_df_neg[c]),
                    customdata=list(_df_neg.index.year),
                    hovertemplate="%{customdata}, %{text:.2e}",
                    name=f"{c} dashed neg",
                )
            )

            upper = lower

        fig.add_trace(
            go.Scatter(
                y=df_plot.sum(axis=1),
                x=df_plot.index,
                mode="lines",
                line=dict(color="black", width=0.5, dash="dot"),
                name="total dashed",
                customdata=list(df_plot.index.year),
                hovertemplate="%{customdata}, %{y:.2e}",
            )
        )

        return fig

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

        upper = lower

    # plot line for sum
    fig.add_trace(
        go.Scatter(
            y=df_plot.sum(axis=1),
            x=df_plot.index,
            mode="lines",
            line=dict(
                color="black",
                width=3,
            ),
            name="total",
            customdata=list(df_plot.index.year),
            hovertemplate="%{customdata}, %{y:.2e}",
        )
    )

    return fig


def create_category_figure(  # type: ignore # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
    source_scenario_dashed: str,
    dataset: xr.Dataset,
) -> go.Figure:
    """
    Create the category figure.

    Parameters
    ----------
    country
        Country to show

    category
        Category to show

    entity
        Entity to show

    source_scenario
        Source scenario to show

    dataset
        Dataset from which to generate the figure

    Returns
    -------
    Created category figure.

    """
    iso_country = get_country_code_mapping(dataset)[country]

    category_options = tuple(dataset["category (IPCC2006_PRIMAP)"].to_numpy())

    categories_to_plot = sorted(select_cat_children(category, category_options))

    # get the data frame for the selected source scenario
    filtered_pandas = get_category_split(
        categories_to_plot=categories_to_plot,
        iso_country=iso_country,
        category=category,
        entity=entity,
        source_scenario=source_scenario,
        dataset=dataset,
    )

    # get the data frame for the selected reference (dashed) source scenario
    filtered_pandas_dashed = get_category_split(
        categories_to_plot=categories_to_plot,
        iso_country=iso_country,
        category=category,
        entity=entity,
        source_scenario=source_scenario_dashed,
        dataset=dataset,
    )

    # Fix for figure not loading at start
    # https://github.com/plotly/plotly.py/issues/3441
    fig = go.Figure(layout=dict(template="plotly"))

    # save xrange in case last values are NaN and cut off
    xrange = [min(filtered_pandas["time"]), max(filtered_pandas["time"])]
    # cut off nan values at end of time series (otherwise they will be plotted as zeros)
    filtered_pandas = filtered_pandas.dropna(subset=[entity])
    filtered_pandas_dashed = filtered_pandas_dashed.dropna(subset=[entity])

    # TODO do we actually need this line?
    fig = go.Figure()

    # TODO! Check different color schemes.
    # https://plotly.com/python/discrete-color/#color-sequences-in-plotly-express
    # Set colors for areas per category
    defaults = iter(px.colors.qualitative.Vivid)
    colors = {}
    for key in categories_to_plot:
        color = next(defaults)
        colors[key] = color

    # stacked area for categories
    fig = plot_stacked_area(
        fig=fig,
        df_plot=filtered_pandas,
        categories_to_plot=categories_to_plot,
        entity=entity,
        colors=colors,
        sub_plot="category",
        dashed=False,
    )

    # stacked area for categories in reference (dashed) scenario
    fig = plot_stacked_area(
        fig=fig,
        df_plot=filtered_pandas_dashed,
        categories_to_plot=categories_to_plot,
        entity=entity,
        colors=colors,
        sub_plot="category",
        dashed=True,
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

    # TODO integrate fixed xyrange later again
    # In the initial callback xyrange_data will be None
    # if xyrange_data :
    #     xyrange_data_dict = json.loads(xyrange_data)
    #     fig.update_layout(
    #         xaxis=dict(
    #             range=xyrange_data_dict["xaxis"],
    #         ),
    #     )

    return fig


def create_entity_figure(  # type: ignore # noqa: PLR0913
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
    source_scenario_dashed: str,
    dataset: xr.Dataset,
) -> go.Figure:
    """
    Create the entity figure.

    Parameters
    ----------
    country
        Country to show

    category
        Category to show

    entity
        Entity to show

    source_scenario
        Source scenario to show

    source_scenario_dashed
        Reference source scenario to show

    dataset
        Dataset from which to generate the figure

    Returns
    -------
    Created entity figure.

    """
    iso_country = get_country_code_mapping(dataset)[country]

    # Get sub-entities (can be equal to entity as well)
    entities_to_plot = sorted(SUBENTITIES[entity])

    stacked = get_entity_split(
        entities_to_plot=entities_to_plot,
        entity=entity,
        dataset=dataset,
        category=category,
        source_scenario=source_scenario,
        iso_country=iso_country,
    )

    stacked_dashed = get_entity_split(
        entities_to_plot=entities_to_plot,
        entity=entity,
        dataset=dataset,
        category=category,
        source_scenario=source_scenario_dashed,
        iso_country=iso_country,
    )

    # drop_parent = False
    # if entity not in entities_to_plot :
    #     # need the parent entity for GWP conversion
    #     entities_to_plot = [*entities_to_plot, entity]
    #     drop_parent = True
    #
    # with warnings.catch_warnings(action="ignore") :
    #     filtered = dataset[entities_to_plot].pr.loc[
    #         {
    #             "category" : [category],
    #             "area (ISO3)" : [iso_country],
    #             "SourceScen" : [source_scenario],
    #         }
    #     ]
    #
    # filtered = apply_gwp(filtered, entity)
    #
    # # Drop the parent entity out before plotting (as otherwise the
    # # area plot doesn't make sense)
    # # TODO! Check if there is a nicer logic for that
    # if drop_parent :
    #     filtered = filtered.drop_vars(entity)
    #
    # with warnings.catch_warnings(action="ignore") :
    #     stacked = filtered.pr.to_interchange_format().melt(
    #         id_vars=index_cols, var_name="time", value_name="value"
    #     )
    #
    # # if all values are NaN
    # if stacked["value"].isna().all() :
    #     # filter again but only for parent entity
    #     with warnings.catch_warnings(action="ignore") :
    #         filtered = dataset[entity].pr.loc[
    #             {
    #                 "category" : [category],
    #                 "area (ISO3)" : [iso_country],
    #                 "SourceScen" : [source_scenario],
    #             }
    #         ]
    #
    #     filtered_df = filtered.to_dataframe().reset_index()
    #     stacked = filtered_df.rename(columns={entity : "value"})
    #     stacked["entity"] = entity
    # stacked["time"] = stacked["time"].apply(pd.to_datetime)
    #
    # # save xrange in case last values are NaN and cut off
    # xrange = [min(stacked["time"]), max(stacked["time"])]
    # stacked = stacked.dropna(subset=["value"])

    # TODO! Check different color schemes.
    # https://plotly.com/python/discrete-color/#color-sequences-in-plotly-express
    # Set colors for areas per category
    defaults = iter(px.colors.qualitative.Vivid)
    colors = {}
    for key in stacked["entity"].unique():
        color = next(defaults)
        colors[key] = color

    fig = go.Figure()

    # bring df in right format for plotting
    # _df = stacked
    # _df = _df.set_index("time")
    # # TODO! There's probably a pandas function for this loop
    # # TODO! Remove hard-coded category column name
    # _df = pd.concat(
    #     [_df[_df["entity"] == c]["value"].rename(c) for c in _df["entity"].unique()],
    #     axis=1,
    # )

    # # TODO: reduce duplication with category plot in future PR
    # # determine where positive and negative emissions
    # _df_pos = _df.map(lambda x : max(x, 0))
    # _df_neg = _df.map(lambda x : min(x, 0))
    #
    #

    # save xrange in case last values are NaN and cut off
    xrange = [min(stacked["time"]), max(stacked["time"])]
    stacked = stacked.dropna(subset=["value"])

    stacked_dashed = stacked_dashed.dropna(subset=["value"])

    # Some combinations produce empty dataframes, i.e. EARTH, 4, NF3
    if stacked_dashed.empty:
        return fig

    fig = plot_stacked_area(
        fig=fig,
        df_plot=stacked,
        categories_to_plot=entities_to_plot,
        entity=entity,
        colors=colors,
        sub_plot="entity",
        dashed=False,
    )

    fig = plot_stacked_area(
        fig=fig,
        df_plot=stacked_dashed,
        categories_to_plot=entities_to_plot,
        entity=entity,
        colors=colors,
        sub_plot="entity",
        dashed=True,
    )

    # # plot all positive emissions
    # lower = [0] * len(_df_pos)
    # for c in reversed(_df_pos.columns) :
    #     if sum(_df_pos[c].fillna(0)) == 0 :
    #         continue
    #
    #     upper = _df_pos[c].fillna(0) + lower
    #     fig.add_trace(
    #         go.Scatter(
    #             y=upper,
    #             x=_df_pos.index,
    #             mode="lines",
    #             showlegend=False,
    #             line=dict(
    #                 color=colors[c],
    #                 width=0,
    #             ),
    #             text=list(_df_pos[c]),
    #             customdata=list(_df_pos.index.year),
    #             hovertemplate="%{customdata}, %{text:.2e}",
    #             name=f"{c} pos",
    #         )
    #     )
    #     fig.add_trace(
    #         go.Scatter(
    #             y=lower,
    #             x=_df_pos.index,
    #             fill="tonexty",  # fill area between trace0 and trace1
    #             fillcolor=colors[c],
    #             mode="lines",
    #             line=dict(
    #                 width=0,
    #             ),
    #             hoverinfo="skip",
    #             name=f"{c} pos",
    #         )
    #     )
    #     lower = upper
    #
    # # plot all negative emissions
    # upper = [0] * len(_df_neg)
    # for c in _df_neg.columns :
    #     if sum(_df_neg[c]) == 0 :
    #         continue
    #
    #     lower = _df_neg[c].fillna(0) + upper
    #     fig.add_trace(
    #         go.Scatter(
    #             y=upper,
    #             x=_df_neg.index,
    #             mode="lines",
    #             line=dict(
    #                 color=colors[c],
    #                 width=0,
    #             ),
    #             showlegend=False,
    #             name=f"{c} neg",
    #             text=f"Category {c}",
    #             hoverinfo="skip",
    #         )
    #     )
    #
    #     fig.add_trace(
    #         go.Scatter(
    #             y=lower,
    #             x=_df_neg.index,
    #             fill="tonexty",  # fill area between trace0 and trace1
    #             mode="lines",
    #             line=dict(
    #                 color=colors[c],
    #                 width=0,
    #             ),
    #             fillcolor=colors[c],
    #             text=list(_df_neg[c]),
    #             customdata=list(_df_neg.index.year),
    #             hovertemplate="%{customdata}, %{text:.2e}",
    #             name=f"{c} neg",
    #         )
    #     )
    #     upper = lower
    #
    # # plot line for sum
    # fig.add_trace(
    #     go.Scatter(
    #         y=_df.sum(axis=1),
    #         x=_df.index,
    #         mode="lines",
    #         line=dict(
    #             color="black",
    #             width=3,
    #         ),
    #         name="total",
    #         customdata=list(_df.index.year),
    #         hovertemplate="%{customdata}, %{y:.2e}",
    #     )
    # )

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
    # if xyrange_data:
    #     xyrange_data_dict = json.loads(xyrange_data)
    #     fig.update_layout(
    #         xaxis=dict(
    #             range=xyrange_data_dict["xaxis"],
    #         ),
    #     )

    return fig
