"""
Tests of our frequency validation
"""

from __future__ import annotations

import datetime as dt
import re
from contextlib import nullcontext as does_not_raise
from pathlib import Path

import cftime
import numpy as np
import pytest
import xarray as xr

from input4mips_validation.inference.from_data import BoundsInfo
from input4mips_validation.validation.frequency import validate_frequency

RNG = np.random.default_rng()


def create_exp_error_msg(data_frequency: str, metadata_frequency: str) -> str:
    res = re.escape(
        "Given the time axis in the data, "
        f"the frequency attribute must be {data_frequency!r}. "
        f"Received frequency={metadata_frequency!r}."
    )

    return res


FIXED_FIELD_DATA = xr.Dataset(
    data_vars={
        "areacella": (("lat", "lon"), RNG.random((6, 6))),
    },
    coords=dict(
        lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
        lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
    ),
    attrs={},
)


def create_monthly_data(years: tuple[int, ...] = (2021, 2022, 2023)) -> xr.Dataset:
    time_axis = [cftime.datetime(y, m, 16) for y in years for m in range(1, 13)]
    time_bounds = [
        [
            cftime.datetime(y, m, 1),
            cftime.datetime(y if m < 12 else y + 1, m + 1 if m < 12 else 1, 1),
        ]
        for y in years
        for m in range(1, 13)
    ]

    res = xr.Dataset(
        data_vars={
            "co2": (("time", "lat", "lon"), RNG.random((len(time_axis), 6, 6))),
        },
        coords=dict(
            time=("time", time_axis),
            time_bounds=(("time", "bnds"), time_bounds),
            lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
            lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
        ),
        attrs={},
    )

    return res


MONTHLY_DATA = create_monthly_data()
MONTHLY_DATA_ACROSS_JULIAN_GREGORIAN_BOUNDARY = create_monthly_data(
    years=tuple(range(1575, 1585))
)


def create_yearly_data(years: tuple[int, ...] = (2021, 2022, 2023)) -> xr.Dataset:
    time_axis = [cftime.datetime(y, 7, 2) for y in years]
    time_bounds = [
        [
            cftime.datetime(y, 1, 1),
            cftime.datetime(y + 1, 1, 1),
        ]
        for y in years
    ]

    res = xr.Dataset(
        data_vars={
            "co2": (("time", "lat", "lon"), RNG.random((len(time_axis), 6, 6))),
        },
        coords=dict(
            time=("time", time_axis),
            time_bounds=(("time", "bnds"), time_bounds),
            lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
            lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
        ),
        attrs={},
    )

    return res


YEARLY_DATA = create_yearly_data()


def create_daily_data(
    days: tuple[cftime.datetime] = (
        cftime.datetime(2023, 7, 29, 12, 0, 0),
        cftime.datetime(2023, 7, 30, 12, 0, 0),
        cftime.datetime(2023, 7, 31, 12, 0, 0),
        cftime.datetime(2023, 8, 1, 12, 0, 0),
        cftime.datetime(2023, 8, 2, 12, 0, 0),
    ),
    # cftime_class: type = cftime.datetime,
    cftime_class: type = cftime.DatetimeGregorian,
) -> xr.Dataset:
    time_axis = list(days)

    time_bounds = []
    for day in time_axis:
        start_day = cftime.datetime(day.year, day.month, day.day)
        end_day = start_day + dt.timedelta(days=1)

        time_bounds.append([start_day, end_day])

    res = xr.Dataset(
        data_vars={
            "co2": (("time", "lat", "lon"), RNG.random((len(time_axis), 6, 6))),
            # "time_bounds": (("time", "bnds"), time_bounds),
        },
        coords=dict(
            time_bounds=(("time", "bnds"), time_bounds),
            time=("time", time_axis),
            lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
            lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
        ),
        attrs={},
    )

    return res


DAILY_DATA = create_daily_data()
DAILY_DATA_ACROSS_JULIAN_GREGORIAN_BOUNDARY = create_daily_data(
    days=(
        cftime.datetime(1582, 10, 2, 12, 0, 0, calendar="gregorian"),
        cftime.datetime(1582, 10, 3, 12, 0, 0, calendar="gregorian"),
        cftime.datetime(1582, 10, 4, 12, 0, 0, calendar="gregorian"),
        cftime.datetime(1582, 10, 15, 12, 0, 0, calendar="gregorian"),
        cftime.datetime(1582, 10, 16, 12, 0, 0, calendar="gregorian"),
        cftime.datetime(1582, 10, 17, 12, 0, 0, calendar="gregorian"),
    ),
)


def create_monthly_climatology_data() -> xr.Dataset:
    time_axis = [cftime.datetime(1850, m, 1) for m in range(1, 13)]

    climatology_bounds = []
    for time_point in time_axis:
        start_year = 1800
        if time_point.month == 12:
            start_month = 12
            end_month = 1
            end_year = 1901

        else:
            start_month = time_point.month
            end_month = start_month + 1
            end_year = 1900

        climatology_bounds.append(
            [
                cftime.datetime(start_year, start_month, 1),
                cftime.datetime(end_year, end_month, 1),
            ]
        )

    res = xr.Dataset(
        data_vars={
            "co2": (("time", "lat", "lon"), RNG.random((len(time_axis), 6, 6))),
        },
        coords=dict(
            time=("time", time_axis),
            # No time_bounds for climatology stuff
            climatology_bounds=(("time", "nv"), climatology_bounds),
            lon=("lon", np.linspace(-180.0 + 15.0, 180.0, 6)),
            lat=("lat", np.linspace(-90.0 + 15.0, 90.0, 6)),
        ),
        attrs={},
    )

    res["co2"].attrs = {"cell_methods": "time: mean over years"}
    res["time"].attrs = {"climatology": "climatology_bounds"}

    return res


MONTHLY_CLIMATOLOGY_DATA = create_monthly_climatology_data()


@pytest.mark.parametrize(
    "ds, frequency, expectation",
    (
        pytest.param(
            FIXED_FIELD_DATA,
            "fx",
            does_not_raise(),
            id="valid_fixed_field",
        ),
        pytest.param(
            MONTHLY_DATA,
            "mon",
            does_not_raise(),
            id="valid_monthly",
        ),
        pytest.param(
            MONTHLY_DATA_ACROSS_JULIAN_GREGORIAN_BOUNDARY,
            "mon",
            does_not_raise(),
            id="valid_monthly_across_julian_gregorian_boundary",
        ),
        pytest.param(
            YEARLY_DATA,
            "yr",
            does_not_raise(),
            id="valid_yr",
        ),
        pytest.param(
            DAILY_DATA,
            "day",
            does_not_raise(),
            id="valid_day",
        ),
        pytest.param(
            DAILY_DATA_ACROSS_JULIAN_GREGORIAN_BOUNDARY,
            "day",
            does_not_raise(),
            id="day_across_julian_gregorian_boundary",
        ),
        pytest.param(
            MONTHLY_DATA,
            "yr",
            pytest.raises(
                ValueError,
                match=create_exp_error_msg(
                    data_frequency="mon",
                    metadata_frequency="yr",
                ),
            ),
            id="mon_data_yr_metadata",
        ),
        pytest.param(
            YEARLY_DATA,
            "mon",
            pytest.raises(
                ValueError,
                match=create_exp_error_msg(
                    data_frequency="yr",
                    metadata_frequency="mon",
                ),
            ),
            id="yr_data_mon_metadata",
        ),
        pytest.param(
            MONTHLY_CLIMATOLOGY_DATA,
            "monC",
            does_not_raise(),
            id="valid_monC",
        ),
        pytest.param(
            MONTHLY_CLIMATOLOGY_DATA,
            "mon",
            pytest.raises(
                ValueError,
                match=create_exp_error_msg(
                    data_frequency="monC",
                    metadata_frequency="mon",
                ),
            ),
            id="monC_data_mon_metadata",
        ),
        # pytest.param(
        #     THREE_HOURLY_DATA,
        #     "to_check",
        #     pytest.raises(NotImplementedError),
        #     id="daily_data",
        # ),
        # Could also consider adding:
        # - climatologies
        # - other frequencies I haven't thought about
        #   (full list here: https://github.com/WCRP-CMIP/CMIP6_CVs/blob/main/CMIP6_frequency.json)
        #   (Table 2 here also helpful for rules: https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf)
    ),
)
@pytest.mark.parametrize(
    "start_from_lazy_loaded_from_disk",
    (
        pytest.param(True, id="lazy-loaded-start"),
        pytest.param(False, id="in-memory-start"),
    ),
)
def test_frequency_validation(
    ds, frequency, expectation, start_from_lazy_loaded_from_disk, tmp_path
):
    if start_from_lazy_loaded_from_disk:
        tmp_file = Path(tmp_path) / "ds.nc"
        ds.to_netcdf(tmp_file)
        ds = xr.open_dataset(tmp_file, use_cftime=True, chunks={})
        for data_var in ds.data_vars:
            assert ds[data_var].chunks is not None, "Test not using dask"

    with expectation:
        validate_frequency(frequency, ds=ds, bounds_info=BoundsInfo(bounds_dim="bnds"))
