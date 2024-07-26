"""
Tests of our create-db command
"""

from __future__ import annotations

import datetime as dt
import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import pytest
import xarray as xr
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.database.creation import create_db_file_entries
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.hashing import get_file_hash_sha256
from input4mips_validation.serialisation import converter_json
from input4mips_validation.testing import get_valid_ds_min_metadata_example

UR = pint.get_application_registry()
try:
    UR.define("ppb = ppm * 1000")
except pint.errors.RedefinitionError:
    pass

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default").absolute()
)


@pytest.mark.parametrize("include_validation", (True, False))
def test_basic(tmp_path, include_validation):
    """
    Write two files in a tree, then make sure we can create the database
    """
    cvs = load_cvs(get_raw_cvs_loader(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE))

    # Create ourselves a tree
    tree_root = tmp_path / "netcdf-files"
    tree_root.mkdir(exist_ok=True, parents=True)
    written_files = []
    info = {}
    for variable_id, units in (
        ("mole_fraction_of_carbon_dioxide_in_air", "ppm"),
        ("mole_fraction_of_methane_in_air", "ppb"),
    ):
        ds, metadata_minimum = get_valid_ds_min_metadata_example(
            variable_id=variable_id, units=units
        )
        ds["time"].encoding = {
            "calendar": "proleptic_gregorian",
            "units": "days since 1850-01-01 00:00:00",
            # Time has to be encoded as float
            # to ensure that half-days etc. are handled.
            "dtype": np.dtypes.Float32DType,
        }

        input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
            data=ds,
            metadata_minimum=metadata_minimum,
            standard_and_or_long_names={variable_id: {"standard_name": variable_id}},
            cvs=cvs,
        )

        written_file = input4mips_ds.write(root_data_dir=tree_root)

        written_files.append(written_file)

        ds = xr.open_dataset(written_file)
        info[variable_id] = {k: ds.attrs[k] for k in ["creation_date", "tracking_id"]}
        info[variable_id]["sha256"] = get_file_hash_sha256(written_file)

    # Test the function directly first (helps with debugging)
    db_entries = create_db_file_entries(
        tree_root, cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE
    )

    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    db_entries_exp = tuple(
        Input4MIPsDatabaseEntryFile(
            Conventions="CF-1.7",
            activity_id="input4MIPs",
            contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
            creation_date=info[variable_id]["creation_date"],
            dataset_category="GHGConcentrations",
            datetime_end="2010-12-01T00:00:00Z",
            datetime_start="2000-01-01T00:00:00Z",
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
            sha256=info[variable_id]["sha256"],
            source_id="CR-CMIP-0-2-0",
            source_version="0.2.0",
            target_mip="CMIP",
            time_range="200001-201012",
            tracking_id=info[variable_id]["tracking_id"],
            variable_id=variable_id,
            version=version_exp,
            grid=None,
            institution=None,
            references=None,
            source=None,
        )
        for variable_id in [
            "mole_fraction_of_carbon_dioxide_in_air",
            "mole_fraction_of_methane_in_air",
        ]
    )

    assert db_entries == db_entries_exp

    db_file = tmp_path / "test_create_db_basic.json"
    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        args = ["create-db", str(tree_root), "--db-file", str(db_file)]
        if not include_validation:
            args.append("--no-validate")

        result = runner.invoke(app, args)

    assert result.exit_code == 0, result.exc_info

    with open(db_file) as fh:
        db_entries_cli = converter_json.loads(
            fh.read(), tuple[Input4MIPsDatabaseEntryFile, ...]
        )

    assert db_entries_cli == db_entries_exp
