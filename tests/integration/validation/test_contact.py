"""
Integration tests of the contact validation
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


def test_invalid_contact_raises(test_cvs):
    """
    Test that an invalid value raises

    For a full list of edge case tests,
    see `tests/unit/validation/test_contact_validation.py`.
    """
    source_id = "CR-CMIP-0-2-0"
    invalid_value = "tim@hotmail.com"

    assert (
        invalid_value != test_cvs.source_id_entries[source_id].values.contact
    ), "The invalid value is what the test CVs expect so the test won't work"

    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs,
    )

    valid_disk_ready_ds.attrs["contact"] = invalid_value

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape(
        "ValueInconsistentWithCVsError: "
        f"The value provided for contact was {invalid_value!r}. "
        "According to the CVs, contact depends on the value of source_id. "
        "As a result, contact must be "
        f"{test_cvs.source_id_entries[source_id].values.contact!r}."
    )
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()


def test_no_contact_raises(test_cvs):
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    valid_disk_ready_ds.attrs.pop("contact")

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    error_msg = re.escape("MissingAttributeError: 'contact'")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()
