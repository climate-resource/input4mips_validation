"""
Validation of datasets and metadata against the CVs
"""
from __future__ import annotations

from collections.abc import Collection
from typing import Any

from attrs import asdict

from input4mips_validation.cvs_handling.exceptions import (
    InconsistentWithCVsError,
    NotInCVsError,
)
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import (
    load_cvs,
)
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.source_id import SourceIDEntry


def assert_in_cvs(
    value: Any, cvs_key: str, cv_values: Collection[Any], cvs: CVsInput4MIPs
) -> None:
    """
    Assert that a given value is in the CVs

    Parameters
    ----------
    value
        Value to check

    cvs_key
        CV's key, e.g. "source_id", "activity_id"

    cv_values
        Valid CV values, which ``value`` must be in.

    cvs
        CVs from which the valid values were retrieved

    Raises
    ------
    NotInCVsError
        ``value`` is not in the CVs for ``cvs_key``
    """
    if value not in cv_values:
        raise NotInCVsError(
            cvs_key=cvs_key,
            cvs_key_value=value,
            cv_values_for_key=cv_values,
            cvs=cvs,
        )


def assert_source_id_entry_is_valid(
    entry: SourceIDEntry, cvs: None | CVsInput4MIPs = None
) -> None:
    """
    Assert that a {py:obj}`SourceIDEntry` is valid

    Parameters
    ----------
    entry
        {py:obj}`SourceIDEntry` to validate

    cvs
        CVs to use for validation

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs`.
    """
    if cvs is None:
        cvs = load_cvs()

    assert_in_cvs(
        value=entry.values.activity_id,
        cvs_key="activity_id",
        cv_values=cvs.activity_id_entries.activity_ids,
        cvs=cvs,
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

    assert_in_cvs(
        value=entry.source_id,
        cvs_key="source_id",
        cv_values=cvs.source_id_entries.source_ids,
        cvs=cvs,
    )

    source_id_entry_from_cvs = cvs.source_id_entries[entry.source_id]

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
                cvs=cvs,
            )
