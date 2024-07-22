"""
Exceptions
"""

from __future__ import annotations

import collections
from collections.abc import Collection
from typing import Any


class NonUniqueError(ValueError):
    """
    Raised when a collection of values are not unique, but they should be
    """

    def __init__(
        self,
        description: str,
        values: Collection[Any],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        description
            Description of the collection and the error

            This is used to make a more helpful error message.

        values
            Collection of values that contains non-unique values
        """
        occurence_counts = collections.Counter(values).most_common()
        error_msg = f"{description}. {occurence_counts=}"

        super().__init__(error_msg)
