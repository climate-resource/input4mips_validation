"""
Tests of `validate-file` behaviour
"""

from __future__ import annotations

import os
import re
from functools import partial
from pathlib import Path
from unittest.mock import patch

import netCDF4
import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import pytest
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.dataset.dataset import (
    prepare_ds_and_get_frequency,
)
from input4mips_validation.testing import get_valid_ds_min_metadata_example
from input4mips_validation.validation.error_catching import ValidationResultsStoreError
from input4mips_validation.validation.file import get_validate_file_result

UR = pint.get_application_registry()
try:
    UR.define("ppb = ppm * 1000")
except pint.errors.RedefinitionError:
    pass

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = (
    Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default"
).absolute()


def test_validate_written_single_variable_file(tmp_path):
    """
    Test that we can write a single variable file that passes our validate-file CLI
    """
    variable_name = "mole_fraction_of_carbon_dioxide_in_air"
    ds, metadata_minimum = get_valid_ds_min_metadata_example(variable_id=variable_name)

    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
            data=ds,
            metadata_minimum=metadata_minimum,
            prepare_func=partial(
                prepare_ds_and_get_frequency,
                standard_and_or_long_names={
                    variable_name: {"standard_name": variable_name}
                },
            ),
        )

    written_file = input4mips_ds.write(root_data_dir=tmp_path)

    # Make sure that the starting file passes
    get_validate_file_result(
        written_file, cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE
    ).raise_if_errors()

    # Add an attribute that shouldn't be there.
    # This induces a warning in the CF-checker.
    ncd = netCDF4.Dataset(written_file, "a")
    ncd["lat_bnds"].setncattr("units", "degrees_north")
    ncd.close()

    # The written file should now fail validation
    error_msg = re.escape(
        "WARN: (7.1): Boundary var lat_bnds should not have attribute units"
    )
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        get_validate_file_result(
            written_file, cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE
        ).raise_if_errors()

    # The file should pass if we set the right flag
    get_validate_file_result(
        written_file,
        cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        allow_cf_checker_warnings=True,
    ).raise_if_errors()

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        result = runner.invoke(
            app, ["validate-file", str(written_file), "--allow-cf-checker-warnings"]
        )

    assert result.exit_code == 0, result.exc_info
