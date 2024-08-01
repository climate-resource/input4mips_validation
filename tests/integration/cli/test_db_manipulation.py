"""
Tests of our database manipulation commands:

- `db add-tree`
- `db validate`
"""

from __future__ import annotations

import datetime as dt
import os
from collections.abc import Iterable
from pathlib import Path
from unittest.mock import patch

import netCDF4
import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import pytest
import xarray as xr
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.database import (
    Input4MIPsDatabaseEntryFile,
    load_database_file_entries,
)
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.hashing import get_file_hash_sha256
from input4mips_validation.testing import get_valid_ds_min_metadata_example
from input4mips_validation.validation.database import validate_database

UR = pint.get_application_registry()
try:
    UR.define("ppb = ppm * 1000")
except pint.errors.RedefinitionError:
    pass

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default").absolute()
)


def add_files_to_tree(
    variable_ids: Iterable[str],
    units: Iterable[str],
    tree_root: Path,
    cvs: Input4MIPsCVs,
) -> dict[str, dict[str, str]]:
    written_files = []
    info = {}
    for variable_id, units in zip(variable_ids, units):
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
        info[variable_id]["filepath"] = str(written_file)
        info[variable_id]["esgf_dataset_master_id"] = str(
            written_file.relative_to(tree_root).parent
        ).replace(os.sep, ".")

    return info


def create_db_entries_exp(
    variable_ids: Iterable[str],
    info: dict[str, dict[str, str]],
    version_exp: str,
) -> tuple[Input4MIPsDatabaseEntryFile, ...]:
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
        for variable_id in variable_ids
    )

    return db_entries_exp


def test_add_flow(tmp_path):
    """
    Test the flow of adding data to a database

    We:

    1. Create two files
    2. Create our database
    3. Ensure that the state of the database is correct
    4. Add another two files
    5. Add them to our database
    6. Ensure that the state of the database is correct
    """
    cvs = load_cvs(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

    # Create ourselves a tree
    tree_root = tmp_path / "netcdf-files"
    tree_root.mkdir(exist_ok=True, parents=True)
    variable_ids = (
        "mole_fraction_of_carbon_dioxide_in_air",
        "mole_fraction_of_methane_in_air",
    )
    info = add_files_to_tree(
        variable_ids=variable_ids,
        units=("ppm", "ppb"),
        tree_root=tree_root,
        cvs=cvs,
    )

    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    db_entries_exp = create_db_entries_exp(
        variable_ids=variable_ids,
        info=info,
        version_exp=version_exp,
    )

    db_dir = tmp_path / "test-create-db-basic"
    # Expect file database to be composed of file entries,
    # each named with their hash.
    exp_created_files = [f"{v['sha256']}.json" for v in info.values()]

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
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

    # Create two more files
    variable_ids_new = (
        "mole_fraction_of_nitrous_oxide_in_air",
        "mole_fraction_of_pfc7118_in_air",
    )
    info_new = add_files_to_tree(
        variable_ids=variable_ids_new,
        units=("ppb", "ppt"),
        tree_root=tree_root,
        cvs=cvs,
    )

    db_entries_exp_new = create_db_entries_exp(
        variable_ids=variable_ids_new,
        info=info_new,
        version_exp=version_exp,
    )
    db_entries_exp_post_add = tuple([*db_entries_exp, *db_entries_exp_new])

    info_post_add = info | info_new
    exp_created_files_post_add = [f"{v['sha256']}.json" for v in info_post_add.values()]

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        args = ["db", "add-tree", str(tree_root), "--db-dir", str(db_dir)]
        result = runner.invoke(app, args)

    assert result.exit_code == 0, result.exc_info

    created_files = list(db_dir.glob("*.json"))
    assert len(created_files) == len(exp_created_files_post_add)
    for exp_created_file in exp_created_files_post_add:
        assert (db_dir / exp_created_file).exists()

    db_entries_cli_post_add = load_database_file_entries(db_dir)

    assert set(db_entries_cli_post_add) == set(db_entries_exp_post_add)


@pytest.mark.skip(reason="WIP")
def test_validate_flow(tmp_path):
    """
    Test the flow of validating data in a database

    We:

    1. Create the database, including one broken file
    2. Check that the validation status of all files in the database is None
    3. Validate the database
    4. Check that the validation status of all files in the database is as expected
       i.e. `True` for all files except the broken one, which should be `False`
    5. Add some more files to our database
    6. Check the validation status of all files in the database.
       The old files' status should be unchanged,
       the new files should have a status of `None`
    7. Validate (would like to check that only new files are validated,
       but this is trickier)
    8. Check the status of all files in the database is as expected
       i.e. `True` for all files except the broken one
    9. Change the DRS of our CVs
    10. Validate
    11. Check that the status of the database is unchanged
        because all files have already been validated
        (this is deliberate behaviour, tracking which CVs were used for validation
        is not a problem we tackle yet)
    12. Validate with the `--force` flag
    13. Check the status of all files in the database is `False`
    """
    cvs = load_cvs(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

    # Create ourselves a tree
    tree_root = tmp_path / "netcdf-files"
    tree_root.mkdir(exist_ok=True, parents=True)
    variable_ids = (
        "mole_fraction_of_carbon_dioxide_in_air",
        "mole_fraction_of_methane_in_air",
    )
    info = add_files_to_tree(
        variable_ids=variable_ids,
        units=("ppm", "ppb"),
        tree_root=tree_root,
        cvs=cvs,
    )

    # Break one of the files
    ncds = netCDF4.Dataset(info[variable_ids[1]]["filepath"], "a")
    # Add units to bounds variable, which isn't allowed
    ncds["lat_bnds"].setncattr("unit", "degrees_north")
    ncds.close()

    db_dir = tmp_path / "test-validate-flow"

    # Create the database
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        args = ["db", "create", str(tree_root), "--db-dir", str(db_dir)]
        result = runner.invoke(app, args)

    ## Validate the database
    # Useful for debugging, do it via the API first
    db = load_database_file_entries(db_dir=db_dir)
    validate_database(db)
    # explode
    # breakpoint()

    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    db_entries_exp = create_db_entries_exp(
        variable_ids=variable_ids,
        info=info,
        version_exp=version_exp,
    )

    # Expect file database to be composed of file entries,
    # each named with their hash.
    exp_created_files = [f"{v['sha256']}.json" for v in info.values()]

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
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

    # Create two more files
    variable_ids_new = (
        "mole_fraction_of_nitrous_oxide_in_air",
        "mole_fraction_of_pfc7118_in_air",
    )
    info_new = add_files_to_tree(
        variable_ids=variable_ids_new,
        units=("ppb", "ppt"),
        tree_root=tree_root,
        cvs=cvs,
    )

    db_entries_exp_new = create_db_entries_exp(
        variable_ids=variable_ids_new,
        info=info_new,
        version_exp=version_exp,
    )
    db_entries_exp_post_add = tuple([*db_entries_exp, *db_entries_exp_new])

    info_post_add = info | info_new
    exp_created_files_post_add = [f"{v['sha256']}.json" for v in info_post_add.values()]

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        args = ["db", "add-tree", str(tree_root), "--db-dir", str(db_dir)]
        result = runner.invoke(app, args)

    assert result.exit_code == 0, result.exc_info

    created_files = list(db_dir.glob("*.json"))
    assert len(created_files) == len(exp_created_files_post_add)
    for exp_created_file in exp_created_files_post_add:
        assert (db_dir / exp_created_file).exists()

    db_entries_cli_post_add = load_database_file_entries(db_dir)

    assert set(db_entries_cli_post_add) == set(db_entries_exp_post_add)
