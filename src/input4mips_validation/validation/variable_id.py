"""
Validation of the `variable_id` attribute
"""

from __future__ import annotations

import string

ALLOWED_CHARACTERS: set[str] = {
    *string.ascii_lowercase,
    *string.ascii_uppercase,
    *(str(v) for v in range(10)),
    "_",
}
"""
Characters that are allowed to appear in the variable ID
"""


def validate_variable_id(variable_id: str, ds_variable: str) -> None:
    """
    Validate the variable ID value

    Parameters
    ----------
    variable_id
        Variable ID value to validate

    Raises
    ------
    ValueError
        `variable_id`'s value is incorrect
    """
    invalid_chars = {c for c in set(variable_id) if c not in ALLOWED_CHARACTERS}
    if invalid_chars:
        msg = (
            f"The `variable_id` attribute "
            "must only contain alphanumeric characters and underscores. "
            f"Received {variable_id=!r}, "
            f"which contains the following invalid characters {invalid_chars}."
        )
        raise ValueError(msg)

    if variable_id != ds_variable:
        msg = (
            f"The `variable_id` attribute "
            f"must match the variable name ({ds_variable!r}) exactly. "
            f"Received {variable_id=!r}."
        )
        raise ValueError(msg)
