"""
Figure view adjustments
"""

from typing import Any

import plotly.graph_objects as go  # type: ignore
from loguru import logger


def update_xy_range(xyrange: dict[str, Any], figure: Any) -> Any:
    """
    Update the x and y range in a figure.

    Parameters
    ----------
    xyrange
        The x- and y-range to apply to the figure

    Returns
    -------
        The updated category figure.
    """
    logger.info(f"{xyrange=}")

    # Hmmm, really don't like these if statements, one for another day
    if isinstance(figure, dict):
        for axis in ["xaxis", "yaxis"]:
            if xyrange[axis] == "autorange":
                # There may be a smarter way to update the values of the dict
                figure["layout"][axis]["autorange"] = True
            else:
                figure["layout"][axis]["range"] = xyrange[axis]
                figure["layout"][axis]["autorange"] = False

    elif isinstance(figure, go.Figure):
        for axis in ["xaxis", "yaxis"]:
            if xyrange[axis] == "autorange":
                # figure["layout"][axis]["autorange"] = True
                figure.update_layout(**{axis: dict(autorange=True)})
            else:
                # figure["layout"][axis]["range"] = xyrange[axis]
                # figure["layout"][axis]["autorange"] = False
                figure.update_layout(
                    **{
                        axis: dict(
                            range=xyrange[axis],
                            autorange=False,
                        )
                    }
                )

    else:
        # I think this will help us figure out what is going on better,
        # and it's generally better practice to error if we hit an unknown path
        # than blindly continue
        raise NotImplementedError(figure)

    return figure
