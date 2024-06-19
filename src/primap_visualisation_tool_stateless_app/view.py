"""
Share view settings across figures.
"""

import json
from typing import Any


def update_x_range(fig: Any, xyrange: dict[str, list[str | float | bool]]) -> Any:
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


def update_y_range(fig: Any, xyrange: dict[str, list[str | float]]) -> Any:
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


def update_xy_range(xyrange: str, figure: dict[Any, Any]) -> Any:
    """
    Update xy-range of entity figure according to stored xy-range.

    Parameters
    ----------
    xyrange_data
        X- and y-axis range to which the figure is to be updated.
    figure
        The figure to be updated.

    Returns
    -------
        Updated figure.
    """
    layout_data = json.loads(xyrange)

    fig = figure

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
        fig = update_x_range(fig, layout_data)
        fig = update_y_range(fig, layout_data)

    return fig


def get_xyrange_from_figure(
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
