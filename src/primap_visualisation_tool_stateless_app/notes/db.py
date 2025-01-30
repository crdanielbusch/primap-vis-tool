"""
Database handling
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

COUNTRY_NOTES_TABLE_NAME: str = "country_notes"
"""Name of the table which contains each country's notes"""


@contextmanager
def notes_db_connection(db_filepath: Path) -> Iterator[sqlite3.Connection]:
    """
    Get a new connection to the notes database

    Parameters
    ----------
    db_filepath
        Filepath to the note's database

    Yields
    ------
        Database connection
    """
    con = sqlite3.connect(db_filepath)

    yield con

    con.commit()
    con.close()


@contextmanager
def notes_db_cursor(db_filepath: Path) -> Iterator[sqlite3.Cursor]:
    """
    Get a new cursor for the notes database

    Parameters
    ----------
    db_filepath
        Filepath to the note's database

    Yields
    ------
        Database cursor
    """
    new_db = not db_filepath.exists()

    with notes_db_connection(db_filepath) as db_connection:
        db_cursor = db_connection.cursor()
        if new_db:
            # No idea if this is the right place to do this...
            setup_db(db_cursor)

        yield db_cursor


def setup_db(cur: sqlite3.Cursor) -> None:
    """
    Set up our database's tables

    Parameters
    ----------
    cur
        Database cursor
    """
    cur.execute("CREATE TABLE country_notes(country_iso3 TEXT PRIMARY KEY, notes TEXT)")


def save_country_notes_in_notes_db(
    db_cursor: sqlite3.Cursor, country_iso3: str, notes_to_save: str
) -> str | None:
    """
    Save a country's notes in the notes database

    Parameters
    ----------
    db_cursor
        Cursor for the notes database

    country_iso3
        The ISO3 code of the country to which the notes apply

    notes_to_save
        Notes to save

    Returns
    -------
        Saved notes
    """
    sql_comand = """
        INSERT INTO country_notes(country_iso3, notes)
        VALUES(?, ?)
        ON CONFLICT(country_iso3)
        DO UPDATE SET notes=excluded.notes
    """
    db_cursor.execute(
        sql_comand,
        (country_iso3, notes_to_save),
    )

    return get_country_notes_from_notes_db(
        db_cursor=db_cursor, country_iso3=country_iso3
    )


def get_country_notes_from_notes_db(
    db_cursor: sqlite3.Cursor, country_iso3: str
) -> str | None:
    """
    Get a country's notes from the notes database

    Parameters
    ----------
    db_cursor
        Cursor for the notes database

    country_iso3
        The ISO3 code of the country for which to get the notes

    Returns
    -------
        Country's notes
    """
    country_notes: list[tuple[str]] = db_cursor.execute(
        "SELECT notes FROM country_notes WHERE country_iso3=?", (country_iso3,)
    ).fetchall()

    # Country notes is our primary key, so we have exactly two cases:
    # Case 1: no notes for this country
    if not country_notes:
        return None

    # Case 2: there is a country note,
    # in which case it is stored as a list with one element.
    # This element is a tuple which contains a single str.
    return country_notes[0][0]


def read_country_notes_db_as_pd(db_filepath: Path) -> pd.DataFrame:
    """
    Read the country notes database as a :obj:`pd.DataFrame`

    Parameters
    ----------
    db_filepath
        Notes database's filepath

    Returns
    -------
        The database's values as a :obj:`pd.DataFrame`
    """
    with notes_db_connection(db_filepath=db_filepath) as db_connection:
        db = pd.read_sql(
            sql="SELECT * FROM country_notes",
            con=db_connection,
        )

    return db
