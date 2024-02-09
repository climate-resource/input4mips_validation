"""
Validation of uuid's
"""
from __future__ import annotations

from input4mips_validation.controlled_vocabularies.constants import UUID_REGEX
from input4mips_validation.exceptions import DoesNotMatchRegexpError


def assert_uuid_is_valid(uuid: str) -> None:
    """
    Assert that a uuid is formatted correctly

    Parameters
    ----------
    uuid
        uuid to check

    Raises
    ------
    DoesNotMatchRegexpError
        The uuid is invalid
    """
    if not UUID_REGEX.fullmatch(uuid):
        raise DoesNotMatchRegexpError(
            high_level_msg=f"{uuid=} is invalid. ",
            regexp=UUID_REGEX,
        )
