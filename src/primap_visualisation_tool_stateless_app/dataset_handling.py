"""
Dataset handling
"""
from __future__ import annotations

import pycountry
import xarray as xr


def get_country_start(
    dataset: xr.Dataset, preferred_starting_country: str = "EARTH"
) -> str:
    """
    Get starting country for a dataset

    Parameters
    ----------
    dataset
        Dataset for which to get the starting country

    preferred_starting_country
        Preferred starting country. If this is available, we use it,
        otherwise we use the first country returned from
        :func:`get_country_options`.

    Returns
    -------
        Starting country to use for ``dataset``.
    """
    country_options = get_country_options(dataset)
    if preferred_starting_country in country_options:
        return preferred_starting_country

    return country_options[0]


def get_country_options(dataset: xr.Dataset) -> tuple[str, ...]:
    """
    Get country options

    Parameters
    ----------
    dataset
        Dataset from which to get the country options

    Returns
    -------
        Sorted country options within the dataset
    """
    country_code_mapping = get_country_code_mapping(dataset)

    return tuple(sorted(country_code_mapping.keys()))


def get_category_start(
    dataset: xr.Dataset, preferred_starting_category: str = "M.0.EL"
) -> str:
    """
    Get starting category for a dataset

    Parameters
    ----------
    dataset
        Dataset for which to get the starting category

    preferred_starting_category
        Preferred starting category. If this is available, we use it,
        otherwise we use the first category returned from
        :func:`get_category_options`.

    Returns
    -------
        Starting category to use for ``dataset``.
    """
    category_options = get_category_options(dataset)
    if preferred_starting_category in category_options:
        return preferred_starting_category

    return category_options[0]


def get_category_options(dataset: xr.Dataset) -> tuple[str, ...]:
    """
    Get category options

    Parameters
    ----------
    dataset
        Dataset from which to get the category options

    Returns
    -------
        Sorted category options within the dataset
    """
    return tuple(sorted(dataset["category (IPCC2006_PRIMAP)"].to_numpy()))


def get_entity_start(
    dataset: xr.Dataset, preferred_starting_entity: str = "CO2"
) -> str:
    """
    Get starting entity for a dataset

    Parameters
    ----------
    dataset
        Dataset for which to get the starting category

    preferred_starting_entity
        Preferred starting entity. If this is available, we use it,
        otherwise we use the first entity returned from
        :func:`get_entity_options`.

    Returns
    -------
        Starting entity to use for ``dataset``.
    """
    entity_options = get_entity_options(dataset)
    if preferred_starting_entity in entity_options:
        return preferred_starting_entity

    return entity_options[0]


def get_entity_options(dataset: xr.Dataset) -> tuple[str, ...]:
    """
    Get entity options

    Parameters
    ----------
    dataset
        Dataset from which to get the entity options

    Returns
    -------
        Sorted entity options within the dataset
    """
    return tuple(sorted(str(i) for i in dataset.data_vars))


def get_country_code_mapping(dataset: xr.Dataset) -> dict[str, str]:
    """
    Get mapping from country names to country codes

    Parameters
    ----------
    dataset
        Dataset for which to get the mapping.

    Returns
    -------
        Mapping from country names to country codes for ``dataset``.
    """
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


def get_source_scenario_options(dataset: xr.Dataset) -> tuple[str, ...]:
    """
    Get available source scenario options from dataset.

    Parameters
    ----------
    dataset
        Dataset for which to get the source scenario options.

    Returns
    -------
        All available source scenario options.

    """
    return tuple(sorted(dataset.coords["SourceScen"].to_numpy()))


def get_source_scenario_start(
    dataset: xr.Dataset,
    preferred_starting_source_scenario: str = "PRIMAP-hist_v2.5_final_nr, HISTCR",
) -> str:
    """
    Get starting source scenario.

    Parameters
    ----------
    dataset
        Dataset for which to get the source scenario options.

    preferred_starting_source_scenario
        Preferred starting source scenario. If this is available, we use it,
        otherwise we use the first source scenario returned from
        :func:`get_source_scenario_options`.

    Returns
    -------
        Starting source scenario to use for ``dataset``
    """
    source_scenario_options = get_source_scenario_options(dataset)
    if preferred_starting_source_scenario in source_scenario_options:
        return preferred_starting_source_scenario

    return source_scenario_options[0]
