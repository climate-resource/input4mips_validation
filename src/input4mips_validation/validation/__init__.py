"""
Core validation code (separate from all the other stuff you need to make this work)
"""
from __future__ import annotations

from pathlib import Path

import xarray as xr

from input4mips_validation.controlled_vocabularies.validators import (
    validate_ds_metadata,
    validate_ds_metadata_consistency,
)
from input4mips_validation.controlled_vocabularies.validators.creation_date import (
    assert_creation_date_is_valid,
)
from input4mips_validation.controlled_vocabularies.validators.uuid import (
    assert_uuid_is_valid,
)


def assert_file_is_valid(to_validate: Path) -> None:
    """
    Assert that a file is valid i.e. matches input4MIPs specifications

    Parameters
    ----------
    to_validate
        Path to the file to validate

    Raises
    ------
    AssertionError
        The file is invalid
        (reasons are given in the error and its __causes__)
    """
    ds = xr.load_dataset(to_validate)
    assert_dataset_is_valid(ds)


def assert_dataset_is_valid(ds: xr.Dataset) -> None:
    """
    Assert that a dataset is valid i.e. complies to all input4MIPs standards

    Parameters
    ----------
    ds
        Dataset to validate

    Raises
    ------
    AssertionError
        The dataset is invalid
        (reasons are given in the error and its __causes__)
    """
    # TODO: test this properly
    validate_ds_metadata(ds)
    validate_ds_metadata_consistency(ds)
    assert_creation_date_is_valid(ds.attrs["creation_date"])
    assert_uuid_is_valid(ds.attrs["tracking_id"])

    if not ds["time"].encoding:
        raise AssertionError(  # noqa: TRY003
            "Not specifying a time encoding will cause all sorts of headaches"
        )
