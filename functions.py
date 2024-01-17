"""
Define helper functions.

"""
import climate_categories as cc


def select_cat_children(
    parent_category: str, existing_categories: list[str]
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
        Children categories.
    """
    parent = cc.IPCC2006_PRIMAP[parent_category]
    # There two ways to break down category 3
    # We use the children M.AG and M.LULUCF for category 3.
    if parent_category == "3":
        children = parent.children[1]
    else:
        try:
            children = parent.children[0]
        except IndexError:
            return parent_category

    output_categories = [
        i.codes[0] for i in children if i.codes[0] in existing_categories
    ]

    if not output_categories:
        return parent_category

    return output_categories
