"""
Notes handling
"""

from primap_visualisation_tool_stateless_app.notes.db import (
    COUNTRY_NOTES_TABLE_NAME,
    get_country_notes_from_notes_db,
    notes_db_connection,
    notes_db_cursor,
    read_country_notes_db_as_pd,
    save_country_notes_in_notes_db,
)
from primap_visualisation_tool_stateless_app.notes.notifications import (
    get_note_save_confirmation_string,
)

__all__ = [
    "COUNTRY_NOTES_TABLE_NAME",
    "get_country_notes_from_notes_db",
    "get_note_save_confirmation_string",
    "notes_db_connection",
    "notes_db_cursor",
    "read_country_notes_db_as_pd",
    "save_country_notes_in_notes_db",
]
