"""
Test CVs validation
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
from attrs import evolve

from input4mips_validation.cvs_handling.exceptions import NotURLError
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
