"""
Integration tests of dataset validation
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from attrs import evolve

from input4mips_validation.cvs_handling.exceptions import (
    InconsistentWithCVsError,
    NotInCVsError,
)
from input4mips_validation.cvs_handling.input4MIPs import (
    SourceIDEntry,
)
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.dataset_validation import (
    assert_source_id_entry_is_valid,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (
        Path(__file__).parent
        / ".."
        / ".."
        / ".."
        / "test-data"
        / "cvs"
        / "input4MIPs"
        / "default"
    ).absolute()
)


@pytest.mark.parametrize(
    "cv_source, source_id",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-1-0",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "junk",
        ),
    ),
)
def test_source_id_not_in_cv_error(cv_source, source_id):
    """
    Test that an error is raised if we try and use a source_id that is not in the CV
    with values that are otherwise valid
    """
    bad_source_id = "junk"

    with patch.dict(os.environ, {"INPUT4MIPS_VALIDATION_CV_SOURCE": cv_source}):
        cvs_exp = load_cvs(get_raw_cvs_loader())

        valid_source_id_entry = cvs_exp.source_id_entries.entries[0]
        if bad_source_id == valid_source_id_entry.source_id:
            msg = (
                "The test won't work if the CV's value "
                "and the applied value are the same"
            )
            raise AssertionError(msg)

        error_msg = re.escape(
            f"Received source_id={bad_source_id!r}. "
            "This is not in the available CV values: "
            f"{cvs_exp.source_id_entries.source_ids!r}. "
            f"CVs raw data loaded with: {cvs_exp.raw_loader!r}. "
        )
        with pytest.raises(NotInCVsError, match=error_msg):
            assert_source_id_entry_is_valid(
                SourceIDEntry(
                    source_id=bad_source_id, values=valid_source_id_entry.values
                )
            )


@pytest.mark.parametrize(
    "cv_source, source_id, key_to_test, value_to_apply",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "activity_id",
            "CMIP",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "contact",
            "zeb@cr.com",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "further_info_url",
            "http://www.tbd.com/elsewhere",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "institution",
            "CR name here",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "institution_id",
            "Cr",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "license",
            "license text",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "mip_era",
            "CMIP7",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "version",
            "0.2.1",
        ),
    ),
)
def test_value_conflict_with_source_id_inferred_value(
    cv_source, source_id, key_to_test, value_to_apply
):
    """
    Test that an error is raised if we try and set a value
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

        values_incorrect = evolve(
            valid_source_id_entry.values, **{key_to_test: value_to_apply}
        )

        error_msg = re.escape(
            f"For source_id={source_id!r}, "
            f"we should have {key_to_test}={value_according_to_cv!r}. "
            f"Received {key_to_test}={value_to_apply!r}. "
            f"CVs raw data loaded with: {cvs_exp.raw_loader!r}. "
        )
        with pytest.raises(InconsistentWithCVsError, match=error_msg):
            assert_source_id_entry_is_valid(
                SourceIDEntry(source_id=source_id, values=values_incorrect)
            )
