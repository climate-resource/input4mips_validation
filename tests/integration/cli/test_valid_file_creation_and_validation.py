"""
Test that we can create a file which passes our validation tests
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import cftime
import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import xarray as xr
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadataDataProducerMinimum,
    Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum,
)

UR = pint.get_application_registry()
UR.define("ppb = ppm * 1000")

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default").absolute()
)
# Tests to write:
# - quasi-unit test of passing to function and handling of error raising
# - help messages
# - logging
# - (in another file) --write-in-drs-path
#   - test that the flag above causes the file to be written in the correct
#     DRS before the validation is applied
#     (this is the Paul workflow)
# Docs to write:
# - how to use the Paul workflow


def test_validate_written_single_variable_file(tmp_path):
    """
    Test that we can write a single variable file that passes our validate-file CLI
    """
    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
        grid_label="gn",
        nominal_resolution="10000 km",
        product="derived",
        region="global",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
    )

    lon = np.arange(-165.0, 180.0, 30.0, dtype=np.float64)
    lat = np.arange(-82.5, 90.0, 15.0, dtype=np.float64)
    time = [
        cftime.datetime(y, m, 1) for y in range(2000, 2010 + 1) for m in range(1, 13)
    ]

    rng = np.random.default_rng()
    ds_data = UR.Quantity(
        rng.random((lon.size, lat.size, len(time))),
        "ppm",
    )

    ds = xr.Dataset(
        data_vars={
            "mole_fraction_of_carbon_dioxide_in_air": (["lat", "lon", "time"], ds_data),
        },
        coords=dict(
            lon=("lon", lon),
            lat=("lat", lat),
            time=time,
        ),
        attrs={},
    )
    # This is a good trick to remember for, e.g. reducing file sizes.
    ds["lat"].encoding = {"dtype": np.dtypes.Float32DType}
    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
            ds=ds,
            metadata_minimum=metadata_minimum,
            dimensions=("time", "lat", "lon"),
            standard_and_or_long_names={
                "mole_fraction_of_carbon_dioxide_in_air": {
                    "standard_name": "mole_fraction_of_carbon_dioxide_in_air"
                }
            },
        )

    written_file = input4mips_ds.write(root_data_dir=tmp_path)

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        result = runner.invoke(app, ["validate-file", str(written_file)])

    assert result.exit_code == 0, result.exc_info


def test_validate_written_multi_variable_file(tmp_path):
    """
    Test that we can write a multi-variable file that passes our validate-file CLI
    """
    lon = np.arange(-165.0, 180.0, 30.0, dtype=np.float64)
    lat = np.arange(-82.5, 90.0, 15.0, dtype=np.float64)
    time = [
        cftime.datetime(y, m, 1) for y in range(2000, 2010 + 1) for m in range(1, 13)
    ]

    rng = np.random.default_rng()
    ds_data = UR.Quantity(
        rng.random((lon.size, lat.size, len(time))),
        "ppm",
    )

    ds = xr.Dataset(
        data_vars={
            "mole_fraction_of_carbon_dioxide_in_air": (["lat", "lon", "time"], ds_data),
            "mole_fraction_of_methane_in_air": (
                ["lat", "lon", "time"],
                ds_data * 2.3 * UR.Quantity(1, "ppb / ppm"),
            ),
        },
        coords=dict(
            lon=("lon", lon),
            lat=("lat", lat),
            time=time,
        ),
        attrs={},
    )
    # This is a good trick to remember for, e.g. reducing file sizes.
    ds["lat"].encoding = {"dtype": np.dtypes.Float32DType}
    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum(
        dataset_category="GHGConcentrations",
        grid_label="gn",
        nominal_resolution="10000 km",
        product="derived",
        realm="atmos",
        region="global",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
    )

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        input4mips_ds = (
            Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable(
                ds=ds,
                metadata_minimum=metadata_minimum,
                dimensions=("time", "lat", "lon"),
                standard_and_or_long_names={
                    "mole_fraction_of_carbon_dioxide_in_air": {
                        "standard_name": "mole_fraction_of_carbon_dioxide_in_air"
                    },
                    "mole_fraction_of_methane_in_air": {
                        "standard_name": "mole_fraction_of_methane_in_air"
                    },
                },
            )
        )

    written_file = input4mips_ds.write(root_data_dir=tmp_path)

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": DEFAULT_TEST_INPUT4MIPS_CV_SOURCE},
    ):
        result = runner.invoke(app, ["validate-file", str(written_file)])

    assert result.exit_code == 0, result.exc_info
