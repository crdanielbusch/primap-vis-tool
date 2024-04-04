"""
PRIMAP visualisation tool, stateless version
"""
from __future__ import annotations

import xarray as xr

from primap_visualisation_tool_stateless_app.dataset_holder import (
    ApplicationDatasetHolder,
)

APPLICATION_DATASET_HOLDER = ApplicationDatasetHolder(None)
"""Holder of the application's dataset"""


def get_application_dataset() -> xr.Dataset:
    """
    Get the dataset to use with the application

    Returns
    -------
        Dataset to use with the application
    """
    return APPLICATION_DATASET_HOLDER.dataset


def set_application_dataset(dataset: xr.Dataset) -> None:
    """
    Set the dataset to use with the application

    Parameters
    ----------
    dataset
        Dataset to use with the application
    """
    APPLICATION_DATASET_HOLDER.dataset = dataset
