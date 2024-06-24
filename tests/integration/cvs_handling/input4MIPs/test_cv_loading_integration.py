"""
Test loading of CVs

At present, all tests here are based on loading test-data locally.
For loading from different sources, e.g. GitHub,
see `test_raw_cv_loading.py`.
"""
from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import patch

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
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.cvs_validation import (
    assert_cvs_are_valid,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    SourceIDEntries,
    SourceIDEntry,
    SourceIDValues,
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
    "input4mips_cv_source, exp_except_source",
    [
        pytest.param(
            DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            CVsInput4MIPs(
                raw_loader="auto_filled_in_test",  # type: ignore
                activity_id_entries=ActivityIDEntries(
                    (
                        ActivityIDEntry(
                            activity_id="CMIP",
                            values=ActivityIDValues(
                                long_name=(
                                    "CMIP DECK: 1pctCO2, abrupt4xCO2, amip, "
                                    "esm-piControl, esm-historical, historical, "
                                    "and piControl experiments"
                                ),
                                url="https://gmd.copernicus.org/articles/9/1937/2016/gmd-9-1937-2016.pdf",
                            ),
                        ),
                        ActivityIDEntry(
                            activity_id="input4MIPs",
                            values=ActivityIDValues(
                                long_name=(
                                    "input forcing datasets for "
                                    "Model Intercomparison Projects"
                                ),
                                url="https://pcmdi.llnl.gov/mips/input4MIPs/",
                            ),
                        ),
                    ),
                ),
                source_id_entries=SourceIDEntries(
                    (
                        SourceIDEntry(
                            source_id="CR-CMIP-0-2-0",
                            values=SourceIDValues(
                                activity_id="input4MIPs",
                                contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
                                further_info_url="http://www.tbd.invalid",
                                institution="Climate Resource",
                                institution_id="CR",
                                license="""CMIP greenhouse gas concentration data
produced by Climate Resource (CR) is licensed under a
Creative Commons Attribution 4.0 International License
(https://creativecommons.org/licenses/by/4.0/).
Consult https://pcmdi.llnl.gov/CMIP6Plus/TermsOfUse
for terms of use governing CMIP6Plus and input4MIPs output,
including citation requirements and proper acknowledgment.
Further information about this data, can be found at TBD.
The data producers and data providers make no warranty,
either express or implied, including, but not limited to,
warranties of merchantability and fitness
for a particular purpose.
All liabilities arising from the supply of the information
(including any liability arising in negligence)
are excluded to the fullest extent permitted by law.""".replace("\n", " "),
                                mip_era="CMIP6Plus",
                                version="0.2.0",
                            ),
                        ),
                    ),
                ),
            ),
            id="local_test_files",
        ),
    ],
)
def test_load_cvs(input4mips_cv_source, exp_except_source):
    raw_cvs_loader = get_raw_cvs_loader(cv_source=input4mips_cv_source)
    res = load_cvs(raw_cvs_loader=raw_cvs_loader)

    exp = evolve(exp_except_source, raw_loader=raw_cvs_loader)
    # Also checks that we can validate CVs and that exp is valid,
    # which then means res is also valid
    assert_cvs_are_valid(exp)

    assert res == exp

    # Also test setting through environment variables
    environ_patches = {
        "INPUT4MIPS_VALIDATION_CV_SOURCE": input4mips_cv_source,
    }
    with patch.dict(os.environ, environ_patches):
        res = load_cvs()

    assert res == exp


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
