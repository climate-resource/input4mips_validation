"""
Validation of values against the CVs

These are typically called on existing instances
(we can't validate the instances at creation time because that would require
us to use the same classes at creation time and as inputs for our validation,
which would create a circular dependency).
"""
from __future__ import annotations

from typing import Any

from attrs import asdict

from input4mips_validation.cvs_handling.exceptions import (
    InconsistentWithCVsError,
    NotInCVsError,
)
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import (
    load_source_id_entries,
    load_valid_cv_values,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import get_cvs_root
from input4mips_validation.cvs_handling.input4MIPs.source_id import SourceIDEntry


def assert_in_cvs(value: Any, cvs_key: str, cv_source: None | str = None) -> None:
    """
    Assert that a given value is in the CVs

    Parameters
    ----------
    value
        Value to check

    cvs_key
        CV's key, e.g. "source_id", "activity_id"

    cv_source
        String identifying the source of the CVs.

        For futher options, see the docstring of
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.get_cvs_root`.

    Raises
    ------
    NotInCVsError
        ``value`` is not in the CVs for ``cvs_key``
    """
    cvs_root = get_cvs_root(cv_source=cv_source)
    cv_values = load_valid_cv_values(cvs_key, cvs_root=cvs_root)

    if value not in cv_values:
        raise NotInCVsError(
            cvs_key=cvs_key,
            cvs_key_value=value,
            cv_values_for_key=cv_values,
            cv_path=cvs_root.location,
        )


def assert_source_id_entry_is_valid(
    entry: SourceIDEntry, cv_source: None | str = None
) -> None:
    """
    Assert that a {py:obj}`SourceIDEntry` is valid

    Parameters
    ----------
    entry
        {py:obj}`SourceIDEntry` to validate

    cv_source
        String identifying the source of the CVs.

        For futher options, see the docstring of
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.get_cvs_root`.
    """
    assert_in_cvs(value=entry.source_id, cvs_key="source_id", cv_source=cv_source)

    cvs_root = get_cvs_root(cv_source=cv_source)
    source_id_entry_from_cvs = load_source_id_entries(cvs_root=cvs_root)[
        entry.source_id
    ]

    for key in asdict(source_id_entry_from_cvs.values):
        value_user = getattr(entry.values, key)
        value_cvs = getattr(source_id_entry_from_cvs.values, key)
        if value_user != value_cvs:
            raise InconsistentWithCVsError(
                cvs_key_dependent=key,
                cvs_key_dependent_value_user=value_user,
                cvs_key_dependent_value_cvs=value_cvs,
                cvs_key_determinant="source_id",
                cvs_key_determinant_value=entry.source_id,
                cv_path=cvs_root.location,
            )
