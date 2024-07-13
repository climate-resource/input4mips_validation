"""
Integration tests of our CLI
"""

from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import xarray as xr
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadataDataProducerMinimum,
)

UR = pint.get_application_registry()

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = str(
    (
        Path(__file__).parent / ".." / "test-data" / "cvs" / "input4MIPs" / "default"
    ).absolute()
)
# Tests to write:
# - quasi-unit test of passing to function and handling of error raising
# - help messages
# - logging


def test_valid_file_passes(tmp_path):
    """
    Test that we can write a file that passes our validate-file CLI
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
    time = pd.date_range("2000-01-15", periods=120, freq="MS")

    rng = np.random.default_rng()
    ds_data = UR.Quantity(
        rng.random((lon.size, lat.size, time.size)),
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
            standard_long_names={
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
