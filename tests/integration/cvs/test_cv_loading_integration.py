"""
Test loading of CVs

This just tests loading from the test data, because that is what we control.
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import pytest

from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.cvs.activity_id import (
    ActivityIDEntries,
    ActivityIDEntry,
    ActivityIDValues,
)
from input4mips_validation.cvs.drs import DataReferenceSyntax
from input4mips_validation.cvs.license import (
    LicenseEntries,
    LicenseEntry,
    LicenseValues,
)
from input4mips_validation.cvs.loading import load_cvs, load_cvs_known_loader
from input4mips_validation.cvs.loading_raw import (
    RawCVLoaderLocal,
    get_raw_cvs_loader,
)
from input4mips_validation.cvs.source_id import (
    SourceIDEntries,
    SourceIDEntry,
    SourceIDValues,
)


@pytest.mark.parametrize(
    "input4mips_cv_source",
    (
        pytest.param(
            str(
                (
                    Path(__file__).parent
                    / ".."
                    / ".."
                    / "test-data"
                    / "cvs"
                    / "default"
                ).absolute()
            ),
            id="str",
        ),
        pytest.param(
            (
                Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default"
            ).absolute(),
            id="Path",
        ),
    ),
)
def test_load_cvs(input4mips_cv_source):
    raw_cvs_loader = get_raw_cvs_loader(cv_source=input4mips_cv_source)
    res = load_cvs_known_loader(raw_cvs_loader=raw_cvs_loader)

    exp = Input4MIPsCVs(
        raw_loader=RawCVLoaderLocal(root_dir=Path(input4mips_cv_source)),
        DRS=DataReferenceSyntax(
            directory_path_template="<activity_id>/<mip_era>/<target_mip>/<institution_id>/<source_id>/<realm>/<frequency>/<variable_id>/<grid_label>/v<version>",
            directory_path_example="input4MIPs/CMIP6Plus/CMIP/PCMDI/PCMDI-AMIP-1-1-9/ocean/mon/tos/gn/v20230512/",
            filename_template="<variable_id>_<activity_id>_<dataset_category>_<target_mip>_<source_id>_<grid_label>[_<time_range>].nc",
            filename_example="tos_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc",
        ),
        activity_id_entries=ActivityIDEntries(
            entries=(
                ActivityIDEntry(
                    activity_id="input4MIPs",
                    values=ActivityIDValues(
                        URL="https://pcmdi.llnl.gov/mips/input4MIPs/",
                        long_name=(
                            "input forcing datasets for Model Intercomparison Projects"
                        ),
                    ),
                ),
            )
        ),
        institution_ids=("CR",),
        license_entries=LicenseEntries(
            entries=(
                LicenseEntry(
                    license_id="CC BY 4.0",
                    values=LicenseValues(
                        conditions=(
                            "The input4MIPs data linked to this entry is licensed "
                            "under a Creative Commons Attribution 4.0 International "
                            "(https://creativecommons.org/licenses/by/4.0/). "
                            "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
                            "for terms of use governing CMIP6Plus output, "
                            "including citation requirements "
                            "and proper acknowledgment. "
                            "The data producers and data providers make no warranty, "
                            "either express or implied, including, but not limited to, "
                            "warranties of merchantability "
                            "and fitness for a particular purpose. "
                            "All liabilities arising "
                            "from the supply of the information "
                            "(including any liability arising in negligence) "
                            "are excluded to the fullest extent permitted by law."
                        ),
                        license_url="https://creativecommons.org/licenses/by/4.0/",
                        long_name="Creative Commons Attribution 4.0 International",
                    ),
                ),
            )
        ),
        source_id_entries=SourceIDEntries(
            entries=(
                SourceIDEntry(
                    source_id="CR-CMIP-0-2-0",
                    values=SourceIDValues(
                        contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
                        further_info_url="http://www.tbd.invalid",
                        institution_id="CR",
                        license_id="CC BY 4.0",
                        mip_era="CMIP6Plus",
                        source_version="0.2.0",
                    ),
                ),
            )
        ),
    )
    assert res == exp

    # Also test loading, where source is set through environment variables
    environ_patches = {
        "INPUT4MIPS_VALIDATION_CV_SOURCE": str(input4mips_cv_source),
    }
    with patch.dict(os.environ, environ_patches):
        res = load_cvs()

    assert res == exp
