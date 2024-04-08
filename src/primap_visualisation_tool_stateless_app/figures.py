"""
Figure handling and creation
"""
import warnings
from collections.abc import Iterable
from typing import Union

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

    out = []

    for line in lines_order:
        if line in inp_options:
            out.append(line)

    remaining_lines = [line for line in inp_options if line not in out]
    out.extend(sorted(remaining_lines))

    return out


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
