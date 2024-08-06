"""
Tests of our creation date validation
"""

from __future__ import annotations

import re

import pytest

from input4mips_validation.validation.creation_date import validate_creation_date


@pytest.mark.parametrize("valid_value", ("2024-08-01T08:03:04Z",))
def test_valid_passes(valid_value):
    # No error should be raised
    validate_creation_date(valid_value)


@pytest.mark.parametrize(
    "invalid_value",
    (
        pytest.param("2024-08-01T08:03:04+00:00Z", id="incorrect-format"),
        pytest.param("2024-13-01T01:01:01Z", id="invalid-month"),
        pytest.param("2024-01-51T01:01:01Z", id="invalid-day"),
        pytest.param("2024-01-01T31:01:01Z", id="invalid-hour"),
        pytest.param("2024-01-01T01:71:01Z", id="invalid-minute"),
        pytest.param("2024-01-01T01:01:91Z", id="invalid-second"),
    ),
)
def test_invalid_error(invalid_value):
    error_msg = re.escape(
        "The `creation_date` attribute must be of the from YYYY-MM-DDThh:mm:ssZ, "
        "i.e. be an ISO 8601 timestamp in the UTC timezone. "
        f"Received creation_date={invalid_value!r}"
    )
    with pytest.raises(ValueError, match=error_msg):
        validate_creation_date(invalid_value)
