"""
Testing of :mod:`input4mips_validation.time`
"""
import re
from unittest.mock import Mock, patch

import cftime
import numpy as np
import pytest
import xarray as xr
import xarray.testing as xrt

from input4mips_validation.testing import get_call_kwargs
from input4mips_validation.time import (
    NonUniqueYearMonths,
    convert_time_to_year_month,
    convert_to_time,
    convert_year_month_to_time,
)

RNG = np.random.default_rng()


def test_roundtrip_from_year_month():
    inp = xr.Dataset(
        {"co2": (["lat", "lon", "year", "month"], RNG.random(size=(3, 3, 2, 12)))},
        coords={
            "lon": [0, 120, 240],
            "lat": [-60, 0, 60],
            "year": [2010, 2011],
            "month": range(1, 12 + 1),
        },
    )

    res = convert_time_to_year_month(convert_year_month_to_time(inp))

    xrt.assert_equal(inp, res)


def test_roundtrip_from_time():
    time_axis = [
        cftime.datetime(y, m, d)
        for y in range(2010, 2015)
        for m in range(1, 12 + 1)
        for d in [1]
    ]

    inp = xr.Dataset(
        {"co2": (["lat", "lon", "time"], RNG.random(size=(3, 3, len(time_axis))))},
        coords={
            "lon": [0, 120, 240],
            "lat": [-60, 0, 60],
            "time": time_axis,
        },
    )

    res = convert_year_month_to_time(convert_time_to_year_month(inp))

    xrt.assert_equal(inp, res)


@pytest.mark.parametrize("day, day_exp", ((None, 1), (10, 10)))
@pytest.mark.parametrize(
    "extra_kwargs, extra_kwargs_exp",
    ((None, {}), ({"calendar": "julian"}, {"calendar": "julian"})),
)
@patch("input4mips_validation.time.partial")
@patch("input4mips_validation.time.convert_to_time")
def test_convert_year_month_to_time(  # noqa: PLR0913
    mock_convert_to_time, mock_partial, day, day_exp, extra_kwargs, extra_kwargs_exp
):
    inp = Mock()
    mock_partial.return_value = "partial func"

    call_kwargs = get_call_kwargs(
        (("day", day),),
        extra_kwargs=extra_kwargs,
    )

    convert_year_month_to_time(inp, **call_kwargs)

    mock_partial.assert_called_once_with(
        cftime.datetime, day=day_exp, **extra_kwargs_exp
    )
    mock_convert_to_time.assert_called_once_with(
        inp,
        time_coords=("year", "month"),
        cftime_converter=mock_partial.return_value,
    )


@pytest.mark.parametrize(
    ", ".join(
        ["time_rel_coords", "time_rel_coords_ds", "cftime_converter", "time_exp"]
    ),
    (
        (
            pytest.param(
                ("year", "month"),
                {"year": [2010], "month": range(1, 3 + 1)},
                lambda y, m: cftime.datetime(y, m, m + 1),
                [
                    cftime.datetime(2010, 1, 2),
                    cftime.datetime(2010, 2, 3),
                    cftime.datetime(2010, 3, 4),
                ],
                id="incrementing-day",
            )
        ),
        (
            pytest.param(
                ("year", "day"),
                {"year": [2010], "day": range(1, 3 + 1)},
                lambda y, d: cftime.datetime(y, 2, d),
                [
                    cftime.datetime(2010, 2, 1),
                    cftime.datetime(2010, 2, 2),
                    cftime.datetime(2010, 2, 3),
                ],
                id="add-month",
            )
        ),
    ),
)
def test_convert_to_time(
    time_rel_coords, time_rel_coords_ds, cftime_converter, time_exp
):
    time_exp = xr.DataArray(data=time_exp, dims=["time"], coords={"time": time_exp})

    data_shape = [3, 3] + [len(time_rel_coords_ds[k]) for k in time_rel_coords_ds]
    inp = xr.Dataset(
        {"co2": (["lat", "lon", *list(time_rel_coords)], RNG.random(size=data_shape))},
        coords={"lon": [0, 120, 240], "lat": [-60, 0, 60], **time_rel_coords_ds},
    )
    res = convert_to_time(inp, time_rel_coords, cftime_converter)

    xrt.assert_equal(res["time"], time_exp)


@pytest.mark.parametrize(
    "time, year_exp, month_exp",
    (
        (
            [
                cftime.datetime(2010, 3, 15),
                cftime.datetime(2011, 5, 1),
                cftime.datetime(2015, 12, 31),
            ],
            [2010, 2011, 2015],
            [3, 5, 12],
        ),
        (
            [
                cftime.datetime(y, m, 1)
                for y in range(2010, 2020 + 1)
                for m in range(1, 12 + 1)
            ],
            range(2010, 2020 + 1),
            range(1, 12 + 1),
        ),
    ),
)
@pytest.mark.parametrize("time_axis, time_axis_exp", ((None, "time"), ("t", "t")))
def test_convert_time_to_year_month(
    time, year_exp, month_exp, time_axis, time_axis_exp
):
    year_exp = xr.DataArray(data=year_exp, dims=["year"], coords={"year": year_exp})
    month_exp = xr.DataArray(
        data=month_exp, dims=["month"], coords={"month": month_exp}
    )

    inp = xr.Dataset(
        {"ch4": (["lat", "lon", time_axis_exp], RNG.random(size=(3, 3, len(time))))},
        coords={
            "lon": [0, 120, 240],
            "lat": [-60, 0, 60],
            time_axis_exp: time,
        },
    )

    call_kwargs = get_call_kwargs((("time_axis", time_axis),))

    res = convert_time_to_year_month(inp, **call_kwargs)

    xrt.assert_equal(res["year"], year_exp)
    xrt.assert_equal(res["month"], month_exp)


def test_convert_time_to_year_month_not_unique():
    time_axis = [
        cftime.datetime(2010, 1, 1),
        cftime.datetime(2010, 2, 1),
        cftime.datetime(2010, 2, 15),
        cftime.datetime(2010, 2, 25),
        cftime.datetime(2010, 3, 1),
        cftime.datetime(2010, 3, 31),
        cftime.datetime(2010, 4, 15),
    ]

    inp = xr.Dataset(
        {"co2": (["lat", "lon", "time"], RNG.random(size=(3, 3, len(time_axis))))},
        coords={
            "lon": [0, 120, 240],
            "lat": [-60, 0, 60],
            "time": time_axis,
        },
    )

    error_msg = re.escape(
        "Your year-month axis is not unique. Year-month values with a "
        "count > 1: [((2010, 2), 3), ((2010, 3), 2)]"
    )
    with pytest.raises(NonUniqueYearMonths, match=error_msg):
        convert_time_to_year_month(inp)
