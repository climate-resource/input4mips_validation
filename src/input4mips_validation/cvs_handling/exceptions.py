"""
Custom exceptions
"""
from __future__ import annotations

import collections
from collections.abc import Collection
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import RawCVLoader


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


class NotURLError(ValueError):
    """
    Raised when a value should be a URL, but isn't
    """

    def __init__(
        self,
        description: str,
        bad_value: Any,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        description
            Description of the location at which the non-URL value occured.

           E.g. "url property of activity ID entry 'CMIP'",
           "further_info_url for source_id 'CR-CMIP-0-2-0'"

        cvs_key_value
            Value that was used for ``cvs_key``
        """
        error_msg = (
            f"{description} has a value of {bad_value!r}. "
            "This should be a URL "
            "(use `www.tbd.invalid` as a placeholder if you need)."
        )

        super().__init__(error_msg)


class CVsLike(Protocol):
    """Assumed shape of CVs when raising errors"""

    @property
    def raw_loader(self) -> RawCVLoader:
        """
        Object used to load the raw CVs
        """
        ...  # pragma: no cover


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
        cvs: CVsLike,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        cvs_key_dependent
            The key in the CVs we're validating.

        cvs_key_dependent_value_user
            Value that was provided by the user for ``cvs_key_dependent_value_user``

        cvs_key_dependent_value_cvs
            The value that ``cvs_key_dependent`` should have according to the CVs.

        cvs_key_determinant
            The key in the CVs which allows us
            to uniquely determine the expected value of ``cvs_key_dependent``

        cvs_key_determinant_value
            The value of ``cvs_key_determinant`` that we're considering

        cvs
            CVs from which the valid values were retrieved
        """
        error_msg = (
            f"For {cvs_key_determinant}={cvs_key_determinant_value!r}, "
            f"we should have {cvs_key_dependent}={cvs_key_dependent_value_cvs!r}. "
            f"Received {cvs_key_dependent}={cvs_key_dependent_value_user!r}. "
            f"CVs raw data loaded with: {cvs.raw_loader!r}. "
        )

        super().__init__(error_msg)


class InternallyInconsistentCVsError(ValueError):
    """
    Raised when the CVs are internally inconsistent

    For example, one part of the CVs has a value that is outside
    the range specified elsewhere in the CVs.
    """

    def __init__(
        self,
        cvs_key: str,
        cvs_key_value: Any,
        cvs_valid_values: Any,
        cvs_valid_values_source_key: str,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        cvs_key
            The key in the CVs we're validating.

        cvs_key_value
            Value in the CVs for ``cvs_key``

        cvs_valid_values
            The value that ``cvs_key`` should have according to the
            source of truth in the CVs.

        cvs_valid_values_source_key
            The key in the CVs which determines the allowed values of ``cvs_key``
        """
        error_msg = (
            f"{cvs_key}={cvs_key_value!r}. "
            "However, it must take a value from the collection specified by "
            f"{cvs_valid_values_source_key}, i.e. {cvs_valid_values!r}"
        )

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
        cvs: CVsLike,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        cvs_key
            Key from the CVs we're looking at

           E.g. "source_id", "activity_id", "mip_era"

        cvs_key_value
            Value that was used for ``cvs_key``

        cv_values_for_key
            The values that ``cvs_key`` can take according to the CVs

        cvs
            CVs from which the valid values were retrieved
        """
        error_msg = (
            f"Received {cvs_key}={cvs_key_value!r}. "
            f"This is not in the available CV values: {cv_values_for_key!r}. "
            f"CVs raw data loaded with: {cvs.raw_loader!r}. "
        )

        super().__init__(error_msg)
