"""
Define helper functions.

"""
import climate_categories as cc
import xarray as xr


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
            return []

    output_categories = [
        i.codes[0] for i in children if i.codes[0] in existing_categories
    ]

    if not output_categories:
        return [parent_category]

    return output_categories


def apply_gwp(inp: xr.Dataset, gwp_base_unit: str) -> xr.Dataset:
    """
    Convert all entities to the same GWP and unit.

    Parameters
    ----------
    inp
        The xarray data set for the visualisation.
    gwp_base_unit
        The selected entity.

    Returns
    -------
        Returns the transformed dataset.
    """
    unit = "Gg CO2 / year"
    if "gwp_context" in inp[gwp_base_unit].attrs.keys():
        entities = inp.data_vars
        outp = inp.copy()
        for entity in entities:
            outp[entity] = outp[entity].pr.convert_to_gwp_like(inp[gwp_base_unit])
            outp[entity] = outp[entity].pint.to(unit)

        return outp
    else:
        return inp
