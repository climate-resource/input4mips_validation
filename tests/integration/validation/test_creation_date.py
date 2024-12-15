"""
Integration tests of the creation date validation
"""

from __future__ import annotations

import re

import pytest

from input4mips_validation.testing import (
    get_valid_out_path_and_disk_ready_ds,
)
from input4mips_validation.validation.datasets_to_write_to_disk import (
    get_ds_to_write_to_disk_validation_result,
)
from input4mips_validation.validation.error_catching import ValidationResultsStoreError


def test_invalid_creation_date_raises(test_cvs):
    """
    Test that an invalid value raises

    For a full list of edge case tests,
    see `tests/unit/validation/test_creation_date_validation.py`.
    """
    invalid_value = "2024-08-01T08:03:04+00:00Z"

    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    valid_disk_ready_ds.attrs["creation_date"] = invalid_value

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape("ValueError: The `creation_date`")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()


def test_no_creation_date_raises(test_cvs):
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    valid_disk_ready_ds.attrs.pop("creation_date")

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape("MissingAttributeError: 'creation_date'")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()
