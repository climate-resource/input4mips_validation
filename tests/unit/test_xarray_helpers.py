"""
Tests of {py:mod}`input4mips_validation.xarray_helpers`
"""
import cftime
import numpy as np
import xarray as xr

from input4mips_validation.xarray_helpers import add_time_bounds


def test_add_time_bounds_monthly():
    time = [cftime.datetime(y, m, 15) for y in range(2020, 2022) for m in range(1, 13)]
    ds = xr.DataArray(
        name="test_add_time_bounds_monthly",
        data=np.arange(48).reshape(24, 2),
        dims=["time", "lat"],
        coords=dict(
            time=time,
            lat=[-45, 45],
        ),
    ).to_dataset()

    start_bounds = [
        cftime.datetime(y, m, 1) for y in range(2020, 2022) for m in range(1, 13)
    ]
    stop_bounds = np.hstack([start_bounds[1:], cftime.datetime(2022, 1, 1)])
    exp_time_bounds = xr.DataArray(
        name="time_bounds",
        data=np.column_stack([start_bounds, stop_bounds]),
        dims=["time", "bounds"],
        coords=dict(time=time, bounds=[0, 1]),
    )
    exp_time_bounds = exp_time_bounds.assign_coords(time_bounds=exp_time_bounds)

    res = add_time_bounds(ds, monthly_time_bounds=True)

    assert res["time"].attrs["bounds"] == "time_bounds"

    xr.testing.assert_equal(
        res["time_bounds"],
        exp_time_bounds,
    )
