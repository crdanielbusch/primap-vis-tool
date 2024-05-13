"""
Figure handling and creation
"""
import warnings
from collections import OrderedDict

import climate_categories as cc
import pandas as pd
import plotly.express as px  # type: ignore
import plotly.graph_objects as go  # type: ignore
import xarray as xr
from attrs import define
from loguru import logger

from primap_visualisation_tool_stateless_app.dataset_handling import (
    SourceScenarioDefinition,
    get_country_code_mapping,
    group_other_source_scenarios,
    infer_source_scenarios,
)


@define
class PlottingConfig:
    """Plotting config"""

    source_scenario_settings: OrderedDict[str, dict[str, str | int]]
    """
    Plotting settings to use for each source-scenario

    The order of keys in the dictionary determines the order of plotting
    (first key is plotted first)
    """


PLOTTING_CONFIG: PlottingConfig | None = None
"""Config to use while plotting"""


def create_default_plotting_config(  # noqa: PLR0913
    source_scenarios: SourceScenarioDefinition,
    primap_cr_colour: str = "rgb(0, 0, 0)",
    primap_tp_colour: str = "rgb(166, 166, 166)",
    primap_width: int = 3,
    new_dash: str = "solid",
    old_dashes: tuple[str, ...] = ("dot", "dash", "longdash", "dashdot", "longdashdot"),
    colour_palette: tuple[str, ...] = (
        "rgb(0, 0, 255)",
        "rgb(50, 200, 255)",
        "rgb(0, 0, 255)",
        "rgb(60, 179, 113)",
        "rgb(238, 130, 238)",
        "rgb(255, 165, 0)",
        "rgb(106, 90, 205)",
        "rgb(50, 0, 255)",
        "rgb(100, 0, 255)",
        "rgb(150, 0, 255)",
        "rgb(200, 0, 255)",
        "rgb(50, 50, 255)",
        "rgb(255, 0, 0)",
    ),
) -> PlottingConfig:
    """
    Create default plotting config

    Parameters
    ----------
    source_scenarios
        Source-scenario definition

    primap_cr_colour
        Colour to use for PRIMAP country-reported

    primap_tp_colour
        Colour to use for PRIMAP third-party

    primap_width
        Width to use when plotting PRIMAP data

    new_dash
        Dash to use for the new version of source-scenarios

    old_dashes
        Dashes to use for the old version(s) of source-scenarios.

    colour_palette
        Colours to cycle through for the non-PRIMAP source-scenarios

    Returns
    -------
        Default plotting config
    """
    source_scenario_groups = group_other_source_scenarios(
        source_scenarios.other_source_scenarios
    )

    source_scenario_settings_non_primap = OrderedDict()
    for i, source_scenario_group in enumerate(source_scenario_groups):
        colour = colour_palette[i % len(colour_palette)]
        for j, source_scenario in enumerate(source_scenario_group[::-1]):
            if j == 0:
                dash = new_dash
            else:
                dash = old_dashes[(j - 1) % len(old_dashes)]

            source_scenario_settings_non_primap[source_scenario] = {
                "color": colour,
                "dash": dash,
            }

    return PlottingConfig(
        source_scenario_settings=OrderedDict(
            {
                source_scenarios.primap_new_cr: {
                    "color": primap_cr_colour,
                    "dash": new_dash,
                    "width": primap_width,
                },
                source_scenarios.primap_new_tp: {
                    "color": primap_tp_colour,
                    "dash": new_dash,
                    "width": primap_width,
                },
                source_scenarios.primap_old_cr: {
                    "color": primap_cr_colour,
                    "dash": old_dashes[0],
                    "width": primap_width,
                },
                source_scenarios.primap_old_tp: {
                    "color": primap_tp_colour,
                    "dash": old_dashes[0],
                    "width": primap_width,
                },
                **source_scenario_settings_non_primap,
            }
        )
    )


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
    plotting_config: PlottingConfig | None = None,
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

    plotting_config
        Plotting configuration to use

    Returns
    -------
        Created figure
    """
    if plotting_config is None:
        if PLOTTING_CONFIG is not None:
            plotting_config = PLOTTING_CONFIG

        else:
            msg = (
                "plotting_config not supplied and PLOTTING_CONFIG is None. "
                "plotting_config will be created now. "
                "Consider creating it before running the app."
            )
            logger.warning(msg)
            source_scenario_definition = infer_source_scenarios(dataset)
            plotting_config = create_default_plotting_config(
                source_scenarios=source_scenario_definition
            )

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

    source_scenario_sorted = []
    if plotting_config is not None:
        source_scenario_sorted = [
            k
            for k in plotting_config.source_scenario_settings.keys()
            if k in new_source_scenario_options
        ]

    for k in new_source_scenario_options:
        if k not in source_scenario_sorted:
            source_scenario_sorted.append(k)

    for source_scenario in source_scenario_sorted:
        # check if layout is defined
        if (
            plotting_config is not None
            and source_scenario in plotting_config.source_scenario_settings
        ):
            line_layout = plotting_config.source_scenario_settings[source_scenario]
        else:
            # Provide no settings to dash
            line_layout = {}

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


def create_category_figure(  # type: ignore
    country: str,
    category: str,
    entity: str,
    source_scenario: str,
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

    categories_plot = sorted(select_cat_children(category, category_options))

    with warnings.catch_warnings(action="ignore"):
        filtered = (
            dataset[entity]
            .pr.loc[
                {
                    "category": categories_plot,
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

        filtered_pandas = filtered.to_dataframe().reset_index()

    # Fix for figure not loading at start
    # https://github.com/plotly/plotly.py/issues/3441
    fig = go.Figure(layout=dict(template="plotly"))

    # save xrange in case last values are NaN and cut off
    xrange = [min(filtered_pandas["time"]), max(filtered_pandas["time"])]
    filtered_pandas = filtered_pandas.dropna(subset=[entity])

    # bring df in right format for plotting
    _df = filtered_pandas
    _df = _df.set_index("time")
    # If we need better performance, there's probably a pandas function for this loop
    # which may help (the loop may also not be that slow)
    # TODO! Remove hard-coded category column name
    _df = pd.concat(
        [
            _df[_df["category (IPCC2006_PRIMAP)"] == c][entity].rename(c)
            for c in categories_plot
        ],
        axis=1,
    )

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
    # if xyrange_data :
    #     xyrange_data_dict = json.loads(xyrange_data)
    #     fig.update_layout(
    #         xaxis=dict(
    #             range=xyrange_data_dict["xaxis"],
    #         ),
    #     )

    return fig


def create_entity_figure(  # type: ignore
    country: str, category: str, entity: str, source_scenario: str, dataset: xr.Dataset
) -> go.Figure:
    """
    Update the overview figure based on the input in the dropdown menus.

    Returns
    -------
        Entity figure.
    """
    iso_country = get_country_code_mapping(dataset)[country]

    entities_to_plot = sorted(SUBENTITIES[entity])

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

    # save xrange in case last values are NaN and cut off
    xrange = [min(stacked["time"]), max(stacked["time"])]
    stacked = stacked.dropna(subset=["value"])

    # bring df in right format for plotting
    _df = stacked
    _df = _df.set_index("time")
    # TODO! There's probably a pandas function for this loop
    # TODO! Remove hard-coded category column name
    _df = pd.concat(
        [_df[_df["entity"] == c]["value"].rename(c) for c in _df["entity"].unique()],
        axis=1,
    )

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
    # if xyrange_data:
    #     xyrange_data_dict = json.loads(xyrange_data)
    #     fig.update_layout(
    #         xaxis=dict(
    #             range=xyrange_data_dict["xaxis"],
    #         ),
    #     )

    return fig
