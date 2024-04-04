"""
Holder for the application dataset

This is sort of behaving like a database.
We might want to use an actual database in the future.
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
