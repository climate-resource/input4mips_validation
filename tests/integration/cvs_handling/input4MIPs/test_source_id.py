"""
Integration tests of handling of the source ID CV
"""
from __future__ import annotations

from pathlib import Path

import pytest

from input4mips_validation.cvs_handling.input4MIPs import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    SourceIDEntry,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_cvs_root,
    load_raw_cv,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    convert_raw_cv_to_source_id_entries,
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
    cvs_root = get_cvs_root(cv_source=input4mips_cv_source)
    raw = load_raw_cv(filename=SOURCE_ID_FILENAME, root=cvs_root)
    res = convert_raw_cv_to_source_id_entries(raw=raw)

    assert isinstance(res, SourceIDEntries)
    assert all(isinstance(v, SourceIDEntry) for v in res.entries)

    for source_id, source_id_checks in checks.items():
        matching = res[source_id]

        for k, v in source_id_checks.items():
            assert getattr(matching.values, k) == v
