"""
Dataset handling
"""
from __future__ import annotations

import pycountry
import xarray as xr


def get_country_start(
    dataset: xr.Dataset, preferred_starting_country: str = "EARTH"
) -> str:
    country_options = get_country_options(dataset)
    if preferred_starting_country in country_options:
        return preferred_starting_country

    return country_options[0]


def get_country_options(dataset: xr.Dataset) -> tuple[str, ...]:
    country_code_mapping = get_country_code_mapping(dataset)

    return tuple(country_code_mapping.keys())


def get_country_code_mapping(dataset: xr.Dataset) -> dict[str, str]:
    all_codes = dataset.coords["area (ISO3)"].to_numpy()
    country_code_mapping = {}
    for code in all_codes:
        try:
            country_code_mapping[pycountry.countries.get(alpha_3=code).name] = code

        # use ISO3 code as name if pycountry cannot find a match
        except Exception:
            # TODO: implement custom mapping later (Johannes)
            country_code_mapping[code] = code

    return country_code_mapping
