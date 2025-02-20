"""
Dataset handling
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable

import pandas as pd
import xarray as xr
from attrs import define
from loguru import logger
from packaging.version import InvalidVersion, Version

from primap_visualisation_tool_stateless_app.iso_mapping import iso3_to_name


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


def get_entity_option_split_by_gwp_annotation(
    dataset: xr.Dataset,
    gwp_identifier: str = "GWP100",
) -> dict[str, list[str]]:
    """
    Get all available entities split by whether they have a GWP annotation

    Parameters
    ----------
    dataset
        Dataset from which to get the entity options
    gwp_identifier
        The string used to identify entities with a GWP annotation

    Returns
    -------
        All avaiable entities in the data set split by whether they have a GWP annotation
    """
    entities = get_entity_options(dataset)
    with_gwp = [gas for gas in entities if gwp_identifier in gas]
    without_gwp = [gas for gas in entities if gwp_identifier not in gas]
    return {"with_gwp": with_gwp, "without_gwp": without_gwp}


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
        country_code_mapping[iso3_to_name(code)] = code

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


def get_not_all_nan_source_scenario_dfs(
    inp: xr.Dataset, entity: str
) -> dict[str, pd.DataFrame]:
    """
    Get source-scenario :obj:`pd.DataFrame`'s for source-scenario combinations which are not all nan

    Parameters
    ----------
    inp
        Input dataset

    entity
        Entity of interest in the dataset.

    Returns
    -------
        A dictionary, where each key is the source-scenario
        and each value is a :obj:`pd.DataFrame` for the source-scenario.
        Only source-scenarios with non-nan values are included in the output.
    """
    inp_df = inp[entity].pint.dequantify().squeeze().to_dataframe().reset_index()

    res = {}
    for source_scenario, source_scen_df in inp_df.groupby("SourceScen"):
        if source_scen_df[entity].isna().all():
            continue

        # Reset index to make sure that the source scenario dataframes
        # have simple indexes rather than numbers that don't make sense.
        res[source_scenario] = source_scen_df.reset_index(drop=True)

    return res


@define
class SourceScenarioDefinition:
    """Definition of source-scenarios provided in the app's dataset"""

    primap_versions: tuple[str]
    """
    PRIMAP versions

    These should be ordered from newest to oldest.
    """

    other_source_scenarios: tuple[str, ...]
    """Other source scenarios"""

    primap_cr_suffix: str = ", HISTCR"
    """Suffix used to denote CR variants"""

    primap_tp_suffix: str = ", HISTTP"
    """Suffix used to denote TP variants"""

    @property
    def primap_scenarios(self) -> tuple[str, ...]:
        """
        PRIMAP scenarios

        These are created by combining the PRIMAP versions
        with the CR and TP suffixes.
        """
        return tuple(
            f"{version}{suffix}"
            for version in self.primap_versions
            for suffix in [self.primap_cr_suffix, self.primap_tp_suffix]
        )


def infer_source_scenarios(
    inp: xr.Dataset, primap_start_str: str = "PRIMAP-hist"
) -> SourceScenarioDefinition:
    """
    Infer source scenarios from an :obj:`xr.Dataset`

    Parameters
    ----------
    inp
        :obj:`xr.Dataset` from which to infer the source scenarios

    primap_start_str
        String that indicates that a scenario is a PRIMAP scenario

    Returns
    -------
        Inferred source scenario definition
    """
    source_scenarios = inp["SourceScen"].values.tolist()  # noqa: PD011

    other_source_scenarios = tuple(
        v for v in source_scenarios if not v.startswith(primap_start_str)
    )
    primap_variants = set(source_scenarios).difference(set(other_source_scenarios))

    primap_sources = set([v.split(",")[0] for v in primap_variants])
    primap_versions = sorted(
        [[Version(v.split("_")[1]), v] for v in primap_sources], key=lambda x: x[0]
    )

    source_scenario_definition = SourceScenarioDefinition(
        primap_versions=tuple(v[1] for v in primap_versions[::-1]),
        other_source_scenarios=tuple(sorted(other_source_scenarios)),
    )

    missing_expected_primap_scenarios = [
        v
        for v in source_scenario_definition.primap_scenarios
        if v not in source_scenarios
    ]

    if missing_expected_primap_scenarios:
        msg = f"Missing expected PRIMAP scenarios {missing_expected_primap_scenarios}. {source_scenarios=}"
        raise AssertionError(msg)

    return source_scenario_definition


def group_other_source_scenarios(inp: tuple[str, ...]) -> tuple[tuple[str, ...], ...]:
    """
    Group other source-scenarios

    This is basically guess work, so won't be perfect, but is a helpful starting point.

    Parameters
    ----------
    inp
        Input source-scenarios to group

    Returns
    -------
        Grouped source-scenarios.
        Each element is a group, sorted in order from oldest to newest version.
    """
    stem_groups = defaultdict(list)
    for source_scen in inp:
        stem = source_scen.split(" ")[0]
        stem_groups[stem].append(source_scen)

    res: list[tuple[str, ...]] = []
    for stem_group in sorted(stem_groups.keys()):
        stem_group_vals = stem_groups[stem_group]
        if len(stem_group_vals) == 1:
            res.append((stem_group_vals[0],))

        else:
            res.append(attempt_to_sort_source_scenarios_in_group(stem_group_vals))

    return tuple(res)


def attempt_to_sort_source_scenarios_in_group(inp: Iterable[str]) -> tuple[str, ...]:
    """
    Attempt to sort the source-scenarios in a group

    Parameters
    ----------
    inp
        Source-scenarios to sort

    Returns
    -------
        Sorted source-scenarios.
        If no obvious pattern can be found, the source-scenarios are simply sorted and returned.
    """
    try:
        versions_names: list[tuple[Version, str]] = [
            (Version(v.split(" ")[1].strip(",")), v) for v in inp
        ]
    except InvalidVersion:
        logger.warning(
            "Source-scenarios will simply be sorted "
            f"because we could not infer any versions for sorting {inp}"
        )
        return tuple(sorted(inp))

    versions_names_sorted = sorted(versions_names, key=lambda x: x[0])

    res = tuple([v[1] for v in versions_names_sorted])

    return res


def filter_entities_by_gwp(
    all_entity_options: dict[str, list[str]],
    allowed_gwp: list[str],
) -> list[str]:
    """
    Filter the entity dropdown according to the selected GWP

    Parameters
    ----------
    gwp
        One or more selected GWP(s) in the GWP dropdown menu

    Returns
    -------
        The filtered entity dropdown options
    """
    if not allowed_gwp:
        return sort_entity_options(
            all_entity_options["with_gwp"] + all_entity_options["without_gwp"]
        )

    new_entity_options = []
    for entity in all_entity_options["with_gwp"]:
        if any(gwp in entity for gwp in allowed_gwp):
            new_entity_options.append(entity)

    return sort_entity_options(all_entity_options["without_gwp"] + new_entity_options)


def sort_entity_options(
    entity_options: list[str] | tuple[str],
    preferred_order: tuple[str, ...] = (
        "KYOTOGHG",
        "CO2",
        "CH4",
        "N2O",
        "FGASES",
        "HFCS",
        "PFCS",
        "SF6",
        "NF3",
    ),
) -> list[str]:
    """
    Sort entity options

    Parameters
    ----------
    entity_options
        Entity options to sort

    preferred_order
        The preferred order of the entities

    Returns
    -------
        Sorted entity options
    """

    def sort_key(item: str) -> int:
        for index, preferred in enumerate(preferred_order):
            if preferred in item:
                return index
        return len(preferred_order)

    return sorted(entity_options, key=sort_key)
