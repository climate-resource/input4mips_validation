"""
Tests of our variable ID validation
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.variable_id import validate_variable_id

EXP_ERROR_MSG_MISMATCH = "".join(
    [
        re.escape("The `variable_id` attribute must match the variable name "),
        r"\('.*'\) exactly. Received variable_id='.*'\.",
    ]
)
EXP_ERROR_MSG_INVALID_CHARS = "".join(
    [
        re.escape(
            "The `variable_id` attribute must only contain "
            "alphanumeric characters and underscores. "
        ),
        r"Received variable_id='.*', ",
        r"which contains the following invalid characters \{.*\}.",
    ]
)


@pytest.mark.parametrize(
    "variable_name, variable_id, expectation",
    (
        pytest.param(
            "co2",
            "co2",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "co2",
            "ch4",
            pytest.raises(ValueError, match=EXP_ERROR_MSG_MISMATCH),
            id="mismatch",
        ),
        pytest.param(
            "mole_fraction_of_carbon_dioxide_in_air",
            "mole_fraction_of_carbon_dioxide_in_air",
            does_not_raise(),
            id="valid_value_with_hyphens",
        ),
        pytest.param(
            "mole-fraction-of-carbon-dioxide-in-air",
            "mole-fraction-of-carbon-dioxide-in-air",
            pytest.raises(ValueError, match=EXP_ERROR_MSG_INVALID_CHARS),
            id="hyphen_in_variable_name",
        ),
        pytest.param(
            "co2 mass",
            "co2 mass",
            pytest.raises(ValueError, match=EXP_ERROR_MSG_INVALID_CHARS),
            id="space_in_variable_name",
        ),
    ),
)
def test_valid_passes(variable_name, variable_id, expectation):
    with expectation:
        validate_variable_id(variable_id, ds_variable=variable_name)
