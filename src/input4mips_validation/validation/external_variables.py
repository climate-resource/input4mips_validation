"""
Validation of the `external_variables` attribute
"""

from __future__ import annotations

from input4mips_validation.validation.allowed_characters import (
    ALPHANUMERIC_AND_UNDERSCORES_AND_WHITESPACE,
    check_only_allowed_characters,
)


def validate_external_variables(external_variables: str) -> None:
    """
    Validate the external variables value

    Parameters
    ----------
    external_variables
        External variables value to validate.

    Raises
    ------
    ValueError
        `external_variables`'s value is incorrect
    """
    try:
        check_only_allowed_characters(
            external_variables,
            allowed_characters=ALPHANUMERIC_AND_UNDERSCORES_AND_WHITESPACE,
        )
    except ValueError as exc:
        msg = (
            "The `external_variables` attribute contains invalid characters. "
            "If you are providing multiple variables, "
            "they should be whitespace-separated. "
            f"{exc}"
        )
        raise ValueError(msg) from exc
