"""
Country mapping handling
"""

from __future__ import annotations

import pycountry


def iso3_to_name(in_iso3: str) -> str:
    """
    Convert ISO3 code to name

    Parameters
    ----------
    in_iso3
        Country ISO3 code

    Returns
    -------
        country name or country group name
    """
    try:
        return str(pycountry.countries.get(alpha_3=in_iso3).name)
    except AttributeError:
        # use input as name if pycountry cannot find a match
        # (e.g. EARTH)
        return in_iso3


def name_to_iso3(in_name: str) -> str:
    """
    Convert country name to ISO3 code

    Parameters
    ----------
    in_name
        country name or country group name

    Returns
    -------
        Country ISO3 code
    """
    try:
        return str(pycountry.countries.get(name=in_name).alpha_3)
    except AttributeError:
        # use input as ISO3 if pycountry cannot find a match
        # (e.g. EARTH)
        return in_name
