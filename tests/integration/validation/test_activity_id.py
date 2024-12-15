"""
Integration tests of the activity ID validation
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


def test_invalid_activity_id_raises(test_cvs):
    """
    Test that an invalid value raises

    For a full list of edge case tests,
    see `tests/unit/validation/test_activity_id_validation.py`.
    """
    invalid_value = "junk"

    assert (
        invalid_value not in test_cvs.activity_id_entries.activity_ids
    ), "The invalid value is in the test CVs so the test won't work"

    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs,
    )

    valid_disk_ready_ds.attrs["activity_id"] = invalid_value

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape(
        "ValueNotAllowedByCVsError: The value provided for activity_id was 'junk'. "
        "According to the CVs, activity_id must be one of"
    )
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()


def test_no_activity_id_raises(test_cvs):
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    valid_disk_ready_ds.attrs.pop("activity_id")

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape("MissingAttributeError: 'activity_id'")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()
