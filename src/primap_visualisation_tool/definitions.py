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

LINES_LAYOUT: dict[str, dict[str, str]] = {
    "Andrew cement, HISTORY": {"color": "rgb(0,0,255)", "dash": "solid"},
    "CDIAC 2020, HISTORY": {"color": "rgb(255, 0, 0)", "dash": "solid"},
    "CEDS 2020, HISTORY": {"color": "rgb(0, 0, 255)", "dash": "solid"},
    "CRF 2022, 230510": {"color": "rgb(60, 179, 113)", "dash": "solid"},
    "CRF 2023, 230926": {"color": "rgb(238, 130, 238)", "dash": "solid"},
    "EDGAR 7.0, HISTORY": {"color": "rgb(255, 165, 0)", "dash": "solid"},
    "EDGAR-HYDE 1.4, HISTORY": {"color": "rgb(106, 90, 205)", "dash": "solid"},
    "EI 2023, HISTORY": {"color": "rgb(50,0,255)", "dash": "solid"},
    "FAOSTAT 2022, HISTORY": {"color": "rgb(100,0,255)", "dash": "solid"},
    "Houghton, HISTORY": {"color": "rgb(150,0,255)", "dash": "solid"},
    "MATCH, HISTORY": {"color": "rgb(200,0,255)", "dash": "solid"},
    "PRIMAP-hist_v2.4.2_final_nr, HISTCR": {"color": "rgb(0, 0, 0)", "dash": "dot"},
    "PRIMAP-hist_v2.4.2_final_nr, HISTTP": {
        "color": "rgb(166, 166, 166)",
        "dash": "dot",
    },
    "PRIMAP-hist_v2.5_final_nr, HISTCR": {"color": "rgb(0, 0, 0)", "dash": "solid"},
    "PRIMAP-hist_v2.5_final_nr, HISTTP": {
        "color": "rgb(166, 166, 166)",
        "dash": "solid",
    },
    "RCP hist, HISTORY": {"color": "rgb(50,50,255)", "dash": "solid"},
    "UNFCCC NAI, 231015": {"color": "rgb(50,200,255)", "dash": "solid"},
}
