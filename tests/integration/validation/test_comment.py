"""
Integration tests of the comment validation
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


def test_invalid_comment_raises(test_cvs):
    """
    Test that an invalid value raises

    For a full list of edge case tests,
    see `tests/unit/validation/test_comment_validation.py`.
    """
    invalid_value = ["list", "of", "strings"]

    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    valid_disk_ready_ds.attrs["comment"] = invalid_value

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape("TypeError: The `comment`")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()


def test_no_comment_is_fine(test_cvs):
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    try:
        valid_disk_ready_ds.attrs.pop("comment")
    except KeyError:
        # Already removed, can carry on
        pass

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    # Should be no error
    res.raise_if_errors()
