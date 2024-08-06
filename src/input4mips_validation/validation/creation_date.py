"""
Validation of the `creation_date` attribute
"""

from __future__ import annotations

import datetime as dt

from input4mips_validation.validation.regexp import (
    DoesNotMatchRegexpError,
    validate_matches_regexp,
)


def validate_creation_date(creation_date: str) -> None:
    """
    Validate the creation date value

    The creation date must be provided as an ISO8601
    formatted string in the UTC timezone.
    In otherwords, it must take the form
    "YYYY-MM-DDThh:mm:ssZ"
    (where the trailing "Z" indicates that the timezone is UTC).

    For futher details, see:

    - https://stackoverflow.com/a/29282022
    - https://en.wikipedia.org/wiki/ISO_8601#Combined_date_and_time_representations

    Parameters
    ----------
    creation_date
        Creation date value to validate

    Raises
    ------
    ValueError
        `creation_date`'s value is not correctly formed
    """
    try:
        validate_matches_regexp(
            value=creation_date,
            regexp_to_match=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$",
        )

        dt.datetime.strptime(creation_date, "%Y-%m-%dT%H:%M:%SZ")

    except (DoesNotMatchRegexpError, ValueError) as exc:
        msg = (
            "The `creation_date` attribute must be of the from YYYY-MM-DDThh:mm:ssZ, "
            "i.e. be an ISO 8601 timestamp in the UTC timezone. "
            f"Received {creation_date=!r}"
        )
        raise ValueError(msg) from exc
