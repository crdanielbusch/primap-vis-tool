"""
Figure view adjustments
"""
from typing import Any

from loguru import logger


def update_xy_range(xyrange: dict[str, Any], figure: Any) -> Any:
    """
    TODO: write
    """
    logger.info(f"{xyrange=}")
    for axis in ["xaxis", "yaxis"]:
        if xyrange[axis] == "autorange":
            update_value = {axis: {"autorange": True}}
        else:
            update_value = {axis: {"range": xyrange[axis], "autorange": False}}

        # Hmmm, really don't like these if statements, one for another day
        if isinstance(figure, dict):
            figure["layout"].update(**update_value)

        else:
            figure.update_layout(**update_value)  # type: ignore

    return figure
