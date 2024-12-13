"""
Validation of the `Conventions` attribute
"""

from __future__ import annotations

from input4mips_validation.validation.regexp import (
    DoesNotMatchRegexpError,
    validate_matches_regexp,
)

REGEXP_TO_MATCH: str = r"CF-[0-9]+\.[0-9]+"
"""
Regular expression that the Conventions attribute must match

This constant is exposed for clarity.
If you change it, we do not guarantee correct performance of the codebase.
"""


def validate_Conventions(Conventions: str) -> None:
    """
    Validate the Conventions value

    Parameters
    ----------
    Conventions
        Conventions value to validate.

    Raises
    ------
    ValueError
        `Conventions`'s value is incorrect
    """
    try:
        validate_matches_regexp(
            value=Conventions,
            regexp_to_match=REGEXP_TO_MATCH,
        )

    except DoesNotMatchRegexpError as exc:
        msg = (
            f"The `Conventions` attribute must be of the form 'CF-X.Y', "
            f"i.e. match the regular expression {REGEXP_TO_MATCH!r}. "
            f"Received {Conventions=!r}."
        )
        raise ValueError(msg) from exc
