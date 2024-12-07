"""
Tests of our variable ID validation
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.variable_id import validate_variable_id

EXP_ERROR_MSG_SINGLE_VAR_MISMATCH = "".join(
    [
        re.escape("The `variable_id` attribute must match the variable name "),
        r"\('.*'\) exactly. Received variable_id='.*'\.",
    ]
)
EXP_ERROR_MSG_MULTIPLE_VAR_INVALID = "".join(
    [
        re.escape(
            "There is more than one variable in the dataset, "
            "hence the `variable_id` attribute must start with 'multiple'. "
        ),
        r"Received variable_id='.*'\.",
    ]
)
EXP_ERROR_MSG_INVALID_CHARS_SINGLE_VAR = "".join(
    [
        re.escape(
            "The `variable_id` attribute contains invalid characters. "
            "Only Alphanumeric characters and underscores are allowed. "
        ),
        r".*invalid_chars=.*",
    ]
)
EXP_ERROR_MSG_INVALID_CHARS_MULTIPLE_VAR = "".join(
    [
        re.escape(
            "The `variable_id` attribute contains invalid characters. "
            "Only Alphanumeric characters, underscores or hyphens are allowed. "
        ),
        r".*invalid_chars=.*",
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
            pytest.raises(ValueError, match=EXP_ERROR_MSG_SINGLE_VAR_MISMATCH),
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
            pytest.raises(ValueError, match=EXP_ERROR_MSG_INVALID_CHARS_SINGLE_VAR),
            id="hyphen_in_variable_name",
        ),
        pytest.param(
            "co2 mass",
            "co2 mass",
            pytest.raises(ValueError, match=EXP_ERROR_MSG_INVALID_CHARS_SINGLE_VAR),
            id="space_in_variable_name",
        ),
        pytest.param(
            ["rss", "sdt"],
            "multiple-volcanic",
            does_not_raise(),
            id="valid_multiple_hyphen",
        ),
        pytest.param(
            ["rss", "sdt"],
            "multiple_volcanic",
            does_not_raise(),
            id="valid_multiple_underscore",
        ),
        pytest.param(
            ["rss", "sdt"],
            "multiple volcanic",
            pytest.raises(ValueError, match=EXP_ERROR_MSG_INVALID_CHARS_MULTIPLE_VAR),
            id="invalid_multiple_whitespace",
        ),
        pytest.param(
            ["rss", "sdt"],
            "volcanic",
            pytest.raises(ValueError, match=EXP_ERROR_MSG_MULTIPLE_VAR_INVALID),
            id="invalid_multiple_underscore",
        ),
    ),
)
def test_valid_passes(variable_name, variable_id, expectation):
    with expectation:
        validate_variable_id(variable_id, ds_variables=variable_name)
