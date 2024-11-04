"""
Tests of our validate-tree command
"""

from __future__ import annotations

import os
from functools import partial
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.dataset.dataset import (
    prepare_ds_and_get_frequency,
)
from input4mips_validation.testing import get_valid_ds_min_metadata_example
from input4mips_validation.validation.tree import get_validate_tree_result

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
    Write two files in a tree, then make sure we can validate the tree
    """
    cvs = load_cvs(cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

    # Create ourselves a tree
    written_files = []
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

        written_file = input4mips_ds.write(root_data_dir=tmp_path)

        written_files.append(written_file)

    # Test the function directly first (helps with debugging)
    get_validate_tree_result(
        tmp_path, cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE
    ).raise_if_errors()

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        result = runner.invoke(app, ["validate-tree", str(tmp_path)])

    assert result.exit_code == 0, result.exc_info
