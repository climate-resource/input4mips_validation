"""
Deprecation support
"""

from __future__ import annotations

import warnings


def raise_deprecation_warning(name: str, removed_in: str, stacklevel: int = 3) -> None:
    """
    Raise a deprecation warning

    Parameters
    ----------
    name
        Name of the callable being deprecated

    removed_in
        Version in which the callable will be removed

    stacklevel
        Stack level to show with the warning
    """
    message = f"{name} will be removed in {removed_in}"
    warnings.warn(message, DeprecationWarning, stacklevel=stacklevel)
