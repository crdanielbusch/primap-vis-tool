"""
Holder for the application dataset
"""
from __future__ import annotations

import xarray as xr
from attrs import define


@define
class ApplicationDatasetHolder:
    """
    Holder of the application's dataset
    """

    dataset: xr.Dataset | None
    """Application's dataset"""
