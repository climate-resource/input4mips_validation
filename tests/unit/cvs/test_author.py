"""
Tests of `input4mips_validation.cvs.author`
"""

from __future__ import annotations

import re
from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.cvs.author import Author
from input4mips_validation.validation.regexp import (
    DoesNotMatchRegexpError,
)


@pytest.mark.parametrize(
    "modifications, expected",
    (
        pytest.param({}, does_not_raise(), id="valid"),
        pytest.param(
            {"email": "tim"},
            pytest.raises(
                ValueError,
                match="The given value is clearly not an email. Received email='tim'",
            ),
            id="invalid-email",
        ),
        pytest.param(
            {"affiliations": "single string"},
            pytest.raises(TypeError, match="'affiliations' must be <class 'tuple'>"),
            id="affiliations-single-string",
        ),
        pytest.param(
            {"affiliations": ["list", "of", "strings like this"]},
            pytest.raises(TypeError, match="'affiliations' must be <class 'tuple'>"),
            id="affiliations-list",
        ),
        pytest.param(
            {"orcid": "1234-1234-4321-001X"},
            does_not_raise(),
            id="valid-orcid-ending-in-x",
        ),
        pytest.param(
            {"orcid": "1234"},
            pytest.raises(
                DoesNotMatchRegexpError,
                match=re.escape(
                    "value='1234' does not match "
                    "regexp_to_match='[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]'"
                ),
            ),
            id="invalid-orcid",
        ),
    ),
)
def test_validation(modifications, expected):
    init_kwargs = dict(
        name="Zebedee Nicholls",
        email="zebedee.nicholls@climate-resource.com",
        affiliations=(
            "Climate Resource, Melbourne, Victoria, Australia",
            "Energy, Climate and Environment Program, International Institute for Applied Systems Analysis (IIASA), 2361 Laxenburg, Austria",  # noqa: E501
            "School of Geography, Earth and Atmospheric Sciences, The University of Melbourne, Melbourne, Victoria, Australia",  # noqa: E501
        ),
        orcid="0000-0002-4767-2723",
    )

    for key, value in modifications.items():
        init_kwargs[key] = value

    with expected:
        Author(**init_kwargs)
