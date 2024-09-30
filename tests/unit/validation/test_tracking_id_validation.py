"""
Tests of our tracking ID validation
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.tracking_id import validate_tracking_id

EXP_ERROR_MSG = "".join(
    [
        re.escape(
            "The `tracking_id` attribute must start with the prefix 'hdl:21.14100/', "
            "followed by a version 4 universally unique identifier (UUID4). "
            "If it does this, it will match the following regular expression, "
            r"'hdl\\:21\\.14100\\/[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}'. ",  # noqa: E501
        ),
        r"Received tracking_id='.*'\. ",
        "To see how to generate a correct tracking ID, ",
        "see `input4mips_validation.io.generate_tracking_id`.",
    ]
)


@pytest.mark.parametrize(
    "tracking_id, expectation",
    (
        pytest.param(
            "hdl:21.14100/e3385e8c-08d9-4524-8377-49feb3eaa05e",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "e3385e8c-08d9-4524-8377-49feb3eaa05e",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="missing_prefix",
        ),
        pytest.param(
            "hdl:21.14100/e85e8c-08d9-4524-8377-49feb3eaa05e",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid_uuid4_missing_values",
        ),
        pytest.param(
            "hdl:21.14100/E3385E8C-08D9-4524-8377-49FEB3EAA05E",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid_uuid4_uppercase",
        ),
    ),
)
def test_valid_passes(tracking_id, expectation):
    with expectation:
        validate_tracking_id(tracking_id)
