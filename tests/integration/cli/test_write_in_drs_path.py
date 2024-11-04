"""
Tests of handling of files that are not in the DRS path, but otherwise correct

This tests a step in the 'Paul' workflow.
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
from functools import partial
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import xarray as xr
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.dataset.dataset import (
    prepare_ds_and_get_frequency,
)
from input4mips_validation.hashing import get_file_hash_sha256
from input4mips_validation.testing import get_valid_ds_min_metadata_example

UR = pint.get_application_registry()

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = (
    Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default"
).absolute()


def test_validate_write_in_drs(tmp_path):
    """
    Test that we can write a file into the DRS path

    The files starts not in the DRS path,
    then we validate it,
    then write it in the DRS path.
    """

    variable_name = "mole_fraction_of_carbon_dioxide_in_air"
    ds, metadata_minimum = get_valid_ds_min_metadata_example(variable_id=variable_name)

    # This is a good trick to remember for, e.g. reducing file sizes.
    ds["lat"].encoding = {"dtype": np.dtypes.Float32DType}
    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    # Create our full, input4MIPs dataset
    cvs = load_cvs(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

    input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
        data=ds,
        metadata_minimum=metadata_minimum,
        cvs=cvs,
        prepare_func=partial(
            prepare_ds_and_get_frequency,
            standard_and_or_long_names={
                variable_name: {"standard_name": variable_name}
            },
        ),
    )

    # Write a correct file as a helper
    helper_root_path = tmp_path / "helper"
    written_file_helper = input4mips_ds.write(root_data_dir=helper_root_path)

    # Copy the file to a directory, without the DRS path
    start_file = tmp_path / "start" / written_file_helper.name
    start_file.parent.mkdir(exist_ok=False, parents=True)
    shutil.copyfile(written_file_helper, start_file)

    write_root_path = tmp_path / "written"
    assert not write_root_path.exists()

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        result = runner.invoke(
            app,
            [
                "validate-file",
                str(start_file),
                "--write-in-drs",
                str(write_root_path),
            ],
        )

    if result.exit_code != 0:
        msg = f"{result.stdout=}\n{result.exc_info=}"
        raise AssertionError(msg)

    written_files = list(write_root_path.rglob("*.nc"))
    assert len(written_files) == 1
    written_file = written_files[0]

    database_entry = Input4MIPsDatabaseEntryFile.from_file(written_file, cvs=cvs)

    ds_attrs = xr.open_dataset(written_file).attrs
    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    database_entry_exp = Input4MIPsDatabaseEntryFile(
        Conventions="CF-1.7",
        activity_id="input4MIPs",
        contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
        creation_date=ds_attrs["creation_date"],
        dataset_category="GHGConcentrations",
        datetime_end="2010-12-01T00:00:00Z",
        datetime_start="2000-01-01T00:00:00Z",
        esgf_dataset_master_id=f"input4MIPs.CMIP6Plus.CMIP.CR.CR-CMIP-0-2-0.atmos.mon.mole-fraction-of-carbon-dioxide-in-air.gn.v{version_exp}",
        filepath=str(written_file),
        frequency="mon",
        further_info_url="http://www.tbd.invalid",
        grid_label="gn",
        institution_id="CR",
        license=(
            "The input4MIPs data linked to this entry "
            "is licensed under a Creative Commons Attribution 4.0 International "
            "(https://creativecommons.org/licenses/by/4.0/). "
            "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
            "for terms of use governing CMIP6Plus output, "
            "including citation requirements and proper acknowledgment. "
            "The data producers and data providers make no warranty, "
            "either express or implied, including, but not limited to, "
            "warranties of merchantability and fitness for a particular purpose. "
            "All liabilities arising from the supply of the information "
            "(including any liability arising in negligence) "
            "are excluded to the fullest extent permitted by law."
        ),
        license_id="CC BY 4.0",
        mip_era="CMIP6Plus",
        nominal_resolution="10000 km",
        product=None,
        realm="atmos",
        region=None,
        sha256=get_file_hash_sha256(written_file),
        source_id="CR-CMIP-0-2-0",
        source_version="0.2.0",
        target_mip="CMIP",
        time_range="200001-201012",
        tracking_id=ds_attrs["tracking_id"],
        variable_id="mole_fraction_of_carbon_dioxide_in_air",
        version=version_exp,
        grid=None,
        institution=None,
        references=None,
        source=None,
    )

    assert database_entry == database_entry_exp
