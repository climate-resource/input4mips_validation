"""
Test CVs validation
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from attrs import evolve

from input4mips_validation.cvs_handling.exceptions import (
    InternallyInconsistentCVsError,
    NotURLError,
)
from input4mips_validation.cvs_handling.input4MIPs.activity_id import (
    ActivityIDEntries,
    ActivityIDEntry,
    ActivityIDValues,
)
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import (
    load_cvs,
)
from input4mips_validation.cvs_handling.input4MIPs.cvs_validation import (
    assert_cvs_are_valid,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    SourceIDEntries,
    SourceIDEntry,
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


def test_activity_id_is_not_url_error():
    start = load_cvs(
        raw_cvs_loader=get_raw_cvs_loader(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)
    )

    inp = evolve(
        start,
        activity_id_entries=ActivityIDEntries(
            (
                ActivityIDEntry(
                    activity_id="CMIP",
                    values=ActivityIDValues(
                        long_name="Some string",
                        url="Obviously not a URL",
                    ),
                ),
            ),
        ),
    )

    error_msg = re.escape(
        "url for activity_id entry 'CMIP' has a value of 'Obviously not a URL'. "
        "This should be a URL (use `www.tbd.invalid` as a placeholder if you need)."
    )
    with pytest.raises(NotURLError, match=error_msg):
        assert_cvs_are_valid(inp)


@pytest.mark.parametrize(
    "cv_source, source_id, key_to_test, value_to_apply, exp_cv_valid_values_source",
    (
        (
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            "CR-CMIP-0-2-0",
            "activity_id",
            "junk",
            "cvs.activity_id_entries.activity_ids",
        ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "institution_id",
        #     "Cr",
        # ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "license",
        #     "license text",
        # ),
        # (
        #     DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        #     "CR-CMIP-0-2-0",
        #     "mip_era",
        #     "CMIP7",
        # ),
    ),
)
def test_source_id_value_element_inconsistent_with_cv_source_of_truth(
    cv_source, source_id, key_to_test, value_to_apply, exp_cv_valid_values_source
):
    """
    Test that an error is raised if a source ID entry contains a value
    that isn't in the rest of the CVs
    """
    start = load_cvs(
        raw_cvs_loader=get_raw_cvs_loader(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)
    )

    start_source_id_values = start.source_id_entries.entries[0].values
    if getattr(start_source_id_values, key_to_test) == value_to_apply:
        msg = (
            "The test won't work if the starting value "
            "and the bad value are the same"
        )
        raise AssertionError(msg)

    bad_source_id_values = evolve(
        start_source_id_values, **{key_to_test: value_to_apply}
    )
    bad_source_id_entry = SourceIDEntry(
        source_id="bad",
        values=bad_source_id_values,
    )

    inp = evolve(
        start,
        source_id_entries=SourceIDEntries(
            (
                *start.source_id_entries.entries,
                bad_source_id_entry,
            ),
        ),
    )

    error_msg = re.escape(
        f"For source_id 'bad', {key_to_test}={value_to_apply!r}. "
        "However, it must take a value from the collection specified by "
        f"{exp_cv_valid_values_source}, i.e. "
    )
    with pytest.raises(InternallyInconsistentCVsError, match=error_msg):
        assert_cvs_are_valid(inp)
