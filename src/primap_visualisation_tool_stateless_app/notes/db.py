"""
Database handling
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def get_notes_db_cursor(db_filepath: Path) -> sqlite3.Cursor:
    """
    Get a new cursor for the notes database

    Parameters
    ----------
    db_filepath
        Filepath to the note's database

    Returns
    -------
        Database cursor
    """
    new_db = not db_filepath.exists()
    con = sqlite3.connect(db_filepath)
    cur = con.cursor()
    if new_db:
        # No idea if this is the right place to do this...
        setup_db(cur)

    yield cur

    con.commit()
    con.close()


def setup_db(cur: sqlite3.Cursor) -> None:
    """
    Set up our database's tables

    Parameters
    ----------
    cur
        Database cursor
    """
    cur.execute("CREATE TABLE country_notes(country, notes)")
