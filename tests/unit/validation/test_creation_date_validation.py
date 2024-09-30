"""
Tests of our creation date validation
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.creation_date import validate_creation_date

EXP_ERROR_MSG = "".join(
    [
        re.escape(
            "The `creation_date` attribute must be of the form YYYY-MM-DDThh:mm:ssZ, "
            "i.e. be an ISO 8601 timestamp in the UTC timezone. "
        ),
        "Received creation_date='.*'",
    ]
)


@pytest.mark.parametrize(
    "creation_date, expectation",
    (
        pytest.param(
            "2024-08-01T08:03:04Z",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "2024-08-01T08:03:04+00:00Z",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="incorrect-format",
        ),
        pytest.param(
            "2024-13-01T01:01:01Z",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid-month",
        ),
        pytest.param(
            "2024-01-51T01:01:01Z",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid-day",
        ),
        pytest.param(
            "2024-01-01T31:01:01Z",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid-hour",
        ),
        pytest.param(
            "2024-01-01T01:71:01Z",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid-minute",
        ),
        pytest.param(
            "2024-01-01T01:01:91Z",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid-second",
        ),
    ),
)
def test_valid_passes(creation_date, expectation):
    with expectation:
        validate_creation_date(creation_date)
