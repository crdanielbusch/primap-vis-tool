"""
Notifications related to notes handling
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path


def get_note_save_confirmation_string(db_filepath: Path, country: str) -> str:
    """
    Get a string which has information about a save operation to the database

    Parameters
    ----------
    db_filepath
        The database's filepath

    country
        Country for which the note has been saved

    Returns
    -------
        String which provides information about the save operation.
    """
    now = datetime.now()
    now_str = now.strftime("%Y-%m-%d-%H-%M-%S")

    return f"Notes for {country} saved at {now_str} in {db_filepath}"
