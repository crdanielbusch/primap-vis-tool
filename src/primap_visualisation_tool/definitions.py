"""
Definitions.
"""


SUBENTITIES: dict[str, list[str]] = {
    "CO2": ["CO2"],
    "CH4": ["CH4"],
    "N2O": ["N2O"],
    "SF6": ["SF6"],
    "NF3": ["NF3"],
    "HFCS (SARGWP100)": ["HFCS (SARGWP100)"],
    "PFCS (SARGWP100)": ["PFCS (SARGWP100)"],
    "FGASES (SARGWP100)": ["HFCS (SARGWP100)", "PFCS (SARGWP100)", "NF3", "SF6"],
    "KYOTOGHG (SARGWP100)": ["CO2", "CH4", "N2O", "FGASES (SARGWP100)"],
    "HFCS (AR4GWP100)": ["HFCS (AR4GWP100)"],
    "PFCS (AR4GWP100)": ["PFCS (AR4GWP100)"],
    "FGASES (AR4GWP100)": ["HFCS (AR4GWP100)", "PFCS (AR4GWP100)", "NF3", "SF6"],
    "KYOTOGHG (AR4GWP100)": ["CO2", "CH4", "N2O", "FGASES (AR4GWP100)"],
    "HFCS (AR5GWP100)": ["HFCS (AR5GWP100)"],
    "PFCS (AR5GWP100)": ["PFCS (AR5GWP100)"],
    "FGASES (AR5GWP100)": ["HFCS (AR5GWP100)", "PFCS (AR5GWP100)", "NF3", "SF6"],
    "KYOTOGHG (AR5GWP100)": ["CO2", "CH4", "N2O", "FGASES (AR5GWP100)"],
    "HFCS (AR6GWP100)": ["HFCS (AR6GWP100)"],
    "PFCS (AR6GWP100)": ["PFCS (AR6GWP100)"],
    "FGASES (AR6GWP100)": ["HFCS (AR6GWP100)", "PFCS (AR6GWP100)", "NF3", "SF6"],
    "KYOTOGHG (AR6GWP100)": ["CO2", "CH4", "N2O", "FGASES (AR6GWP100)"],
}
"""Mapping between entities and their components"""

index_cols: list[str] = [
    # "source",
    # "scenario (PRIMAP-hist)",
    "SourceScen",
    "provenance",
    "area (ISO3)",
    "entity",
    "unit",
    "category (IPCC2006_PRIMAP)",
]
"""Columns to use as the index when creating stacked plots"""
