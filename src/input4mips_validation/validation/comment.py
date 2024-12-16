"""
Validation of the `comment` attribute
"""

from __future__ import annotations


def validate_comment(comment: str) -> None:
    """
    Validate the comment value

    Parameters
    ----------
    comment
        Tracking ID value to validate

    Raises
    ------
    TypeError
        `comment`'s value is not a string
    """
    if not isinstance(comment, str):
        msg = f"The `comment` attribute must be a string, received {comment=!r}."
        raise TypeError(msg)
