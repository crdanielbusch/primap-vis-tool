"""
Dropdown defaults
"""
from attrs import define


@define
class DropdownDefaults:
    """
    Default values for dropdowns
    """

    country: str
    """Default country"""

    category: str
    """Default category"""

    entity: str
    """Default entity"""

    gwp: str
    """Default gwp"""


DROPDOWN_DEFAULTS: DropdownDefaults | None = None


def get_dropdown_defaults() -> DropdownDefaults:
    """
    Get the default values for dropdown

    Returns
    -------
        Object that holds the default values for dropdowns
    """
    if DROPDOWN_DEFAULTS is None:
        msg = "Dropdown defaults have not been set yet"
        raise ValueError(msg)

    return DROPDOWN_DEFAULTS
