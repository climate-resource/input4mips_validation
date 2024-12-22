"""
Tests of `input4mips_validation.inference.from_data`
"""

from __future__ import annotations

import re

import cftime
import numpy as np
import pytest
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


def test_time_bounds_has_too_many_dims():
    time_axis = [
        cftime.datetime(y, m, 16) for y in range(2020, 2023) for m in range(1, 13)
    ]
    time_bounds = [
        [
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
    ]

    ds = xr.Dataset(
        data_vars={
            "co2": (("tim", "lat", "lon"), RNG.random((len(time_axis), 6, 6))),
        },
        coords=dict(
            time=("time", time_axis),
            time_bnds=(
                ("extra", "time", "bnds"),
                time_bounds,
            ),
            lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
            lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
        ),
        attrs={},
    )
    ds["time"].attrs["bounds"] = "time_bnds"

    exp_error_msg = re.escape(
        "Expected to find just one non-time dimension for time_bnds. "
        "Inferred: bounds_dim_l=['extra', 'bnds']. "
        "Original dimensions of time_bnds: ('extra', 'time', 'bnds')"
    )
    with pytest.raises(AssertionError, match=exp_error_msg):
        BoundsInfo.from_ds(ds)


@pytest.mark.parametrize("bounds_dim_exp", ("bounds", "bnds", "nv"))
def test_climatology(bounds_dim_exp):
    exp = BoundsInfo(
        time_bounds="not_used",
        bounds_dim=bounds_dim_exp,
        bounds_dim_lower_val=1,
        bounds_dim_upper_val=2,
    )

    time_axis = [
        cftime.datetime(y, m, 16) for y in range(2020, 2023) for m in range(1, 13)
    ]
    climatology_bounds = [
        [
            cftime.datetime(dt.year - 20, dt.month, 1),
            cftime.datetime(
                (dt.year if dt.month < 12 else dt.year + 1) + 20,
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
        coords=(
            dict(
                tim=("tim", time_axis),
                climatology_bounds=(("tim", bounds_dim_exp), climatology_bounds),
                lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
                lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
            )
            | {bounds_dim_exp: (bounds_dim_exp, [1, 2])}
        ),
        attrs={},
    )
    ds["tim"].attrs["climatology"] = "climatology_bounds"

    res = BoundsInfo.from_ds(ds, time_dimension="tim")

    assert res == exp


@pytest.mark.parametrize("bounds_dim_exp", ("bounds", "bnds", "nv"))
def test_no_time_dimension(bounds_dim_exp):
    exp = BoundsInfo(
        time_bounds="not_used",
        bounds_dim=bounds_dim_exp,
        bounds_dim_lower_val=0,
        bounds_dim_upper_val=1,
    )

    lon_step = 18.0
    lon = np.arange(-180.0 + lon_step / 2.0, 180.0 - lon_step / 4.0, lon_step)
    lon_bounds = np.vstack(
        [
            np.arange(-180, 180.0 - lon_step / 2.0, lon_step),
            np.arange(-180 + lon_step, 180.0 + lon_step / 2.0, lon_step),
        ]
    ).T

    lat_step = 15.0
    lat = np.arange(-90.0 + lat_step / 2.0, 90.0 - lat_step / 4.0, lat_step)
    lat_bounds = np.vstack(
        [
            np.arange(-90, 90.0 - lat_step / 2.0, lat_step),
            np.arange(-90 + lat_step, 90.0 + lat_step / 2.0, lat_step),
        ]
    ).T

    ds = xr.Dataset(
        data_vars={
            "areacella": (("lat", "lon"), RNG.random((len(lat), len(lon)))),
        },
        coords=(
            dict(
                lon=("lon", lon),
                lon_bnds=(("lon_bnds", bounds_dim_exp), lon_bounds),
                lat=("lat", lat),
                lat_bnds=(("lat_bnds", bounds_dim_exp), lat_bounds),
            )
        ),
        attrs={},
    )

    res = BoundsInfo.from_ds(ds)

    assert res == exp


def test_can_not_guess_bounds_var():
    time_axis = [
        cftime.datetime(y, m, 16) for y in range(2020, 2023) for m in range(1, 13)
    ]
    climatology_bounds = [
        [
            cftime.datetime(dt.year - 20, dt.month, 1),
            cftime.datetime(
                (dt.year if dt.month < 12 else dt.year + 1) + 20,
                dt.month + 1 if dt.month < 12 else 1,
                1,
            ),
        ]
        for dt in time_axis
    ]

    ds = xr.Dataset(
        data_vars={
            "co2": (("time",), RNG.random(len(time_axis))),
        },
        coords=(
            dict(
                time=("time", time_axis),
                climatology_bounds=(("tim", "bounds_weird"), climatology_bounds),
            )
        ),
        attrs={},
    )
    ds["time"].attrs["climatology"] = "climatology_bounds"

    exp_error_msg = re.escape(
        "Could not guess which variable was the bounds variable. "
        "Guessed guesses=('bounds', 'bnds', 'nv'). ds="
    )
    with pytest.raises(AssertionError, match=exp_error_msg):
        BoundsInfo.from_ds(ds)
