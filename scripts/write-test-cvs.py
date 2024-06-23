"""
Write test CV files

This will eventually become redundant, once the CVs format settles
on https://github.com/PCMDI/input4MIPs_CVs
"""
from __future__ import annotations

from pathlib import Path

from input4mips_validation.cvs_handling.input4MIPs import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    SourceIDEntry,
    SourceIDValues,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    convert_source_id_entries_to_unstructured_cv,
)
from input4mips_validation.cvs_handling.serialisation import json_dumps_cv_style

test_input4mips_cvs_dir = (
    Path(__file__).parent
    / ".."
    / "tests"
    / "test-data"
    / "cvs"
    / "input4MIPs"
    / "default"
)

source_id_entries = SourceIDEntries(
    (
        SourceIDEntry(
            source_id="CR-CMIP-0-2-0",
            values=SourceIDValues(
                activity_id="input4MIPs",
                contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
                further_info_url="http://www.tbd.com",
                institution="Climate Resource",
                institution_id="CR",
                license=(
                    "CMIP greenhouse gas concentration data "
                    "produced by Climate Resource (CR) "
                    "is licensed under a "
                    "Creative Commons Attribution 4.0 International License "
                    "(https://creativecommons.org/licenses/by/4.0/). "
                    "Consult https://pcmdi.llnl.gov/CMIP6Plus/TermsOfUse "
                    "for terms of use governing CMIP6Plus and input4MIPs output, "
                    "including citation requirements and proper acknowledgment. "
                    "Further information about this data, can be found at TBD. "
                    "The data producers and data providers make no warranty, "
                    "either express or implied, including, but not limited to, "
                    "warranties of merchantability and fitness "
                    "for a particular purpose. "
                    "All liabilities arising from the supply of the information "
                    "(including any liability arising in negligence) "
                    "are excluded to the fullest extent permitted by law."
                ),
                mip_era="CMIP6Plus",
                version="0.2.0",
            ),
        ),
    )
)

test_input4mips_cvs_dir.mkdir(parents=True, exist_ok=True)
with open(test_input4mips_cvs_dir / SOURCE_ID_FILENAME, "w") as fh:
    fh.write(
        json_dumps_cv_style(
            convert_source_id_entries_to_unstructured_cv(source_id_entries)
        )
    )
