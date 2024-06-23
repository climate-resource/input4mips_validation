"""
Email-related validation
"""
from __future__ import annotations

from input4mips_validation.controlled_vocabularies.constants import INCLUDES_EMAIL_REGEX
from input4mips_validation.exceptions import DoesNotMatchRegexpError


def assert_includes_email(metadata_value: str) -> None:
    """
    Assert that a metadata_value includes an email address

    Parameters
    ----------
    metadata_value
        Metadata value to check

    Raises
    ------
    DoesNotMatchRegexpError
        The metadata value does not contain an email address
    """
    if not INCLUDES_EMAIL_REGEX.fullmatch(metadata_value):
        raise DoesNotMatchRegexpError(
            high_level_msg=f"{metadata_value} does not contain an email. ",
            regexp=INCLUDES_EMAIL_REGEX,
        )
