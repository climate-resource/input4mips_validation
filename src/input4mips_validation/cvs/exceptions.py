"""
Exceptions related to CVs
"""

from __future__ import annotations

from collections.abc import Collection
from typing import Any


class ValueNotAllowedByCVsError(ValueError):
    """
    Raised when a value is not in the values allowed by the CVs
    """

    def __init__(
        self,
        value: str,
        cv_component: str,
        cv_allowed_values: Collection[str],
        cv_entries: Collection[Any],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        value
            The invalid value

        cv_component
            The component of the CVs being considered

        cv_allowed_values
            The values that the attribute can have, according to the CVs

        cv_entries
            The full entries as they are in the CVs
        """
        entries_newline = "\n".join([str(entry) for entry in cv_entries])

        error_msg = (
            f"The value provided for {cv_component} was {value!r}. "
            "According to the CVs, "
            f"{cv_component} must be one of {cv_allowed_values!r}. "
            f"If helpful, the full CV entries are:\n{entries_newline}."
        )

        super().__init__(error_msg)


class ValueInconsistentWithCVsError(ValueError):
    """
    Raised when a value is inconsistent with the value expected by the CVs
    """

    def __init__(  # noqa: PLR0913
        self,
        value: str,
        expected_value: str,
        cv_component: str,
        cv_component_dependent_on: str,
        cv_entry_dependenty_component: Any,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        value
            The invalid value

        expected_value
            The value expected by the CVs

        cv_component
            The component of the CVs being considered

        cv_component_dependent_on
            The component of the CVs that the component being considered is dependent on

        cv_entry_dependenty_component
            The entry that defines the value, as it is in the CVs
        """
        error_msg = (
            f"The value provided for {cv_component} was {value!r}. "
            "According to the CVs, "
            f"{cv_component} depends on the value of {cv_component_dependent_on}. "
            f"As a result, {cv_component} must be {expected_value!r}. "
            f"If helpful, the full CV entry for {cv_component_dependent_on} is: "
            f"{cv_entry_dependenty_component}."
        )

        super().__init__(error_msg)
