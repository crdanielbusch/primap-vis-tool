"""
Figure view adjustments
"""

from typing import Any

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
        # figure["layout"].update(**update_value)
        for axis in ["xaxis", "yaxis"]:
            if xyrange[axis] == "autorange":
                # There may be a smarter way to update the values of the dict
                # without removing 'title' and 'type'
                figure["layout"][axis]["autorange"] = True
            else:
                figure["layout"][axis]["range"] = xyrange[axis]
                figure["layout"][axis]["autorange"] = False
    else:
        print("Figure not a dict")
        # figure.update_layout(**update_value)
    return figure
