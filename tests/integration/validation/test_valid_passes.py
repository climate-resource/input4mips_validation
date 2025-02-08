"""
This acts as a canary.

If these tests fail, lots of other things will likely go wrong.
"""

from __future__ import annotations

from pathlib import Path

import cftime
import numpy as np
import xarray as xr

from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadataDataProducerMinimum,
)
from input4mips_validation.testing import (
    get_valid_out_path_and_disk_ready_ds,
)
from input4mips_validation.validation.datasets_to_write_to_disk import (
    get_ds_to_write_to_disk_validation_result,
)


def test_valid_ds_passes(test_cvs):
    """
    Test that a valid dataset passes validation
    """
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    # Make sure that there are no errors
    get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    ).raise_if_errors()


def test_variable_ds_region_passes(test_cvs):
    """
    Ensure that having a region variable doesn't cause failure
    """
    root_data_dir = Path("/to/somewhere")

    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
        grid_label="gn",
        nominal_resolution="250 km",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
    )
    regions = ["africa", "red_sea"]
    time = [
        cftime.datetime(y, m, 1) for y in range(2000, 2010 + 1) for m in range(1, 13)
    ]

    rng = np.random.default_rng()
    data = rng.random((len(time), len(regions)))
    units = "K"

    data_xr = xr.DataArray(
        data,
        dims=["time", "lbl"],
        coords=dict(time=time),
        attrs={"standard_name": "air_temperature", "unit": units},
    )
    regions_xr = xr.DataArray(
        regions,
        dims=["lbl"],
        attrs={"standard_name": "region"},
    )
    ds = xr.Dataset(
        data_vars=dict(
            air_temperature=data_xr,
            region=regions_xr,
        ),
    )

    input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
        data=ds,
        metadata_minimum=metadata_minimum,
        dataset_category="Temperature",
        realm="atmos",
        cvs=test_cvs,
    )

    out_path, valid_disk_ready_ds = input4mips_ds.get_out_path_and_disk_ready_dataset(
        root_data_dir=root_data_dir
    )

    res = get_ds_to_write_to_disk_validation_result(
        valid_disk_ready_ds,
        out_path=out_path,
        cvs=test_cvs,
    )

    res.raise_if_errors()
