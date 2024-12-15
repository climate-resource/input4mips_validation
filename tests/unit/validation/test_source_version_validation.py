"""
Tests of our source version validation
"""

from __future__ import annotations

from contextlib import nullcontext as does_not_raise

import pytest

EXP_ERROR_MSG = "".join(
    [
        r"The value provided for source_version was '.*'\. ",
        r"According to the CVs, source_version depends on the value of source_id. ",
        r"As a result, source_version must be '.*'\. "
        "If helpful, the full CV entry for source_id is:",
    ]
)


@pytest.mark.parametrize(
    "source_version, source_id, expectation",
    (
        pytest.param(
            "0.2.0",
            "CR-CMIP-0-2-0",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "0-2-0",
            "CR-CMIP-0-2-0",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid_value",
        ),
    ),
)
def test_source_version_validation(source_version, source_id, expectation, test_cvs):
    with expectation:
        test_cvs.validate_source_version(source_version, source_id=source_id)
