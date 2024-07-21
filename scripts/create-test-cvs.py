"""
Create test CVs files
"""

from __future__ import annotations

from pathlib import Path

import typer

from input4mips_validation.cvs.activity_id import (
    ACTIVITY_ID_FILENAME,
    ActivityIDEntries,
    ActivityIDEntry,
    ActivityIDValues,
    convert_activity_id_entries_to_unstructured_cv,
)
from input4mips_validation.cvs.drs import (
    DATA_REFERENCE_SYNTAX_FILENAME,
    DataReferenceSyntax,
    convert_drs_to_unstructured_cv,
)
from input4mips_validation.cvs.institution_id import (
    INSTITUTION_ID_FILENAME,
    convert_institution_ids_to_unstructured_cv,
)
from input4mips_validation.cvs.license import (
    LICENSE_FILENAME,
    LicenseEntries,
    LicenseEntry,
    LicenseValues,
    convert_license_entries_to_unstructured_cv,
)
from input4mips_validation.cvs.source_id import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    SourceIDEntry,
    SourceIDValues,
    convert_source_id_entries_to_unstructured_cv,
)
from input4mips_validation.serialisation import json_dumps_cv_style

HERE = Path(__file__).parent


def main() -> None:
    """
    Write the test CVs files
    """
    TEST_CVS_PATH = HERE / ".." / "tests" / "test-data" / "cvs" / "default"
    TEST_CVS_PATH.mkdir(exist_ok=True, parents=True)

    with open(TEST_CVS_PATH / "README.md", "w") as fh:
        fh.write(
            "The files in this directory are auto-generated with "
            "`scripts/create-test-cvs.py`.\n\n"
            "Do not edit them by hand.\n"
        )

    activity_id_entries = ActivityIDEntries(
        (
            ActivityIDEntry(
                activity_id="input4MIPs",
                values=ActivityIDValues(
                    URL="https://pcmdi.llnl.gov/mips/input4MIPs/",
                    long_name="input forcing datasets for Model Intercomparison Projects",
                ),
            ),
        )
    )
    with open(TEST_CVS_PATH / ACTIVITY_ID_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_activity_id_entries_to_unstructured_cv(activity_id_entries)
            )
        )
        fh.write("\n")

    drs = DataReferenceSyntax(
        directory_path_example="input4MIPs/CMIP6Plus/CMIP/PCMDI/PCMDI-AMIP-1-1-9/ocean/mon/tos/gn/v20230512/",
        directory_path_template="<activity_id>/<mip_era>/<target_mip>/<institution_id>/<source_id>/<realm>/<frequency>/<variable_id>/<grid_label>/v<version>",
        filename_example="tos_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc",
        filename_template="<variable_id>_<activity_id>_<dataset_category>_<target_mip>_<source_id>_<grid_label>[_<time_range>].nc",
    )
    with open(TEST_CVS_PATH / DATA_REFERENCE_SYNTAX_FILENAME, "w") as fh:
        fh.write(json_dumps_cv_style(convert_drs_to_unstructured_cv(drs)))

    institution_ids = ("CR",)
    with open(TEST_CVS_PATH / INSTITUTION_ID_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_institution_ids_to_unstructured_cv(institution_ids)
            )
        )
        fh.write("\n")

    license_entries = LicenseEntries(
        (
            LicenseEntry(
                license_id="CC BY 4.0",
                values=LicenseValues(
                    conditions=(
                        "The input4MIPs data linked to this entry is licensed "
                        "under a Creative Commons Attribution 4.0 International "
                        "(https://creativecommons.org/licenses/by/4.0/). "
                        "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
                        "for terms of use governing CMIP6Plus output, "
                        "including citation requirements and proper acknowledgment. "
                        "The data producers and data providers make no warranty, "
                        "either express or implied, including, but not limited to, "
                        "warranties of merchantability "
                        "and fitness for a particular purpose. "
                        "All liabilities arising from the supply of the information "
                        "(including any liability arising in negligence) "
                        "are excluded to the fullest extent permitted by law."
                    ),
                    long_name="Creative Commons Attribution 4.0 International",
                    license_url="https://creativecommons.org/licenses/by/4.0/",
                ),
            ),
        )
    )
    with open(TEST_CVS_PATH / LICENSE_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_license_entries_to_unstructured_cv(license_entries)
            )
        )
        fh.write("\n")

    source_id_entries = SourceIDEntries(
        (
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
    )
    with open(TEST_CVS_PATH / SOURCE_ID_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_source_id_entries_to_unstructured_cv(source_id_entries)
            )
        )


if __name__ == "__main__":
    typer.run(main)
