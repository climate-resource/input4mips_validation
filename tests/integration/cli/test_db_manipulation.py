"""
Tests of our database manipulation commands:

- `db add-tree`
- `db validate`
"""

from __future__ import annotations

import datetime as dt
import os
import shutil
import subprocess
from collections.abc import Iterable
from functools import partial
from pathlib import Path

import netCDF4
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.database import (
    Input4MIPsDatabaseEntryFile,
    load_database_file_entries,
)
from input4mips_validation.testing import (
    create_files_in_tree_return_info,
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
DIFFERENT_DRS_CV_SOURCE = (
    Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "different-drs"
).absolute()


def create_db_entries_exp(
    variable_ids: Iterable[str],
    info: dict[str, dict[str, str]],
    version_exp: str,
    fixed_variable_ids: tuple[str, ...] = (),
) -> tuple[Input4MIPsDatabaseEntryFile, ...]:
    db_entries_exp = tuple(
        Input4MIPsDatabaseEntryFile(
            Conventions="CF-1.7",
            activity_id="input4MIPs",
            contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
            creation_date=info[variable_id]["creation_date"],
            dataset_category="GHGConcentrations",
            datetime_end="2010-12-01T00:00:00Z"
            if variable_id not in fixed_variable_ids
            else None,
            datetime_start="2000-01-01T00:00:00Z"
            if variable_id not in fixed_variable_ids
            else None,
            esgf_dataset_master_id=info[variable_id]["esgf_dataset_master_id"],
            filepath=info[variable_id]["filepath"],
            frequency="mon" if variable_id not in fixed_variable_ids else "fx",
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
            time_range="200001-201012"
            if variable_id not in fixed_variable_ids
            else None,
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
        "areacella",
    )
    info = create_files_in_tree_return_info(
        variable_ids=variable_ids,
        units=("ppm", "ppb", "%"),
        fixed_fields=(False, False, True),
        tree_root=tree_root,
        cvs=cvs,
        dataset_category="GHGConcentrations",
    )

    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    db_entries_exp = create_db_entries_exp(
        variable_ids=variable_ids,
        info=info,
        version_exp=version_exp,
        fixed_variable_ids=("areacella",),
    )

    db_dir = tmp_path / "test-create-db-basic"
    # Expect file database to be composed of file entries,
    # each named with their hash.
    exp_created_files = [f"{v['sha256']}.json" for v in info.values()]

    # Then test the CLI
    args = ["db", "create", str(tree_root), "--db-dir", str(db_dir)]
    result = runner.invoke(
        app,
        args,
        env={"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    )

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
    info_new = create_files_in_tree_return_info(
        variable_ids=variable_ids_new,
        units=("ppb", "ppt"),
        fixed_fields=(False, False),
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

    args = ["db", "add-tree", str(tree_root), "--db-dir", str(db_dir)]
    result = runner.invoke(
        app,
        args,
        env={"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    )

    assert result.exit_code == 0, result.exc_info

    created_files = list(db_dir.glob("*.json"))
    assert len(created_files) == len(exp_created_files_post_add)
    for exp_created_file in exp_created_files_post_add:
        assert (db_dir / exp_created_file).exists()

    db_entries_cli_post_add = load_database_file_entries(db_dir)

    assert set(db_entries_cli_post_add) == set(db_entries_exp_post_add)


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
    9. Change the DRS of our CVs and validate again
    10. Check that the status of the database is unchanged
        because all files have already been validated
        (this is deliberate behaviour, tracking which CVs were used for validation
        is not a problem we tackle yet)
    11. Validate with the `--force` flag
    12. Check the status of all files in the database is `False`
    """
    # Note: using the runner to invoke the commands causes things to break.
    # I have no idea why, but this is the reason we use subprocess throughout here.
    input4mips_validation_cli = shutil.which("input4mips-validation")
    subprocess_check_output = partial(
        subprocess.check_output,
        env={
            "INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
            **os.environ,
        },
    )

    cvs = load_cvs(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

    # Create ourselves a tree
    tree_root = tmp_path / "netcdf-files"
    tree_root.mkdir(exist_ok=True, parents=True)
    variable_ids = (
        "mole_fraction_of_carbon_dioxide_in_air",
        "mole_fraction_of_methane_in_air",
        "areacella",
    )
    info = create_files_in_tree_return_info(
        variable_ids=variable_ids,
        units=("ppm", "ppb", "%"),
        fixed_fields=(False, False, True),
        tree_root=tree_root,
        cvs=cvs,
        dataset_category="GHGConcentrations",
    )

    # Break one of the files
    broken_file = info[variable_ids[1]]["filepath"]
    valid_files = [
        info[vid]["filepath"]
        for vid in variable_ids
        if info[vid]["filepath"] != broken_file
    ]
    ncds = netCDF4.Dataset(broken_file, "a")
    # Add units to bounds variable, which isn't allowed
    ncds["lat_bnds"].setncattr("units", "degrees_north")
    ncds.close()

    db_dir = tmp_path / "test-validate-flow"

    # 1. Create the database
    subprocess_check_output(
        [
            input4mips_validation_cli,
            "db",
            "create",
            str(tree_root),
            "--db-dir",
            str(db_dir),
        ],
    )

    # 2. Check initial status
    assert all(
        v.validated_input4mips is None for v in load_database_file_entries(db_dir)
    )

    # 3. Validate the database
    subprocess_check_output(
        [
            input4mips_validation_cli,
            "--logging-level",
            "DEBUG",
            "db",
            "validate",
            "--db-dir",
            str(db_dir),
        ],
    )

    # 4. Check status of files in the database
    db_1 = {v.filepath: v for v in load_database_file_entries(db_dir)}
    assert not db_1[broken_file].validated_input4mips
    assert all(v.validated_input4mips for k, v in db_1.items() if k in valid_files)

    # 5. Add some more files to our tree
    variable_ids = (
        "mole_fraction_of_halon1211_in_air",
        "mole_fraction_of_pfc6116_in_air",
    )
    info = create_files_in_tree_return_info(
        variable_ids=variable_ids,
        units=("ppt", "ppt"),
        fixed_fields=(False, False),
        tree_root=tree_root,
        cvs=cvs,
    )

    # 6. Check status of files in the database
    db_2 = {v.filepath: v for v in load_database_file_entries(db_dir)}
    assert not db_2[broken_file].validated_input4mips
    assert all(v.validated_input4mips for k, v in db_2.items() if k in valid_files)
    assert all(
        v.validated_input4mips is None
        for k, v in db_2.items()
        if k not in valid_files and k != broken_file
    )

    # 7. Validate the database again
    subprocess_check_output(
        [
            input4mips_validation_cli,
            "db",
            "validate",
            "--db-dir",
            str(db_dir),
        ],
    )

    # 8. Check status of files in the database
    db_3 = {v.filepath: v for v in load_database_file_entries(db_dir)}
    assert not db_3[broken_file].validated_input4mips
    assert all(v.validated_input4mips for k, v in db_3.items() if k != broken_file)

    # 9. Change the DRS and validate again
    subprocess_check_output(
        [
            input4mips_validation_cli,
            "db",
            "validate",
            "--db-dir",
            str(db_dir),
        ],
    )

    # 10. Check status of files in the database.
    #     No change from above because we didn't use `--force`
    db_4 = {v.filepath: v for v in load_database_file_entries(db_dir)}
    assert not db_4[broken_file].validated_input4mips
    assert all(v.validated_input4mips for k, v in db_4.items() if k != broken_file)

    # 11. Change the DRS and validate again with the `--force` flag
    subprocess.check_output(
        [  # noqa: S603
            input4mips_validation_cli,
            "db",
            "validate",
            "--db-dir",
            str(db_dir),
            "--force",
        ],
        env={
            "INPUT4MIPS_VALIDATION_CV_SOURCE": DIFFERENT_DRS_CV_SOURCE,
            **os.environ,
        },
    )

    # 12. Check status of files in the database.
    #     Should all be `False` now.
    db_5 = {v.filepath: v for v in load_database_file_entries(db_dir)}
    assert all(v.validated_input4mips is False for k, v in db_5.items())
