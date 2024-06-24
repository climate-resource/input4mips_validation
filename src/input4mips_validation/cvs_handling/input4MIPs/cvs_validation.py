"""
Validation of CVs against our data model

This basically allows us to check that the raw CV JSON files
actually comply with the data model codified here.
"""
from __future__ import annotations

from collections.abc import Collection
from typing import Any

import validators

from input4mips_validation.cvs_handling.exceptions import (
    InternallyInconsistentCVsError,
    NotURLError,
)
from input4mips_validation.cvs_handling.input4MIPs.activity_id import ActivityIDEntry
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.source_id import SourceIDEntry


def assert_consistent_with_other_values_in_cvs(
    value: Any,
    source_key: str,
    cv_valid_values: Collection[Any],
    cv_valid_values_source_key: str,
) -> None:
    """
    Assert that a given value is consistent with the values elsewhere in the CVs

    Parameters
    ----------
    value
        Value to check

    source_key
        The source key from which ``value`` was retrieved e.g. "source_id.activity_id"

    cv_valid_values
        Valid CV values, which ``value`` must be in.

    cv_valid_values_source_key
        The source key from which ``cv_valid_values`` were retrieved.

    Raises
    ------
    NotInCVsError
        ``value`` is not in the CVs for ``cvs_key``
    """
    if value not in cv_valid_values:
        raise InternallyInconsistentCVsError(
            cvs_key=source_key,
            cvs_key_value=value,
            cvs_valid_values=cv_valid_values,
            cvs_valid_values_source_key=cv_valid_values_source_key,
        )


def assert_activity_id_entry_is_valid(entry: ActivityIDEntry) -> None:
    """
    Assert that a {py:obj}`ActivityIDEntry` is valid

    Parameters
    ----------
    entry
        {py:obj}`ActivityIDEntry` to validate

    Raises
    ------
    NotURLError
        ``entry.url`` is not a URL
    """
    # TODO: work out
    #
    # - whether this should also be consistent with
    #   some global source from the multiverse
    #
    # - whether there are any restrictions on long_name

    if not validators.url(entry.values.url):
        raise NotURLError(
            bad_value=entry.values.url,
            cv_location_description=(
                f"url for activity_id entry {entry.activity_id!r}"
            ),
        )


def assert_source_id_entry_is_valid(entry: SourceIDEntry, cvs: CVsInput4MIPs) -> None:
    """
    Assert that a {py:obj}`SourceIDEntry` is valid

    Parameters
    ----------
    entry
        {py:obj}`SourceIDEntry` to validate

    cvs
        Rest of CVs

        This is required because the source_id entry must be consistent
        with other parts of the CVs.

    Raises
    ------
    NotURLError
        ``entry.url`` is not a URL
    """
    # Activity ID
    assert_consistent_with_other_values_in_cvs(
        value=entry.values.activity_id,
        source_key=f"For source_id {entry.source_id!r}, activity_id",
        cv_valid_values=cvs.activity_id_entries.activity_ids,
        cv_valid_values_source_key="cvs.activity_id_entries.activity_ids",
    )

    # # Institution ID
    # assert_consistent_with_other_values_in_cvs(
    #     value=entry.values.institution_id,
    #     source_key=f"For source_id {entry.source_id!r}, institution_id",
    #     cv_valid_values=cvs.institution_id_entries.institution_ids,
    #     cv_valid_values_source_key="cvs.institution_id_entries.institution_ids",
    # )
    #
    # License
    # assert_license_entry_is_valid(entry.values.license, cvs=cvs)
    #
    # MIP ERA
    # assert_consistent_with_other_values_in_cvs(
    #     value=entry.values.mip_era,
    #     source_key=f"For source_id {entry.source_id!r}, mip_era",
    #     cv_valid_values=cvs.mip_eras,
    #     cv_valid_values_source_key="cvs.mip_eras",
    # )


def assert_cvs_are_valid(cvs: CVsInput4MIPs) -> None:
    """
    Assert that a {py:obj}`CVsInput4MIPs` is valid (internally consistent etc.)

    Parameters
    ----------
    cvs
        {py:obj}`CVsInput4MIPs` to check
    """
    # Activity ID
    for activity_id in cvs.activity_id_entries.entries:
        assert_activity_id_entry_is_valid(activity_id)

    # Dataset categories
    # Validate against some global source?

    # Data required global attributes
    # Validate against some global source?

    # DRS
    # must look like paths
    # placeholders etc. have to parse correctly and match data available in CV
    # (noting that some parts of the CV come from outside input4MIPs e.g. realm)

    # Institution ID
    # Validate against some global source?

    # License
    # Validate against some global source?
    # Make that the placeholders are available in CV
    # for license_spec in cvs.license_spec_entries:
    #     validate_license_spec_entry(license_spec)
    # licencse ID should be a string (validated against?)
    # license_url should be a URL

    # MIP era
    # Validate against some global source?

    # Product
    # Validate against some global source?

    # Source ID
    for source_id in cvs.source_id_entries.entries:
        assert_source_id_entry_is_valid(source_id, cvs=cvs)

    # Target MIP
    # Validate against some global source?
    # for target_mip_id in cvs.target_mip_id_entries:
    #     validate_target_mip_id_entry(target_mip_id)
    # URL in each entry should be a URL
    # long name can be any string

    # Tracking ID
    # regexp that looks sensible
    # (check we can generate tracking IDs that pass the regexp)
