"""
Custom exceptions
"""
import collections
from collections.abc import Collection
from pathlib import Path
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


class NotInCVsError(ValueError):
    """
    Raised when a value is not in the CVs
    """

    def __init__(
        self,
        cvs_key: str,
        cvs_key_value: Any,
        cv_values_for_key: Collection[Any],
        cv_path: str | Path,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        cvs_key
            Key from the CVs we're looking at

           E.g. "source_id", "activity_id", "mip_era"

        cvs_key_value
            Value that was used for ``key``

        cv_values_for_key
            The values that ``key`` can take according to the CVs

        cv_path
            The path from which the CVs were loaded
        """
        error_msg = (
            f"Received {cvs_key}={cvs_key_value!r}. "
            f"This is not in the available CV values: {cv_values_for_key!r}. "
            f"CVs path: {cv_path!r}"
        )

        super().__init__(error_msg)


class InconsistentWithCVsError(ValueError):
    """
    Raised when a value is inconsistent with the CVs
    """

    def __init__(  # noqa: PLR0913
        self,
        cvs_key_dependent: str,
        cvs_key_dependent_value_user: Any,
        cvs_key_dependent_value_cvs: Any,
        cvs_key_determinant: str,
        cvs_key_determinant_value: Any,
        cv_path: str | Path,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        cvs_key
            Key from the CVs we're looking at

           E.g. "source_id", "activity_id", "mip_era"

        cvs_key_value
            Value that was used for ``key``

        cv_values_for_key
            The values that ``key`` can take according to the CVs

        cv_path
            The path from which the CVs were loaded
        """
        error_msg = (
            f"For {cvs_key_determinant}={cvs_key_determinant_value!r}, "
            f"we should have {cvs_key_dependent}={cvs_key_dependent_value_cvs!r}. "
            f"Received {cvs_key_dependent}={cvs_key_dependent_value_user!r}. "
            f"CVs path: {cv_path!r}"
        )

        super().__init__(error_msg)
