"""
Validation of values against regular expressions
"""

from __future__ import annotations

import re


class DoesNotMatchRegexpError(ValueError):
    """
    Raised when a value does not match a given regular expression, but it should
    """

    def __init__(
        self,
        value: str,
        regexp_to_match: str,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        value
            Value that should match `regexp_to_match`

        regexp_to_match
            Regular expression that `value` should match
        """
        error_msg = f"{value=!r} does not match {regexp_to_match=!r}"

        super().__init__(error_msg)


def validate_matches_regexp(value: str, regexp_to_match: str) -> None:
    """
    Validate that a value matches a given regular expression

    Parameters
    ----------
    value
        Value to validate

    regexp_to_match
        Regular expression that `value` should match

    Raises
    ------
    DoesNotMatchRegexpError
        `value` does not match `regexp_to_match`
    """
    if not re.match(regexp_to_match, value):
        raise DoesNotMatchRegexpError(value, regexp_to_match=regexp_to_match)
