from typing import Any


def update_xy_range(xyrange: dict[str, Any], figure: dict[Any, Any]) -> Any:
    """
    TODO: write
    """
    for axis in ["xaxis", "yaxis"]:
        if xyrange[axis] == "autorange":
            figure["layout"].update(**{axis: {"autorange": True}})  # type: ignore
        else:
            figure["layout"].update(
                **{axis: {"range": xyrange[axis], "autorange": False}}
            )

    return figure
