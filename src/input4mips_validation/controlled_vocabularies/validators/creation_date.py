"""
Validation of creation date
"""
from __future__ import annotations

from input4mips_validation.controlled_vocabularies.constants import CREATION_DATE_REGEX
from input4mips_validation.exceptions import DoesNotMatchRegexpError


def assert_creation_date_is_valid(creation_date: str) -> None:
    """
    Assert that a creation date is formatted correctly

    Parameters
    ----------
    creation_date
        Creation date to check

    Raises
    ------
    DoesNotMatchRegexpError
        The creation date is invalid
    """
    if not CREATION_DATE_REGEX.fullmatch(creation_date):
        raise DoesNotMatchRegexpError(
            high_level_msg=f"{creation_date=} is invalid. ",
            regexp=CREATION_DATE_REGEX,
        )
