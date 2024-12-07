"""
Tests of our variable ID validation
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.variable_id import validate_variable_id

EXP_ERROR_MSG = "".join(
    [
        re.escape("The `variable_id` attribute must match the variable name "),
        r"('.*') exactly. Received variable_id='.*'\. ",
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
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="mismatch",
        ),
        pytest.param(
            "mole_fraction_of_carbon_dioxide_in_air",
            "mole_fraction_of_carbon_dioxide_in_air",
            does_not_raise(),
            id="valid_value_with_hyphens",
        ),
        pytest.param(
            "mole_fraction_of_carbon_dioxide_in_air",
            "mole-fraction-of-carbon-dioxide-in-air",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="hyphens_rather_than_underscores",
        ),
        pytest.param(
            "mole-fraction-of-carbon-dioxide-in-air",
            "mole-fraction-of-carbon-dioxide-in-air",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="hyphen_in_variable_name",
        ),
    ),
)
def test_valid_passes(variable_name, variable_id, expectation):
    with expectation:
        validate_variable_id(variable_id, ds_variable=variable_name)
