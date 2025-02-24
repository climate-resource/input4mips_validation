"""
Validation of emails
"""

from __future__ import annotations

import email.utils as eutils


def validate_email(email: str) -> None:
    """
    Validate that a value might be a valid email

    This won't catch everything (so use with some caution),
    but it will catch things which are clearly wrong.

    Parameters
    ----------
    email
        Email to validate

    Raises
    ------
    ValueError
        `email` is clearly not an email
    """
    check_res = eutils.parseaddr(email)

    if "@" not in check_res[1]:
        msg = f"The given value is clearly not an email. Received {email=}"
        raise ValueError(msg)
