"""
Tests of our `db create` command
"""

from __future__ import annotations

import datetime as dt
import os
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
from input4mips_validation.database import (
    Input4MIPsDatabaseEntryFile,
    load_database_file_entries,
)
from input4mips_validation.database.creation import create_db_file_entries
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.dataset.dataset import (
    prepare_ds_and_get_frequency,
)
from input4mips_validation.hashing import get_file_hash_sha256
from input4mips_validation.testing import (
    get_valid_ds_min_metadata_example,
)

UR = pint.get_application_registry()
try:
    UR.define("ppb = ppm * 1000")
except pint.errors.RedefinitionError:
    pass

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = (
    Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default"
).absolute()


def test_basic(tmp_path):
    """
    Write two files in a tree, then make sure we can create the database
    """
    cvs = load_cvs(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

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
            cvs=cvs,
            prepare_func=partial(
                prepare_ds_and_get_frequency,
                standard_and_or_long_names={
                    variable_id: {"standard_name": variable_id}
                },
            ),
        )

        written_file = input4mips_ds.write(root_data_dir=tree_root)

        written_files.append(written_file)

        ds = xr.open_dataset(written_file)
        info[variable_id] = {k: ds.attrs[k] for k in ["creation_date", "tracking_id"]}
        info[variable_id]["sha256"] = get_file_hash_sha256(written_file)
        info[variable_id]["filepath"] = str(written_file)
        info[variable_id]["esgf_dataset_master_id"] = str(
            written_file.relative_to(tree_root).parent
        ).replace(os.sep, ".")

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
            esgf_dataset_master_id=info[variable_id]["esgf_dataset_master_id"],
            filepath=info[variable_id]["filepath"],
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

    # Test the function directly first (helps with debugging)
    db_entries = create_db_file_entries(
        tree_root.rglob("*.nc"), cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE
    )

    assert set(db_entries) == set(db_entries_exp)

    db_dir = tmp_path / "test-create-db-basic"

    # Expect file database to be composed of file entries,
    # each named with their hash.
    exp_created_files = [f"{v['sha256']}.json" for v in info.values()]

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        args = ["db", "create", str(tree_root), "--db-dir", str(db_dir)]
        result = runner.invoke(app, args)

    assert result.exit_code == 0, result.exc_info

    created_files = list(db_dir.glob("*.json"))
    assert len(created_files) == len(exp_created_files)
    for exp_created_file in exp_created_files:
        assert (db_dir / exp_created_file).exists()

    db_entries_cli = load_database_file_entries(db_dir)

    assert set(db_entries_cli) == set(db_entries_exp)
