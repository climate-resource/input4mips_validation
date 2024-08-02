"""
Create test CVs files
"""

from __future__ import annotations

from pathlib import Path

import typer
from attrs import evolve

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


def dump_cvs(  # noqa: PLR0913
    dir: Path,
    source_id_entries: SourceIDEntries,
    license_entries: LicenseEntries,
    institution_ids: tuple[str, ...],
    drs: DataReferenceSyntax,
    activity_id_entries: ActivityIDEntries,
) -> None:
    """
    Dump CVs to a given directory
    """
    with open(dir / "README.md", "w") as fh:
        fh.write(
            "The files in this directory are auto-generated with "
            f"`{Path(__file__).parent}/{Path(__file__).name}`.\n\n"
            "Do not edit them by hand.\n"
        )

    with open(dir / SOURCE_ID_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_source_id_entries_to_unstructured_cv(source_id_entries)
            )
        )
        fh.write("\n")

    with open(dir / LICENSE_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_license_entries_to_unstructured_cv(license_entries)
            )
        )
        fh.write("\n")

    with open(dir / INSTITUTION_ID_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_institution_ids_to_unstructured_cv(institution_ids)
            )
        )
        fh.write("\n")

    with open(dir / DATA_REFERENCE_SYNTAX_FILENAME, "w") as fh:
        fh.write(json_dumps_cv_style(convert_drs_to_unstructured_cv(drs)))
        fh.write("\n")

    with open(dir / ACTIVITY_ID_FILENAME, "w") as fh:
        fh.write(
            json_dumps_cv_style(
                convert_activity_id_entries_to_unstructured_cv(activity_id_entries)
            )
        )
        fh.write("\n")


def main() -> None:
    """
    Write the test CVs files
    """
    TEST_CVS_PATH = HERE / ".." / "tests" / "test-data" / "cvs"

    TEST_CVS_DEFAULT_PATH = TEST_CVS_PATH / "default"
    TEST_CVS_DEFAULT_PATH.mkdir(exist_ok=True, parents=True)

    TEST_CVS_DIFFERENT_DRS_PATH = TEST_CVS_PATH / "different-drs"
    TEST_CVS_DIFFERENT_DRS_PATH.mkdir(exist_ok=True, parents=True)

    activity_id_entries = ActivityIDEntries(
        (
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
    )

    drs = DataReferenceSyntax(
        directory_path_example="input4MIPs/CMIP6Plus/CMIP/PCMDI/PCMDI-AMIP-1-1-9/ocean/mon/tos/gn/v20230512/",
        directory_path_template="<activity_id>/<mip_era>/<target_mip>/<institution_id>/<source_id>/<realm>/<frequency>/<variable_id>/<grid_label>/v<version>",
        filename_example="tos_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc",
        filename_template="<variable_id>_<activity_id>_<dataset_category>_<target_mip>_<source_id>_<grid_label>[_<time_range>].nc",
    )

    institution_ids = ("CR",)

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

    dump_cvs(
        TEST_CVS_DEFAULT_PATH,
        source_id_entries=source_id_entries,
        license_entries=license_entries,
        institution_ids=institution_ids,
        drs=drs,
        activity_id_entries=activity_id_entries,
    )

    drs_different = evolve(
        drs,
        directory_path_example="PCMDI-AMIP-1-1-9/gn",
        directory_path_template="<source_id>/<grid_label>",
    )

    dump_cvs(
        TEST_CVS_DIFFERENT_DRS_PATH,
        source_id_entries=source_id_entries,
        license_entries=license_entries,
        institution_ids=institution_ids,
        drs=drs_different,
        activity_id_entries=activity_id_entries,
    )


if __name__ == "__main__":
    typer.run(main)
