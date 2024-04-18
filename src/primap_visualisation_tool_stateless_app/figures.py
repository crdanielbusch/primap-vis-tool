"""
Figure handling and creation
"""
import warnings
from collections.abc import Iterable
from typing import Union
import pandas as pd
import plotly.graph_objects as go  # type: ignore
import xarray as xr
import plotly.express as px  # type: ignore
import climate_categories as cc
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

LINES_LAYOUT: dict[str, dict[str, Union[str, int]]] = {
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


def sort_source_scenario_options(
    inp_options: Iterable[str],
    lines_order: tuple[str, ...] = None,
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

def create_overview_figure(
    country: str,
    category: str,
    entity: str,
    dataset: xr.Dataset,
    lines_layout: Union[dict[str, dict[str, Union[str, int]]], None] = None,
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



def create_category_figure(
        country: str,
        category: str,
        entity: str,
        source_scenario : str,
        dataset: xr.Dataset,
) -> go.Figure :

    iso_country = get_country_code_mapping(dataset)[country]

    # TODO This should go somewhere else I guess
    category_options = tuple(dataset["category (IPCC2006_PRIMAP)"].to_numpy())

    categories_plot = select_cat_children(category, category_options)

    with warnings.catch_warnings(action="ignore") :  # type: ignore
        filtered = (
            dataset[entity]
            .pr.loc[
                {
                    "category" : categories_plot,
                    "area (ISO3)" : iso_country,
                    "SourceScen" : source_scenario,
                }
            ]
            .squeeze()
        )

    filtered_pandas = filtered.to_dataframe().reset_index()

    if filtered_pandas[entity].isna().all() :
        # filter again but only for parent category
        with warnings.catch_warnings(action="ignore") :  # type: ignore
            filtered = (
                dataset[entity]
                .pr.loc[
                    {
                        "category" : category,
                        "area (ISO3)" : iso_country,
                        "SourceScen" : source_scenario,
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
    _df_pos = _df.map(lambda x : max(x, 0))
    _df_neg = _df.map(lambda x : min(x, 0))

    # TODO! Check different color schemes.
    # https://plotly.com/python/discrete-color/#color-sequences-in-plotly-express
    # Set colors for areas per category
    defaults = iter(px.colors.qualitative.Vivid)
    colors = {}
    for key in _df.columns :
        color = next(defaults)
        colors[key] = color

    fig = go.Figure()

    # plot all positive emissions
    lower = [0] * len(_df_pos)
    for c in reversed(_df_pos.columns) :
        if sum(_df_pos[c].fillna(0)) == 0 :
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
    for c in _df_neg.columns :
        if sum(_df_neg[c]) == 0 :
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