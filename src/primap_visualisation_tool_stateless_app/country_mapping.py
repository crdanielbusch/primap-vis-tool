"""
Country mapping handling
"""

from __future__ import annotations

import pycountry


def country_iso3_to_name(country_iso3: str) -> str:
    """
    Convert country ISO3 code to name

    Parameters
    ----------
    country_iso3
        Country ISO3 code

    Returns
    -------
        Country name
    """
    try:
        return pycountry.countries.get(alpha_3=country_iso3).name
    except AttributeError:
        # use input as name if pycountry cannot find a match
        # (e.g. EARTH)
        # TODO: implement custom mapping later (Johannes)
        return country_iso3


def country_name_to_iso3(country: str) -> str:
    """
    Convert country name to ISO3 code

    Parameters
    ----------
    country
        Country name

    Returns
    -------
        Country ISO3 code
    """
    try:
        return pycountry.countries.get(name=country).alpha_3
    except AttributeError:
        # use input as ISO3 if pycountry cannot find a match
        # (e.g. EARTH)
        # TODO: implement custom mapping later (Johannes)
        return country
