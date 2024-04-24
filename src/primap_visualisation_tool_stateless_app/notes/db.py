"""
Database handling
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

COUNTRY_NOTES_TABLE_NAME: str = "country_notes"
"""Name of the table which contains each country's notes"""


@contextmanager
def notes_db_connection(db_filepath: Path) -> sqlite3.Connection:
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
    cur.execute("CREATE TABLE country_notes(country TEXT PRIMARY KEY, notes TEXT)")


def save_country_note_in_notes_db(
    db_filepath: Path, country: str, note: str
) -> str | None:
    with get_notes_db_cursor(db_filepath=db_filepath) as db_cursor:
        sql_comand = """
            INSERT INTO country_notes(country, notes)
            VALUES(?, ?)
            ON CONFLICT(country)
            DO UPDATE SET notes=excluded.notes
        """
        db_cursor.execute(
            sql_comand,
            (country, note),
        )

    # If success, return the note, else return None
    # TODO: check for failure
    return get_country_note_from_notes_db(db_filepath, country=country)


def get_country_note_from_notes_db(db_filepath: Path, country: str) -> str | None:
    with get_notes_db_cursor(db_filepath=db_filepath) as db_cursor:
        country_notes = db_cursor.execute(
            "SELECT notes FROM country_notes WHERE country=?", (country,)
        ).fetchall()

    if len(country_notes) > 1:
        msg = f"Should only be one entry per country, have {len(country_notes)=}"
        raise AssertionError(msg)

    if not country_notes:
        return None

    existing_notes = country_notes[0]
    if len(existing_notes) != 1:
        msg = f"Number of notes isn't 1, received {len(existing_notes)=}"
        raise AssertionError(msg)

    if not existing_notes:
        return None

    return existing_notes[0]


def read_country_notes_db_as_pd(db_filepath: Path) -> pd.DataFrame:
    with notes_db_connection(db_filepath=db_filepath) as db_connection:
        db = pd.read_sql(
            sql=f"SELECT * FROM {COUNTRY_NOTES_TABLE_NAME}",
            con=db_connection,
        )

    return db
