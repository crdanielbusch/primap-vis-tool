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


def apply_gwp(
    inp: xr.Dataset, entity_to_match: str, unit: str = "Gg CO2 / year"
) -> xr.Dataset:
    """
    Convert all entities to the same GWP and unit.

    All entities in the dataset are converted to the same GWP and unit as
    `entity_to_match`.

    Parameters
    ----------
    inp
        Input data set.

    entity_to_match
        The entity in the data set which defines the GWP all other variables
        in `inp` should be converted to.

    unit
        Unit to convert to

    Returns
    -------
        Dataset with all variables converted to the same GWP as `entity_to_match`
        and unit converted to `unit`.
    """
    if "gwp_context" in inp[entity_to_match].attrs.keys():
        entities = inp.data_vars
        outp = inp.copy()
        for entity in entities:
            converted = outp[entity].pr.convert_to_gwp_like(inp[entity_to_match])
            outp[converted.name] = converted
            if converted.name != entity:
                # works without the str() function bit mypy will complain
                outp = outp.drop_vars(str(entity))
            outp[converted.name] = outp[converted.name].pint.to(unit)

        return outp

    return inp
