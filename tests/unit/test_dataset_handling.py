import pytest

from primap_visualisation_tool_stateless_app.dataset_handling import sort_entity_options


@pytest.mark.parametrize(
    "unsorted, expected",
    (
        pytest.param(
            [
                "CH4",
                "CO2",
                "FGASES (AR6GWP100)",
                "HFCS (AR6GWP100)",
                "KYOTOGHG (AR6GWP100)",
                "N2O",
                "NF3",
                "PFCS (AR6GWP100)",
                "SF6",
            ],
            [
                "KYOTOGHG (AR6GWP100)",
                "CO2",
                "CH4",
                "N2O",
                "FGASES (AR6GWP100)",
                "HFCS (AR6GWP100)",
                "PFCS (AR6GWP100)",
                "SF6",
                "NF3",
            ],
            id="basic",
        ),
        pytest.param(
            ["CH4", "CO2", "N2O"],
            ["CO2", "CH4", "N2O"],
            id="only three entities",
        ),
        pytest.param(
            [
                "CH4",
                "CO2",
                "FGASES (AR5GWP100)",
                "FGASES (AR6GWP100)",
                "HFCS (AR5GWP100)",
                "HFCS (AR6GWP100)",
                "KYOTOGHG (AR5GWP100)",
                "KYOTOGHG (AR6GWP100)",
                "N2O",
                "NF3",
                "PFCS (AR5GWP100)",
                "PFCS (AR6GWP100)",
                "SF6",
            ],
            [
                "KYOTOGHG (AR5GWP100)",
                "KYOTOGHG (AR6GWP100)",
                "CO2",
                "CH4",
                "N2O",
                "FGASES (AR5GWP100)",
                "FGASES (AR6GWP100)",
                "HFCS (AR5GWP100)",
                "HFCS (AR6GWP100)",
                "PFCS (AR5GWP100)",
                "PFCS (AR6GWP100)",
                "SF6",
                "NF3",
            ],
            id="multiple GWPs",
        ),
    ),
)
def test_sort_entity_options(unsorted, expected):
    assert sort_entity_options(unsorted) == expected
