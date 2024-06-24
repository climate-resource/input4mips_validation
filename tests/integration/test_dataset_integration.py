"""
Tests of dataset handling
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from attrs import asdict

from input4mips_validation.cvs_handling.exceptions import InconsistentWithCVsError
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import (
    load_cvs,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.dataset import Input4MIPsDataset, Input4MIPsDatasetMetadata

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (
        Path(__file__).parent / ".." / "test-data" / "cvs" / "input4MIPs" / "default"
    ).absolute()
)


# Test of just plain wrong values
@pytest.mark.parametrize(
    "cv_source, source_id, key_to_test, value_to_apply",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "activity_id",
            "CMIP",
        ),
    ),
)
def test_value_conflict_with_source_id_inferred_value(
    cv_source, source_id, key_to_test, value_to_apply
):
    """
    Test that an error is raised if we use a value
    that is inconsistent with the value we can infer from the source_id and the CV
    """
    with patch.dict(os.environ, {"INPUT4MIPS_VALIDATION_CV_SOURCE": cv_source}):
        cvs_exp = load_cvs(get_raw_cvs_loader())

        valid_source_id_entry = cvs_exp.source_id_entries.entries[0]

        value_according_to_cv = getattr(valid_source_id_entry.values, key_to_test)
        if value_according_to_cv == value_to_apply:
            msg = (
                "The test won't work if the CV's value "
                "and the applied value are the same"
            )
            raise AssertionError(msg)

        other_metadata_values = {
            k: v
            for k, v in asdict(valid_source_id_entry.values).items()
            if k in ["activity_id"]
        }
        other_metadata_values[key_to_test] = value_to_apply

        error_msg = re.escape(
            f"For source_id={source_id!r}, "
            f"we should have {key_to_test}={value_according_to_cv!r}. "
            f"Received {key_to_test}={value_to_apply!r}. "
            f"CVs raw data loaded with: {cvs_exp.raw_loader!r}. "
        )
        with pytest.raises(InconsistentWithCVsError, match=error_msg):
            Input4MIPsDataset(
                ds="to_be_replaced_with_valid_ds",
                metadata=Input4MIPsDatasetMetadata(
                    source_id=source_id, **other_metadata_values
                ),
            )
