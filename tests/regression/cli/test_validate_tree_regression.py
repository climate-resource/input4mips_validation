"""
Regression tests of our validate-tree command
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import netCDF4
import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.testing import get_valid_ds_min_metadata_example
from input4mips_validation.validation import validate_tree

UR = pint.get_application_registry()
try:
    UR.define("ppb = ppm * 1000")
except pint.errors.RedefinitionError:
    pass

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default").absolute()
)


def test_errors_html(tmp_path, file_regression):
    """
    Test for any changes in our error-interrogating HTML output
    """
    root_dir_tree = tmp_path / "tree-to-validate"
    root_dir_tree.mkdir()

    html_output_path = tmp_path / "html-errors-dump.html"

    cvs = load_cvs(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

    # Create ourselves a tree with some errors
    def add_disallowed_unit_info(fp: Path) -> None:
        ncds = netCDF4.Dataset(fp, "a")
        # Add units to bounds variable, which isn't allowed
        ncds["lat_bnds"].setncattr("units", "degrees_north")
        ncds.close()

    written_files = []
    for variable_id, units, break_to_apply in (
        ("mole_fraction_of_carbon_dioxide_in_air", "ppm", add_disallowed_unit_info),
        ("mole_fraction_of_methane_in_air", "ppb", None),
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

        written_file = input4mips_ds.write(root_data_dir=root_dir_tree)

        if break_to_apply is not None:
            break_to_apply(written_file)

        written_files.append(written_file)

    # Test the function directly first (helps with debugging)
    validate_tree_result = validate_tree(
        root_dir_tree, cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE
    )

    with open(html_output_path, "w") as fh:
        fh.write(validate_tree_result.to_html())

    file_regression.check(html_output_path)

    # Then test the CLI
    html_output_path.unlink()
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        result = runner.invoke(
            app,
            [
                "validate-tree",
                str(root_dir_tree),
                "--output-html",
                str(html_output_path),
            ],
        )

    assert result.exit_code == 0, result.exc_info

    file_regression.check(html_output_path)
