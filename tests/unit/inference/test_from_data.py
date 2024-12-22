"""
Tests of `input4mips_validation.inference.from_data`
"""

from __future__ import annotations

import cftime
import numpy as np
import xarray as xr

from input4mips_validation.inference.from_data import BoundsInfo

RNG = np.random.default_rng()


def test_basic_case():
    exp = BoundsInfo(
        time_bounds="time_bnds",
        bounds_dim="bnds",
        bounds_dim_lower_val=1,
        bounds_dim_upper_val=2,
    )

    time_axis = [
        cftime.datetime(y, m, 16) for y in range(2020, 2023) for m in range(1, 13)
    ]
    time_bounds = [
        [
            cftime.datetime(dt.year, dt.month, 1),
            cftime.datetime(
                dt.year if dt.month < 12 else dt.year + 1,
                dt.month + 1 if dt.month < 12 else 1,
                1,
            ),
        ]
        for dt in time_axis
    ]

    ds = xr.Dataset(
        data_vars={
            "co2": (("tim", "lat", "lon"), RNG.random((len(time_axis), 6, 6))),
        },
        coords=dict(
            tim=("tim", time_axis),
            time_bnds=(("tim", "bnds"), time_bounds),
            bnds=("bnds", [1, 2]),
            lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
            lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
        ),
        attrs={},
    )
    ds["tim"].attrs["bounds"] = "time_bnds"

    res = BoundsInfo.from_ds(ds, time_dimension="tim")

    assert res == exp
