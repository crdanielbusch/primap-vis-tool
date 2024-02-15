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

delete_later = {
    "data": [
        {
            "line": {"color": "rgb(60, 179, 113)", "dash": "solid"},
            "mode": "lines",
            "name": "CRF 2022, 230510",
            "visible": True,
            "x": [
                "2018-01-01T00:00:00",
                "2019-01-01T00:00:00",
                "2020-01-01T00:00:00",
                "2021-01-01T00:00:00",
                "2022-01-01T00:00:00",
            ],
            "y": [17300000, 16900000, 15700000, None, None],
            "type": "scatter",
        },
        {
            "line": {"color": "rgb(238, 130, 238)", "dash": "solid"},
            "mode": "lines",
            "name": "CRF 2023, 230926",
            "visible": True,
            "x": [
                "2018-01-01T00:00:00",
                "2019-01-01T00:00:00",
                "2020-01-01T00:00:00",
                "2021-01-01T00:00:00",
                "2022-01-01T00:00:00",
            ],
            "y": [17300000, 16900000, 15700000, 16400000, None],
            "type": "scatter",
        },
        {
            "line": {"color": "rgb(255, 165, 0)", "dash": "solid"},
            "mode": "lines",
            "name": "EDGAR 7.0, HISTORY",
            "visible": True,
            "x": [
                "2018-01-01T00:00:00",
                "2019-01-01T00:00:00",
                "2020-01-01T00:00:00",
                "2021-01-01T00:00:00",
                "2022-01-01T00:00:00",
            ],
            "y": [50900000, 51200000, 49700000, 51700000, None],
            "type": "scatter",
        },
        {
            "line": {"color": "rgb(0, 0, 0)", "dash": "solid"},
            "mode": "lines",
            "name": "PRIMAP-hist_v2.5_final_nr, HISTCR",
            "visible": True,
            "x": [
                "2018-01-01T00:00:00",
                "2019-01-01T00:00:00",
                "2020-01-01T00:00:00",
                "2021-01-01T00:00:00",
                "2022-01-01T00:00:00",
            ],
            "y": [48969956, 49204731, 47852986, 49803629, 50145579],
            "type": "scatter",
        },
        {
            "line": {"color": "rgb(166, 166, 166)", "dash": "solid"},
            "mode": "lines",
            "name": "PRIMAP-hist_v2.5_final_nr, HISTTP",
            "visible": True,
            "x": [
                "2018-01-01T00:00:00",
                "2019-01-01T00:00:00",
                "2020-01-01T00:00:00",
                "2021-01-01T00:00:00",
                "2022-01-01T00:00:00",
            ],
            "y": [50916691, 51229179, 49723345, 51805253, 52190900],
            "type": "scatter",
        },
        {
            "line": {"color": "rgb(50,200,255)", "dash": "solid"},
            "mode": "lines",
            "name": "UNFCCC NAI, 231015",
            "visible": True,
            "x": [
                "2018-01-01T00:00:00",
                "2019-01-01T00:00:00",
                "2020-01-01T00:00:00",
                "2021-01-01T00:00:00",
                "2022-01-01T00:00:00",
            ],
            "y": [2520000, 3410000, 1160000, None, None],
            "type": "scatter",
        },
    ],
    "layout": {
        "template": {
            "data": {
                "histogram2dcontour": [
                    {
                        "type": "histogram2dcontour",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1, "#f0f921"],
                        ],
                    }
                ],
                "choropleth": [
                    {"type": "choropleth", "colorbar": {"outlinewidth": 0, "ticks": ""}}
                ],
                "histogram2d": [
                    {
                        "type": "histogram2d",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1, "#f0f921"],
                        ],
                    }
                ],
                "heatmap": [
                    {
                        "type": "heatmap",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1, "#f0f921"],
                        ],
                    }
                ],
                "heatmapgl": [
                    {
                        "type": "heatmapgl",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1, "#f0f921"],
                        ],
                    }
                ],
                "contourcarpet": [
                    {
                        "type": "contourcarpet",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                    }
                ],
                "contour": [
                    {
                        "type": "contour",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1, "#f0f921"],
                        ],
                    }
                ],
                "surface": [
                    {
                        "type": "surface",
                        "colorbar": {"outlinewidth": 0, "ticks": ""},
                        "colorscale": [
                            [0, "#0d0887"],
                            [0.1111111111111111, "#46039f"],
                            [0.2222222222222222, "#7201a8"],
                            [0.3333333333333333, "#9c179e"],
                            [0.4444444444444444, "#bd3786"],
                            [0.5555555555555556, "#d8576b"],
                            [0.6666666666666666, "#ed7953"],
                            [0.7777777777777778, "#fb9f3a"],
                            [0.8888888888888888, "#fdca26"],
                            [1, "#f0f921"],
                        ],
                    }
                ],
                "mesh3d": [
                    {"type": "mesh3d", "colorbar": {"outlinewidth": 0, "ticks": ""}}
                ],
                "scatter": [
                    {
                        "fillpattern": {
                            "fillmode": "overlay",
                            "size": 10,
                            "solidity": 0.2,
                        },
                        "type": "scatter",
                    }
                ],
                "parcoords": [
                    {
                        "type": "parcoords",
                        "line": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "scatterpolargl": [
                    {
                        "type": "scatterpolargl",
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "bar": [
                    {
                        "error_x": {"color": "#2a3f5f"},
                        "error_y": {"color": "#2a3f5f"},
                        "marker": {
                            "line": {"color": "#E5ECF6", "width": 0.5},
                            "pattern": {
                                "fillmode": "overlay",
                                "size": 10,
                                "solidity": 0.2,
                            },
                        },
                        "type": "bar",
                    }
                ],
                "scattergeo": [
                    {
                        "type": "scattergeo",
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "scatterpolar": [
                    {
                        "type": "scatterpolar",
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "histogram": [
                    {
                        "marker": {
                            "pattern": {
                                "fillmode": "overlay",
                                "size": 10,
                                "solidity": 0.2,
                            }
                        },
                        "type": "histogram",
                    }
                ],
                "scattergl": [
                    {
                        "type": "scattergl",
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "scatter3d": [
                    {
                        "type": "scatter3d",
                        "line": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "scattermapbox": [
                    {
                        "type": "scattermapbox",
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "scatterternary": [
                    {
                        "type": "scatterternary",
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "scattercarpet": [
                    {
                        "type": "scattercarpet",
                        "marker": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                    }
                ],
                "carpet": [
                    {
                        "aaxis": {
                            "endlinecolor": "#2a3f5f",
                            "gridcolor": "white",
                            "linecolor": "white",
                            "minorgridcolor": "white",
                            "startlinecolor": "#2a3f5f",
                        },
                        "baxis": {
                            "endlinecolor": "#2a3f5f",
                            "gridcolor": "white",
                            "linecolor": "white",
                            "minorgridcolor": "white",
                            "startlinecolor": "#2a3f5f",
                        },
                        "type": "carpet",
                    }
                ],
                "table": [
                    {
                        "cells": {
                            "fill": {"color": "#EBF0F8"},
                            "line": {"color": "white"},
                        },
                        "header": {
                            "fill": {"color": "#C8D4E3"},
                            "line": {"color": "white"},
                        },
                        "type": "table",
                    }
                ],
                "barpolar": [
                    {
                        "marker": {
                            "line": {"color": "#E5ECF6", "width": 0.5},
                            "pattern": {
                                "fillmode": "overlay",
                                "size": 10,
                                "solidity": 0.2,
                            },
                        },
                        "type": "barpolar",
                    }
                ],
                "pie": [{"automargin": True, "type": "pie"}],
            },
            "layout": {
                "autotypenumbers": "strict",
                "colorway": [
                    "#636efa",
                    "#EF553B",
                    "#00cc96",
                    "#ab63fa",
                    "#FFA15A",
                    "#19d3f3",
                    "#FF6692",
                    "#B6E880",
                    "#FF97FF",
                    "#FECB52",
                ],
                "font": {"color": "#2a3f5f"},
                "hovermode": "closest",
                "hoverlabel": {"align": "left"},
                "paper_bgcolor": "white",
                "plot_bgcolor": "#E5ECF6",
                "polar": {
                    "bgcolor": "#E5ECF6",
                    "angularaxis": {
                        "gridcolor": "white",
                        "linecolor": "white",
                        "ticks": "",
                    },
                    "radialaxis": {
                        "gridcolor": "white",
                        "linecolor": "white",
                        "ticks": "",
                    },
                },
                "ternary": {
                    "bgcolor": "#E5ECF6",
                    "aaxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                    "baxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                    "caxis": {"gridcolor": "white", "linecolor": "white", "ticks": ""},
                },
                "coloraxis": {"colorbar": {"outlinewidth": 0, "ticks": ""}},
                "colorscale": {
                    "sequential": [
                        [0, "#0d0887"],
                        [0.1111111111111111, "#46039f"],
                        [0.2222222222222222, "#7201a8"],
                        [0.3333333333333333, "#9c179e"],
                        [0.4444444444444444, "#bd3786"],
                        [0.5555555555555556, "#d8576b"],
                        [0.6666666666666666, "#ed7953"],
                        [0.7777777777777778, "#fb9f3a"],
                        [0.8888888888888888, "#fdca26"],
                        [1, "#f0f921"],
                    ],
                    "sequentialminus": [
                        [0, "#0d0887"],
                        [0.1111111111111111, "#46039f"],
                        [0.2222222222222222, "#7201a8"],
                        [0.3333333333333333, "#9c179e"],
                        [0.4444444444444444, "#bd3786"],
                        [0.5555555555555556, "#d8576b"],
                        [0.6666666666666666, "#ed7953"],
                        [0.7777777777777778, "#fb9f3a"],
                        [0.8888888888888888, "#fdca26"],
                        [1, "#f0f921"],
                    ],
                    "diverging": [
                        [0, "#8e0152"],
                        [0.1, "#c51b7d"],
                        [0.2, "#de77ae"],
                        [0.3, "#f1b6da"],
                        [0.4, "#fde0ef"],
                        [0.5, "#f7f7f7"],
                        [0.6, "#e6f5d0"],
                        [0.7, "#b8e186"],
                        [0.8, "#7fbc41"],
                        [0.9, "#4d9221"],
                        [1, "#276419"],
                    ],
                },
                "xaxis": {
                    "gridcolor": "white",
                    "linecolor": "white",
                    "ticks": "",
                    "title": {"standoff": 15},
                    "zerolinecolor": "white",
                    "automargin": True,
                    "zerolinewidth": 2,
                },
                "yaxis": {
                    "gridcolor": "white",
                    "linecolor": "white",
                    "ticks": "",
                    "title": {"standoff": 15},
                    "zerolinecolor": "white",
                    "automargin": True,
                    "zerolinewidth": 2,
                },
                "scene": {
                    "xaxis": {
                        "backgroundcolor": "#E5ECF6",
                        "gridcolor": "white",
                        "linecolor": "white",
                        "showbackground": True,
                        "ticks": "",
                        "zerolinecolor": "white",
                        "gridwidth": 2,
                    },
                    "yaxis": {
                        "backgroundcolor": "#E5ECF6",
                        "gridcolor": "white",
                        "linecolor": "white",
                        "showbackground": True,
                        "ticks": "",
                        "zerolinecolor": "white",
                        "gridwidth": 2,
                    },
                    "zaxis": {
                        "backgroundcolor": "#E5ECF6",
                        "gridcolor": "white",
                        "linecolor": "white",
                        "showbackground": True,
                        "ticks": "",
                        "zerolinecolor": "white",
                        "gridwidth": 2,
                    },
                },
                "shapedefaults": {"line": {"color": "#2a3f5f"}},
                "annotationdefaults": {
                    "arrowcolor": "#2a3f5f",
                    "arrowhead": 0,
                    "arrowwidth": 1,
                },
                "geo": {
                    "bgcolor": "white",
                    "landcolor": "#E5ECF6",
                    "subunitcolor": "white",
                    "showland": True,
                    "showlakes": True,
                    "lakecolor": "white",
                },
                "title": {"x": 0.05},
                "mapbox": {"style": "light"},
            },
        },
        "xaxis": {
            "rangeslider": {
                "visible": True,
                "thickness": 0.05,
                "yaxis": {"_template": None, "rangemode": "match"},
                "autorange": True,
                "range": ["2018-01-01", "2022-01-01"],
            },
            "type": "date",
            "range": ["2018-03-03 15:58:26.4935", "2022-01-01"],
            "autorange": False,
        },
        "legend": {
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "left",
            "x": 0,
        },
        "margin": {"l": 0, "r": 0, "t": 0, "b": 0},
        "yaxis": {"type": "linear", "range": [-1675050, 55025950], "autorange": True},
    },
}
