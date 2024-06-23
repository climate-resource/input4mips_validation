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
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    RawCVLoader,
    get_raw_cvs_loader,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import SourceIDEntry


def assert_in_cvs(
    value: Any, cvs_key: str, raw_cvs_loader: None | RawCVLoader = None
) -> None:
    """
    Assert that a given value is in the CVs

    Parameters
    ----------
    value
        Value to check

    cvs_key
        CV's key, e.g. "source_id", "activity_id"

    raw_cvs_loader
        Loader of raw CVs data.

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.get_raw_cvs_loader`.

    Raises
    ------
    NotInCVsError
        ``value`` is not in the CVs for ``cvs_key``
    """
    if raw_cvs_loader is None:
        raw_cvs_loader = get_raw_cvs_loader()

    cv_values = load_valid_cv_values(cvs_key, raw_cvs_loader=raw_cvs_loader)

    if value not in cv_values:
        raise NotInCVsError(
            cvs_key=cvs_key,
            cvs_key_value=value,
            cv_values_for_key=cv_values,
            raw_cvs_loader=raw_cvs_loader,
        )


def assert_source_id_entry_is_valid(
    entry: SourceIDEntry, raw_cvs_loader: None | RawCVLoader = None
) -> None:
    """
    Assert that a {py:obj}`SourceIDEntry` is valid

    Parameters
    ----------
    entry
        {py:obj}`SourceIDEntry` to validate

    raw_cvs_loader
        Loader of raw CVs data.

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.get_raw_cvs_loader`.
    """
    if raw_cvs_loader is None:
        raw_cvs_loader = get_raw_cvs_loader()

    assert_in_cvs(
        value=entry.source_id, cvs_key="source_id", raw_cvs_loader=raw_cvs_loader
    )
    #
    # key = "activity_id"
    # assert_in_cvs(
    #     value=getattr(entry.values, key), cvs_key=key, raw_cvs_loader=raw_cvs_loader
    # )
    #
    # assert_is_email_like(entry.values.contact)
    #
    # assert_is_url_like(entry.values.further_info_url)
    #
    # # institution can be any string, no validation right now
    #
    # key = "institution_id"
    # assert_in_cvs(
    #     value=getattr(entry.values, key), cvs_key=key, raw_cvs_loader=raw_cvs_loader
    # )
    #
    # assert_license_entry_is_valid(entry.values.license, other_values=entry.values)
    #
    # key = "mip_era"
    # assert_in_cvs(
    #     value=getattr(entry.values, key), cvs_key=key, raw_cvs_loader=raw_cvs_loader
    # )
    #
    # # version can be any string, no validation right now

    source_id_entry_from_cvs = load_source_id_entries(raw_cvs_loader=raw_cvs_loader)[
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
                raw_cvs_loader=raw_cvs_loader,
            )
