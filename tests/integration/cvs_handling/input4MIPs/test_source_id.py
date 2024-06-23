"""
Integration tests of handling of the source ID CV
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import patch

import pytest
from attrs import evolve

from input4mips_validation.cvs_handling.exceptions import (
    InconsistentWithCVsError,
    NotInCVsError,
)
from input4mips_validation.cvs_handling.input4MIPs import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    SourceIDEntry,
    SourceIDValues,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    convert_raw_cv_to_source_id_entries,
)
from input4mips_validation.cvs_handling.input4MIPs.validation import (
    assert_source_id_entry_is_valid,
)

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
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
)


@pytest.mark.parametrize(
    "input4mips_cv_source, checks",
    (
        pytest.param(
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
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
    # May want to abstract this further later,
    # but I'm not sure what the pattern will be so not doing this just yet.
    raw_cvs_loader = get_raw_cvs_loader(cv_source=input4mips_cv_source)
    raw = raw_cvs_loader.load_raw(filename=SOURCE_ID_FILENAME)
    res = convert_raw_cv_to_source_id_entries(raw=raw)

    assert isinstance(res, SourceIDEntries)
    assert all(isinstance(v, SourceIDEntry) for v in res.entries)

    for entry in res:
        assert_source_id_entry_is_valid(entry, raw_cvs_loader=raw_cvs_loader)

    for source_id, source_id_checks in checks.items():
        matching = res[source_id]

        for k, v in source_id_checks.items():
            assert getattr(matching.values, k) == v


@pytest.mark.parametrize(
    "cv_source, source_id",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-1-0",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "junk",
        ),
    ),
)
def test_source_id_not_in_cv(cv_source, source_id):
    """
    Test that an error is raised if we try and use a source_id that is not in the CV
    """
    values = SourceIDValues(
        activity_id="placeholder",
        contact="placeholder",
        further_info_url="placeholder",
        institution="placeholder",
        institution_id="placeholder",
        license="placeholder",
        mip_era="placeholder",
        version="placeholder",
    )
    with patch.dict(os.environ, {"INPUT4MIPS_VALIDATION_CV_SOURCE": cv_source}):
        raw_cvs_loader = get_raw_cvs_loader()
        source_ids = convert_raw_cv_to_source_id_entries(
            raw_cvs_loader.load_raw(filename=SOURCE_ID_FILENAME)
        ).source_ids

        error_msg = re.escape(
            f"Received source_id={source_id!r}. "
            f"This is not in the available CV values: {source_ids!r}. "
            f"Raw CVs loader: {raw_cvs_loader!r}"
        )
        with pytest.raises(NotInCVsError, match=error_msg):
            assert_source_id_entry_is_valid(
                SourceIDEntry(source_id=source_id, values=values)
            )


@pytest.mark.parametrize(
    "cv_source, source_id, key_to_test, value_to_apply",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "activity_id",
            "inpt",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "contact",
            "zeb@cr.com",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "further_info_url",
            "http://www.tbd.com/elsewhere",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "institution",
            "CR name here",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "institution_id",
            "Cr",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "license",
            "license text",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "mip_era",
            "CMIP7",
        ),
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "version",
            "0.2.1",
        ),
    ),
)
def test_value_conflict_with_source_id_inferred_value(
    cv_source, source_id, key_to_test, value_to_apply
):
    """
    Test that an error is raised if we try and set a value
    that is inconsistent with the value we can infer from the source_id and the CV
    """
    with patch.dict(os.environ, {"INPUT4MIPS_VALIDATION_CV_SOURCE": cv_source}):
        raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
        valid_source_id_entry = convert_raw_cv_to_source_id_entries(
            raw_cvs_loader.load_raw(filename=SOURCE_ID_FILENAME)
        )[0]

        value_according_to_cv = getattr(valid_source_id_entry.values, key_to_test)
        if value_according_to_cv == value_to_apply:
            msg = (
                "The test won't work if the CV's value "
                "and the applied value are the same"
            )
            raise AssertionError(msg)

        values_incorrect = evolve(
            valid_source_id_entry.values, **{key_to_test: value_to_apply}
        )

        error_msg = re.escape(
            f"For source_id={source_id!r}, "
            f"we should have {key_to_test}={value_according_to_cv!r}. "
            f"Received {key_to_test}={value_to_apply!r}. "
            f"Raw CVs loader: {raw_cvs_loader!r}"
        )
        with pytest.raises(InconsistentWithCVsError, match=error_msg):
            assert_source_id_entry_is_valid(
                SourceIDEntry(source_id=source_id, values=values_incorrect)
            )
