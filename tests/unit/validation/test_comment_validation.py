"""
Tests of our comment validation
"""

from __future__ import annotations

from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.validation.comment import validate_comment

EXP_ERROR_MSG = "".join(
    [
        r"The `comment` attribute must be a string, received comment=.*\.",
    ]
)


@pytest.mark.parametrize(
    "comment, expectation",
    (
        pytest.param(
            "Some comment",
            does_not_raise(),
            id="valid_value",
        ),
        pytest.param(
            "Some comment with new lines\nin it.",
            does_not_raise(),
            id="valid_value_with_newlines",
        ),
        pytest.param(
            ["list", "of", "strings"],
            pytest.raises(TypeError, match=EXP_ERROR_MSG),
            id="list_of_strings",
        ),
        pytest.param(
            ("tuple", "of", "strings"),
            pytest.raises(TypeError, match=EXP_ERROR_MSG),
            id="tuple_of_strings",
        ),
    ),
)
def test_comment_validation(comment, expectation):
    with expectation:
        validate_comment(comment)
