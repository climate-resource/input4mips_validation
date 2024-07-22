"""
Definition of everything database-related
"""

from __future__ import annotations

from input4mips_validation.database.database import (
    Input4MIPsDatabaseEntryFile,
    # TODO: remove this function entirely
    make_class_from_database_entry_file_fields,
)

__all__ = ["Input4MIPsDatabaseEntryFile", "make_class_from_database_entry_file_fields"]
