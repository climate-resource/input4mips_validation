"""
Integration tests of the external variables validation
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


def test_invalid_external_variables_raises(test_cvs):
    """
    Test that an invalid value raises

    For a full list of edge case tests,
    see `tests/unit/validation/test_external_variables_validation.py`.
    """
    invalid_value = "junk,comma,separated"

    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs,
    )

    valid_disk_ready_ds.attrs["external_variables"] = invalid_value

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape("ValueError: The `external_variables`")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()


def test_no_external_variables_is_fine(test_cvs):
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    valid_disk_ready_ds.attrs.pop("external_variables")

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    # Should be no error
    res.raise_if_errors()
