"""
Tools for validation more generally (neither dataset nor CV specific)
"""

from __future__ import annotations

import validators

from input4mips_validation.cvs_handling.exceptions import (
    NotURLError,
)


def assert_is_url_like(value: str, description: str) -> None:
    """
    Assert that a value is URL like

    Parameters
    ----------
    value
        The value which might be a URL

    description
        The description of where this is being validated.
        This is used to create more helpful error messages.

        E.g. "URL for activity_id entry 'CMIP'"

    Raises
    ------
    NotURLError
        ``value`` is obviously not a URL
    """
    if not validators.url(value):
        raise NotURLError(
            bad_value=value,
            description=description,
        )
