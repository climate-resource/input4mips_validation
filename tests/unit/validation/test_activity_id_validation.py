"""
Tests of our activity ID validation
"""

from __future__ import annotations

from contextlib import nullcontext as does_not_raise

import pytest

EXP_ERROR_MSG = "".join(
    [
        r"The value provided for activity_id was '.*'\. ",
        r"According to the CVs, activity_id must be one of \(.*\). ",
        r"If helpful, the full CV entries are:",
    ]
)


@pytest.mark.parametrize(
    "activity_id, expectation",
    (
        pytest.param(
            "input4MIPs",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "junk",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid_value",
        ),
    ),
)
def test_activity_id_validation(activity_id, expectation, test_cvs):
    with expectation:
        test_cvs.validate_activity_id(activity_id)
