"""
Tests of {py:mod}`primap_visualisation_tool_stateless_app.figures`
"""

from __future__ import annotations

from collections import OrderedDict

import pytest

from primap_visualisation_tool_stateless_app.dataset_handling import (
    SourceScenarioDefinition,
)
from primap_visualisation_tool_stateless_app.figures import (
    PlottingConfig,
    create_default_plotting_config,
)


@pytest.mark.parametrize(
    "inp, exp",
    (
        pytest.param(
            SourceScenarioDefinition(
                primap_versions=(
                    "PRIMAP-hist_v3.0",
                    "PRIMAP-hist_v2.5.1",
                ),
                other_source_scenarios=(
                    "SSPs",
                    "RCMIP v2.4, SSP126",
                    "RCMIP v2.5, SSP126",
                    "EDGAR 2022, History",
                    "RCP rcp26, HISTORY",
                    "EDGAR 2023, History",
                    "Andrews, History",
                    "EDGAR-HYDE 1.4, History",
                    "RCP hist, HISTORY",
                    "EDGAR-HYDE 1.5, History",
                ),
            ),
            PlottingConfig(
                source_scenario_settings=OrderedDict(
                    {
                        "PRIMAP-hist_v3.0, HISTCR": {
                            "color": "rgb(0, 0, 0)",
                            "dash": "solid",
                            "width": 3,
                        },
                        "PRIMAP-hist_v3.0, HISTTP": {
                            "color": "rgb(166, 166, 166)",
                            "dash": "solid",
                            "width": 3,
                        },
                        "PRIMAP-hist_v2.5.1, HISTCR": {
                            "color": "rgb(0, 0, 0)",
                            "dash": "dot",
                            "width": 3,
                        },
                        "PRIMAP-hist_v2.5.1, HISTTP": {
                            "color": "rgb(166, 166, 166)",
                            "dash": "dot",
                            "width": 3,
                        },
                        # Other source-scenarios are sorted.
                        # They are also grouped where possible,
                        # with source-scenarios with the same stem
                        # receiving the same colour but different dashes.
                        "Andrews, History": {
                            "color": "rgb(0, 0, 255)",
                            "dash": "solid",
                        },
                        "EDGAR 2023, History": {
                            "color": "rgb(50, 200, 255)",
                            "dash": "solid",
                        },
                        "EDGAR 2022, History": {
                            "color": "rgb(50, 200, 255)",
                            "dash": "dot",
                        },
                        "EDGAR-HYDE 1.5, History": {
                            "color": "rgb(0, 0, 255)",
                            "dash": "solid",
                        },
                        "EDGAR-HYDE 1.4, History": {
                            "color": "rgb(0, 0, 255)",
                            "dash": "dot",
                        },
                        "RCMIP v2.5, SSP126": {
                            "color": "rgb(60, 179, 113)",
                            "dash": "solid",
                        },
                        "RCMIP v2.4, SSP126": {
                            "color": "rgb(60, 179, 113)",
                            "dash": "dot",
                        },
                        "RCP rcp26, HISTORY": {
                            "color": "rgb(238, 130, 238)",
                            "dash": "solid",
                        },
                        "RCP hist, HISTORY": {
                            "color": "rgb(238, 130, 238)",
                            "dash": "dot",
                        },
                        "SSPs": {"color": "rgb(255, 165, 0)", "dash": "solid"},
                    }
                ),
            ),
            id="full",
        ),
    ),
)
def test_create_default_plotting_config(inp, exp):
    res = create_default_plotting_config(inp)

    assert res == exp
