"""
Validation of CVs against our data model

This basically allows us to check that the raw CV JSON files
actually comply with the data model codified here.
"""
from __future__ import annotations

import validators

from input4mips_validation.cvs_handling.exceptions import (
    NotURLError,
)
from input4mips_validation.cvs_handling.input4MIPs.activity_id import ActivityIDEntry
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs


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
    # TODO:
    #
    # - work out whether this should also be consistent with
    #   some global source from the multiverse
    #
    # - work out whether there are any restrictions on long_name

    if not validators.url(entry.values.url):
        raise NotURLError(
            bad_value=entry.values.url,
            cv_location_description=(
                f"url for activity_id entry {entry.activity_id!r}"
            ),
        )


def assert_cvs_are_valid(cvs: CVsInput4MIPs) -> None:
    """
    Assert that a {py:obj}`CVsInput4MIPs` is valid (internally consistent etc.)

    Parameters
    ----------
    cvs
        {py:obj}`CVsInput4MIPs` to check
    """
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
    # for source_id in cvs.source_id_entries:
    #     validate_source_id_entry(source_id)

    # Target MIP
    # Validate against some global source?
    # for target_mip_id in cvs.target_mip_id_entries:
    #     validate_target_mip_id_entry(target_mip_id)
    # URL in each entry should be a URL
    # long name can be any string

    # Tracking ID
    # regexp that looks sensible
    # (check we can generate tracking IDs that pass the regexp)
