"""
Tests of our external variables validation
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.external_variables import (
    validate_external_variables,
)

EXP_ERROR_MSG = "".join(
    [
        re.escape(
            "The `external_variables` attribute contains invalid characters. "
            "If you are providing multiple variables, "
            "they should be whitespace-separated. "
            "Only alphanumeric characters, underscores and whitespaces are allowed. "
        ),
        r".*invalid_chars=.*",
    ]
)


@pytest.mark.parametrize(
    "external_variables, expectation",
    (
        pytest.param(
            "co2",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "co2_mole",
            does_not_raise(),
            id="valid_value_underscore",
        ),
        pytest.param(
            "co2 ch4",
            does_not_raise(),
            id="valid_value_whitespace_separated",
        ),
        pytest.param(
            "co2 ch4_mole",
            does_not_raise(),
            id="valid_value_whitespace_separated_underscore_1",
        ),
        pytest.param(
            "co2_mole ch4",
            does_not_raise(),
            id="valid_value_whitespace_separated_underscore_2",
        ),
        pytest.param(
            "co2_mole ch4_mole",
            does_not_raise(),
            id="valid_value_whitespace_separated_underscore_3",
        ),
        pytest.param(
            "co2,ch4",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid_value_comma_separated",
        ),
        pytest.param(
            "co2;ch4",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid_value_semicolon_separated",
        ),
        pytest.param(
            "co2-mole",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="invalid_value_hyphen",
        ),
    ),
)
def test_external_variables_validation(external_variables, expectation):
    with expectation:
        validate_external_variables(external_variables)
