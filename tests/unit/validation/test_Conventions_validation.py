"""
Tests of our Conventions validation
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.Conventions import validate_Conventions

EXP_ERROR_MSG = "".join(
    [
        re.escape(
            "The `Conventions` attribute must be of the form 'CF-X.Y', "
            r"i.e. match the regular expression 'CF-[0-9]+\\.[0-9]+'. ",
        ),
        r"Received Conventions='.*'\.",
    ]
)


@pytest.mark.parametrize(
    "Conventions, expectation",
    (
        pytest.param(
            "CF-1.8",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "CF-1.7",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "CF-10.70",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "CF 1.7",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="space_instead_of_hyphen",
        ),
        pytest.param(
            "1.7",
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="missing_prefix",
        ),
    ),
)
def test_Conventions_validation(Conventions, expectation):
    with expectation:
        validate_Conventions(Conventions)
