"""
Integration tests of handling of the source ID CV
"""
from __future__ import annotations

from pathlib import Path

import pytest

from input4mips_validation.cvs_handling.input4MIPs import (
    SourceIDEntries,
    SourceIDEntry,
    load_source_id_entries,
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
    res = load_source_id_entries(cv_source=input4mips_cv_source)

    assert isinstance(res, SourceIDEntries)
    assert all(isinstance(v, SourceIDEntry) for v in res)

    for source_id, source_id_checks in checks.items():
        matching = res[source_id]

        for k, v in source_id_checks.items():
            assert getattr(matching, k) == v
