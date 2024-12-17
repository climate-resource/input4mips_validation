"""
Support for defining rules around the characters allowed in metadata
"""

from __future__ import annotations

import string

from attrs import define


@define
class AllowedCharacters:
    """
    Definition of a set of allowed characters
    """

    values: set[str]
    """The allowed characters"""

    desc: str
    """A human-readable description of this set of allowed characters"""


ALPHANUMERIC_AND_UNDERSCORES = AllowedCharacters(
    values={
        *string.ascii_lowercase,
        *string.ascii_uppercase,
        *(str(v) for v in range(10)),
        "_",
    },
    desc="alphanumeric characters and underscores",
)

ALPHANUMERIC_AND_UNDERSCORES_AND_HYPYHENS = AllowedCharacters(
    values={
        *ALPHANUMERIC_AND_UNDERSCORES.values,
        "-",
    },
    desc="alphanumeric characters, underscores and hyphens",
)

ALPHANUMERIC_AND_UNDERSCORES_AND_WHITESPACE = AllowedCharacters(
    values={
        *ALPHANUMERIC_AND_UNDERSCORES.values,
        " ",
    },
    desc="alphanumeric characters, underscores and whitespaces",
)


def check_only_allowed_characters(
    value: str, allowed_characters: AllowedCharacters
) -> None:
    """
    Check that a value only contains allowed characters

    Parameters
    ----------
    value
        Value to check

    allowed_characters
        Allowed characters

    Raises
    ------
    ValueError
        inv contains characters which are not allowed.
    """
    invalid_chars = {c for c in set(value) if c not in allowed_characters.values}
    if invalid_chars:
        msg = f"Only {allowed_characters.desc} are allowed. {value=}. {invalid_chars=}."
        raise ValueError(msg)
