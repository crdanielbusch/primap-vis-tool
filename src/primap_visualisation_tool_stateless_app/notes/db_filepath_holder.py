"""
Holder for the application's notes database filepath

If this doesn't work, copy the pattern from dataset_holder.py instead
"""
from __future__ import annotations

from pathlib import Path

from attrs import define


@define
class ApplicationNotesDBPathHolder:
    """
    Holder of the path to the application's notes database
    """

    filepath: Path | None
    """Path to the application's notes database"""


APPLICATION_NOTES_DB_PATH_HOLDER = ApplicationNotesDBPathHolder(None)
"""Holder of the path in which the application's notes database lives"""


def get_application_notes_db_filepath() -> Path:
    """
    Get the path to the application's notes database

    Returns
    -------
        Path to the application's notes database
    """
    return APPLICATION_NOTES_DB_PATH_HOLDER.filepath


def set_application_notes_db_filepath(filepath: Path) -> None:
    """
    Set the path to the application's notes database

    Parameters
    ----------
    filepath
        Path to the application's notes database
    """
    APPLICATION_NOTES_DB_PATH_HOLDER.filepath = filepath
