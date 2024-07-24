"""
Support for testing

This covers (or could cover) both testing (e.g. comparing objects)
and generation of test/example instances.
"""

from __future__ import annotations

from typing import Union

import cftime
import numpy as np
import pint
import xarray as xr

from input4mips_validation.dataset import (
    Input4MIPsDatasetMetadataDataProducerMinimum,
)


def get_valid_ds_min_metadata_example(
    variable_id: str = "siconc",
    units: str = "%",
    unit_registry: Union[pint.registry.UnitRegistry, None] = None,
) -> tuple[xr.Dataset, Input4MIPsDatasetMetadataDataProducerMinimum]:
    """
    Get an example of a valid dataset and associated minimum metadata

    The results can be combined to create a
    [`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset].

    Parameters
    ----------
    variable_id
        Variable ID to apply to the dataset

    units
        Units to attach to the dataset

    unit_registry
        Unit registry to use.
        If not supplied, we retrieve it with
        [pint.get_application_registry][].

    Returns
    -------
    dataset :
        Example valid dataset

    minimum_metadata :
        Example minimum metadata
    """
    if unit_registry is None:
        ur: pint.registry.UnitRegistry = pint.get_application_registry()  # type: ignore

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
    ds_data = ur.Quantity(
        rng.random((lon.size, lat.size, len(time))),
        units,
    )

    ds = xr.Dataset(
        data_vars={
            variable_id: (["lat", "lon", "time"], ds_data),
        },
        coords=dict(
            lon=("lon", lon),
            lat=("lat", lat),
            time=time,
        ),
        attrs={},
    )

    return ds, metadata_minimum
