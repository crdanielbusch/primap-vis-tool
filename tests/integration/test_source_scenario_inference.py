"""
Tests of our ability to infer source-scenarios based on input data
"""

from __future__ import annotations

import numpy as np
import numpy.typing as npt
import pytest
import xarray as xr

from primap_visualisation_tool_stateless_app.dataset_handling import (
    infer_source_scenarios,
)


def create_testing_dataset(
    source_scenarios: tuple[str, ...] = ("PRIMAP_hist_2.5.1", "RCMIP", "EDGAR"),
    dimensions: tuple[str, ...] = (
        "time",
        "category (IPCC2006_PRIMAP)",
        "area (ISO3)",
        "SourceScen",
    ),
    categories: tuple[str, ...] = ("1", "2"),
    area: tuple[str, ...] = ("ABW", "AFG"),
    time: npt.NDArray[np.datetime64] = np.array(
        ["2000-01-01", "2001-01-01", "2002-01-01"], dtype="datetime64"
    ),
) -> xr.Dataset:
    array_shape = [len(v) for v in [time, categories, area, source_scenarios]]
    array_n_elements = np.prod(array_shape)

    co2 = np.arange(array_n_elements).reshape(array_shape)
    hfcs = 1e-3 * np.arange(array_n_elements).reshape(array_shape)

    test_ds = xr.Dataset(
        data_vars={"CO2": (dimensions, co2), "HFCS (SARGWP100)": (dimensions, hfcs)},
        coords={
            "category (IPCC2006_PRIMAP)": list(categories),
            "area (ISO3)": list(area),
            "SourceScen": list(source_scenarios),
            "time": time,
        },
        attrs={"area": "area (ISO3)", "cat": "category (IPCC2006_PRIMAP)"},
    )

    return test_ds


@pytest.mark.parametrize(
    [
        "source_scenarios",
        "exp_primap_old_cr",
        "exp_primap_old_tp",
        "exp_primap_new_cr",
        "exp_primap_new_tp",
        "exp_other_source_scenarios",
    ],
    (
        pytest.param(
            (
                "PRIMAP-hist_v2.5_final_nr, HISTCR",
                "PRIMAP-hist_v2.5_final_nr, HISTTP",
                "RCMIP v2.5.1",
                "RCMIP v3.2",
                "EDGAR",
                "PRIMAP-hist_v2.4.2_final_nr, HISTCR",
                "PRIMAP-hist_v2.4.2_final_nr, HISTTP",
            ),
            "PRIMAP-hist_v2.4.2_final_nr, HISTCR",
            "PRIMAP-hist_v2.4.2_final_nr, HISTTP",
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "PRIMAP-hist_v2.5_final_nr, HISTTP",
            tuple(
                ("EDGAR",),
                ("RCMIP v2.5.1", "RCMIP v3.2"),
            ),
            id="basic",
        ),
        pytest.param(
            (
                "SSPs",
                "PRIMAP-hist_v2.5_final_nr, HISTCR",
                "PRIMAP-hist_v2.5_final_nr, HISTTP",
                "RCMIP",
                "EDGAR",
                "PRIMAP-hist_v3.0-alpha_final_nr, HISTCR",
                "PRIMAP-hist_v3.0-alpha_final_nr, HISTTP",
                "Andrews",
            ),
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "PRIMAP-hist_v2.5_final_nr, HISTTP",
            "PRIMAP-hist_v3.0-alpha_final_nr, HISTCR",
            "PRIMAP-hist_v3.0-alpha_final_nr, HISTTP",
            tuple(
                ("Andrews",),
                ("EDGAR",),
                ("RCMIP",),
                ("SSPs",),
            ),
            id="alpha_release",
        ),
        pytest.param(
            (
                "SSPs",
                "PRIMAP-hist_v2.5_final_nr, HISTCR",
                "PRIMAP-hist_v2.5_final_nr, HISTTP",
                "RCMIP",
                "EDGAR",
                "PRIMAP-hist_v3.0-beta_final_nr, HISTCR",
                "PRIMAP-hist_v3.0-beta_final_nr, HISTTP",
                "Andrews",
            ),
            "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "PRIMAP-hist_v2.5_final_nr, HISTTP",
            "PRIMAP-hist_v3.0-beta_final_nr, HISTCR",
            "PRIMAP-hist_v3.0-beta_final_nr, HISTTP",
            tuple(
                ("Andrews",),
                ("EDGAR",),
                ("RCMIP",),
                ("SSPs",),
            ),
            id="beta_release",
        ),
        pytest.param(
            (
                "SSPs",
                "PRIMAP-hist_v3.0-alpha_final_nr, HISTTP",
                "RCMIP",
                "PRIMAP-hist_v3.0-beta_final_nr, HISTCR",
                "PRIMAP-hist_v3.0-alpha_final_nr, HISTCR",
                "EDGAR",
                "PRIMAP-hist_v3.0-beta_final_nr, HISTTP",
                "Andrews",
            ),
            "PRIMAP-hist_v3.0-alpha_final_nr, HISTCR",
            "PRIMAP-hist_v3.0-alpha_final_nr, HISTTP",
            "PRIMAP-hist_v3.0-beta_final_nr, HISTCR",
            "PRIMAP-hist_v3.0-beta_final_nr, HISTTP",
            tuple(
                ("Andrews",),
                ("EDGAR",),
                ("RCMIP",),
                ("SSPs",),
            ),
            id="alpha_vs_beta_release",
        ),
        pytest.param(
            (
                "SSPs",
                "PRIMAP-hist_v3.0_final_nr, HISTTP",
                "RCMIP v2.4, SSP126",
                "RCMIP v2.5, SSP126",
                "PRIMAP-hist_v3.0_final_nr, HISTCR",
                "PRIMAP-hist_v3.1_final_nr, HISTCR",
                "PRIMAP-hist_v3.1_final_nr, HISTTP",
                "Andrews, History",
            ),
            "PRIMAP-hist_v3.0_final_nr, HISTCR",
            "PRIMAP-hist_v3.0_final_nr, HISTTP",
            "PRIMAP-hist_v3.1_final_nr, HISTCR",
            "PRIMAP-hist_v3.1_final_nr, HISTTP",
            tuple(
                ("Andrews, History",),
                ("RCMIP v2.4, SSP126", "RCMIP v2.5, SSP126"),
                ("SSPs",),
            ),
            id="other_source_scenarios_inference_version_string",
        ),
        pytest.param(
            (
                "SSPs",
                "PRIMAP-hist_v3.0_final_nr, HISTTP",
                "PRIMAP-hist_v3.0_final_nr, HISTCR",
                "PRIMAP-hist_v3.1_final_nr, HISTCR",
                "EDGAR 2022, History",
                "EDGAR 2023, History",
                "PRIMAP-hist_v3.1_final_nr, HISTTP",
                "Andrews, History",
            ),
            "PRIMAP-hist_v3.0_final_nr, HISTCR",
            "PRIMAP-hist_v3.0_final_nr, HISTTP",
            "PRIMAP-hist_v3.1_final_nr, HISTCR",
            "PRIMAP-hist_v3.1_final_nr, HISTTP",
            tuple(
                ("Andrews, History",),
                ("EDGAR 2022, History", "EDGAR 2023, History"),
                ("SSPs",),
            ),
            id="other_source_scenarios_inference_year",
        ),
        pytest.param(
            (
                "SSPs",
                "PRIMAP-hist_v3.0_final_nr, HISTTP",
                "PRIMAP-hist_v3.0_final_nr, HISTCR",
                "PRIMAP-hist_v3.1_final_nr, HISTCR",
                "PRIMAP-hist_v3.1_final_nr, HISTTP",
                "Andrews, History",
                "EDGAR-HYDE 1.4, History",
                "EDGAR-HYDE 1.5, History",
            ),
            "PRIMAP-hist_v3.0_final_nr, HISTCR",
            "PRIMAP-hist_v3.0_final_nr, HISTTP",
            "PRIMAP-hist_v3.1_final_nr, HISTCR",
            "PRIMAP-hist_v3.1_final_nr, HISTTP",
            tuple(
                ("Andrews, History",),
                ("EDGAR-HYDE 1.4, History", "EDGAR-HYDE 1.5, History"),
                ("SSPs",),
            ),
            id="other_source_scenarios_inference_version_string_no_v",
        ),
        pytest.param(
            (
                "SSPs",
                "PRIMAP-hist_v3.0_final_nr, HISTTP",
                "RCMIP v2.4, SSP126",
                "RCMIP v2.5, SSP126",
                "PRIMAP-hist_v3.0_final_nr, HISTCR",
                "PRIMAP-hist_v3.1_final_nr, HISTCR",
                "EDGAR 2022, History",
                "EDGAR 2023, History",
                "PRIMAP-hist_v3.1_final_nr, HISTTP",
                "Andrews, History",
                "EDGAR-HYDE 1.4, History",
                "EDGAR-HYDE 1.5, History",
            ),
            "PRIMAP-hist_v3.0_final_nr, HISTCR",
            "PRIMAP-hist_v3.0_final_nr, HISTTP",
            "PRIMAP-hist_v3.1_final_nr, HISTCR",
            "PRIMAP-hist_v3.1_final_nr, HISTTP",
            tuple(
                ("Andrews, History",),
                ("EDGAR 2022, History", "EDGAR 2023, History"),
                ("EDGAR-HYDE 1.4, History", "EDGAR-HYDE 1.5, History"),
                ("RCMIP v2.4, SSP126", "RCMIP v2.5, SSP126"),
                ("SSPs",),
            ),
            id="other_source_scenarios_inference",
        ),
    ),
)
def test_infer_source_scenarios(  # noqa: PLR0913
    source_scenarios,
    exp_primap_old_cr,
    exp_primap_old_tp,
    exp_primap_new_cr,
    exp_primap_new_tp,
    exp_other_source_scenarios,
):
    inp_ds = create_testing_dataset(source_scenarios=source_scenarios)

    res = infer_source_scenarios(inp_ds)

    assert res.primap_old_cr == exp_primap_old_cr
    assert res.primap_old_tp == exp_primap_old_tp
    assert res.primap_new_cr == exp_primap_new_cr
    assert res.primap_new_tp == exp_primap_new_tp
    assert res.other_source_scenarios == exp_other_source_scenarios
