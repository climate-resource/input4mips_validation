"""
Create test data for our docs
"""

from __future__ import annotations

from pathlib import Path

import iris
import ncdata.iris_xarray
import netCDF4
import numpy as np
import pint_xarray  # noqa: F401
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
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.cvs.source_id import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    SourceIDEntry,
    SourceIDValues,
    convert_source_id_entries_to_unstructured_cv,
)
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.serialisation import json_dumps_cv_style
from input4mips_validation.testing import get_valid_ds_min_metadata_example

HERE = Path(__file__).parent


def write_start_file_for_how_to_prepare_a_submission() -> None:
    """
    Write the starting file for how to prepare a submission

    At the time of writing, the notebook we're writing for is
    `docs/how-to-guides/how-to-prepare-a-file-for-submission-to-input4mips.py`.
    """
    out_file = (
        HERE.parent
        / "docs"
        / "how-to-guides"
        / "CH4-em-biomassburning_input4MIPs_emissions_CMIP_CR-CMIP-0-2-0_gn_200001-201012.nc"  # noqa: E501
    )
    variable_name = "biomass_burning_CH4_flux"
    ds, metadata_minimum = get_valid_ds_min_metadata_example(variable_id=variable_name)

    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    cvs = load_cvs(get_raw_cvs_loader("gh:main"))

    input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
        data=ds,
        metadata_minimum=metadata_minimum,
        standard_and_or_long_names={variable_name: {"standard_name": variable_name}},
        cvs=cvs,
        dataset_category="emissions",
        realm="atmos",
    )

    start = input4mips_ds.data.rename({variable_name: "CH4"}).pint.dequantify()
    # Overwrite the attributes to make this match what we want
    start.attrs = {
        "Conventions": "CF-1.7",
        "activity_id": "input4MIPs",
        "comment": "Demo",
        "contact": "zebedee.nicholls@climate-resource.com",
        "creation_date": "2024-07-25T18:23:47Z",
        "data_structure": "grid",
        "dataset_category": "emissions",
        "external_variables": "gridcellarea,sources",
        "frequency": "mon",
        "further_info_url": "www.tbd.invalid",
        "grid_label": "gn",
        "institution": "Climate Resource",
        "institution_id": "DRES",
        "license": "The input4MIPs data linked to this entry is licensed under a Creative Commons Attribution 4.0 International (https://creativecommons.org/licenses/by/4.0/). Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse for terms of use governing CMIP6Plus output, including citation requirements and proper acknowledgment. The data producers and data providers make no warranty, either express or implied, including, but not limited to, warranties of merchantability and fitness for a particular purpose. All liabilities arising from the supply of the information (including any liability arising in negligence) are excluded to the fullest extent permitted by law.",  # noqa: E501
        "mip_era": "CMIP6Plus",
        "nominal_resolution": "25 km",
        "realm": "atmos",
        "references": "Reference to great paper",
        "source": "Climate Resource demo",
        "source_id": "CR-CMIP-0-2-0",
        "source_version": "0.2.0",
        "target_mip": "CMIP",
        "title": "Title here",
        "variable_id": "CH4",
    }
    start["CH4"].attrs = {
        "units": "kg m-2 s-1",
        "standard_name": variable_name,
        "cell_methods": "time: mean",
    }

    cubes = ncdata.iris_xarray.cubes_from_xarray(start)
    if out_file.exists():
        out_file.unlink()

    iris.save(
        cubes,
        out_file,
    )

    # iris won't let you write a file that is broken like this,
    # so break it manually.
    nc_direct = netCDF4.Dataset(
        str(out_file),
        "a",
        format="NETCDF4",
    )
    nc_direct["CH4"].delncattr("long_name")
    nc_direct["CH4"].setncattr("standard_name", variable_name)
    nc_direct["CH4"].setncattr("cell_measures", "area: gridcellarea")
    nc_direct.close()


def main() -> None:
    """
    Write the test files for the docs
    """
    write_start_file_for_how_to_prepare_a_submission()
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
                    long_name=(
                        "input forcing datasets for Model Intercomparison Projects"
                    ),
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
        fh.write("\n")

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
        fh.write("\n")


if __name__ == "__main__":
    typer.run(main)
