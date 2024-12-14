"""
Tests of our validation of the consistency between the filename and the DRS
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.drs_consistency import (
    validate_filename_consistent_with_drs,
)

EXP_ERROR_MSG = "".join(
    [
        re.escape(
            "The `tracking_id` attribute must start with the prefix 'hdl:21.14100/', "
        ),
        r"Received tracking_id='.*'\. ",
    ]
)


@pytest.mark.parametrize(
    "filename, ds_attrs_mods, expectation",
    (
        pytest.param(
            "hdl:21.14100/e3385e8c-08d9-4524-8377-49feb3eaa05e",
            None,
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "e3385e8c-08d9-4524-8377-49feb3eaa05e",
            {"variable_id": "variable"},
            pytest.raises(ValueError, match=EXP_ERROR_MSG),
            id="incorrect_variable_id",
        ),
    ),
)
def test_filename_consistent_with_drs_validation(filename, ds_attrs_mods, expectation):
    if ds_attrs_mods is not None:
        raise NotImplementedError()

    with expectation:
        validate_filename_consistent_with_drs(tracking_id)
