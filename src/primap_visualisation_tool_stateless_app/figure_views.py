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

    # Hmmm, really don't like these if statements, one for another day
    if isinstance(figure, dict):
        # figure["layout"].update(**update_value)
        for axis in ["xaxis", "yaxis"]:
            if xyrange[axis] == "autorange":
                # update_value = {axis : {"autorange" : True}}
                figure["layout"][axis]["autorange"] = True
            else:
                # update_value = {axis : {"range" : xyrange[axis], "autorange" : False}}
                figure["layout"][axis]["range"] = xyrange[axis]
                figure["layout"][axis]["autorange"] = False
    else:
        pass
        # figure.update_layout(**update_value)
    print("Updated figure")
    print(f"{figure['layout']['xaxis']=}")
    print(f"{figure['layout']['yaxis']=}")
    return figure
