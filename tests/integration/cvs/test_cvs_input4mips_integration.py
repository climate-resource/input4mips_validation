"""Integration tests of our input4MIPs CV handling"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from input4mips_validation.controlled_vocabularies.handling.input4MIPs import (
    load_source_ids,
)
from input4mips_validation.controlled_vocabularies.handling.input4MIPs.source_id import (  # noqa: E501
    SourceIDEntry,
)


@pytest.mark.parametrize(
    "input4mips_cv_source, checks",
    (
        pytest.param(
            str(
                (
                    Path(__file__).parent
                    / ".."
                    / ".."
                    / "test-data"
                    / "cvs"
                    / "input4MIPs"
                    / "default"
                ).absolute()
            ),
            {
                "CR-CMIP-0-2-0": {
                    "contact": "zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",  # noqa: E501
                    "institution_id": "CR",
                    "mip_era": "CMIP6Plus",
                    "version": "0.2.0",
                }
            },
            id="local_defaults",
        ),
    ),
)
def test_load_source_ids_from_cv(input4mips_cv_source, checks):
    # Test that we can load the source IDs from given sources without error
    with patch.dict(
        os.environ, {"INPUT4MIPS_VALIDATION_INPUT4MIPS_CV_SOURCE": input4mips_cv_source}
    ):
        res = load_source_ids()

    assert isinstance(res, tuple)
    assert all(isinstance(v, SourceIDEntry) for v in res)

    for source_id, source_id_checks in checks.items():
        matching = [v for v in res if v.source_id == source_id]
        assert len(matching) == 1
        matching = matching[0]

        for k, v in source_id_checks.items():
            assert getattr(matching, k) == v
