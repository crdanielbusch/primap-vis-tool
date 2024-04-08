"""
Figure handling and creation
"""
import warnings

import plotly.graph_objects as go  # type: ignore
import xarray as xr

from primap_visualisation_tool_stateless_app.dataset_handling import (
    get_country_code_mapping,
    get_source_scenario_options,
)


def create_overview_figure(
    country: str, category: str, entity: str, dataset: xr.Dataset
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

    Returns
    -------
        Created figure
    """
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

    fig = go.Figure()

    source_scenario_sorted = list(get_source_scenario_options(dataset))
    # move primap source scenarios to the front of the list
    # in the same order as specified in LINES_ORDER
    # for i in [j for j in LINES_ORDER if j in self.source_scenario_options] :
    #     source_scenario_sorted.insert(
    #         0, source_scenario_sorted.pop(source_scenario_sorted.index(i))
    #     )

    for source_scenario in source_scenario_sorted:
        # check if layout is defined
        # if source_scenario in LINES_LAYOUT :
        #     line_layout = LINES_LAYOUT[source_scenario]
        # else :
        #     line_layout = {}  # empty dict creates random layout
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
