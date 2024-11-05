"""
Helpers for time handling
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from typing import Callable

import cftime
import numpy as np
import xarray as xr

MONTHS_PER_YEAR: int = 12
"""Months per year"""


class NonUniqueYearMonths(ValueError):
    """
    Raised when the user tries to convert to year-month with non-unique values

    This happens when the datetime values lead to year-month values that are
    not unique
    """

    def __init__(
        self, unique_vals: Iterable[tuple[int, int]], counts: Iterable[int]
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        unique_vals
            Unique values. In each tuple, the first value is the year and the
            second is the month.

        counts
            Counts of the number of time each unique value appeared in the
            original array
        """
        non_unique = list((v, c) for v, c in zip(unique_vals, counts) if c > 1)

        error_msg = (
            "Your year-month axis is not unique. "
            f"Year-month values with a count > 1: {non_unique}"
        )
        super().__init__(error_msg)


def split_time_to_year_month(
    inp: xr.Dataset,
    time_axis: str = "time",
) -> xr.Dataset:
    """
    Convert the time dimension to year and month without stacking

    This means there is still a single time dimension in the output,
    but there is now also accompanying year and month information.

    Parameters
    ----------
    inp
        Data to convert

    Returns
    -------
        Data with year and month information for the time axis

    Raises
    ------
    NonUniqueYearMonths
        The years and months are not unique
    """
    out = inp.assign_coords(
        {
            "month": inp[time_axis].dt.month,
            "year": inp[time_axis].dt.year,
        }
    ).set_index({time_axis: ("year", "month")})

    # Could be updated when https://github.com/pydata/xarray/issues/7104 is
    # closed
    unique_vals, counts = np.unique(out[time_axis].values, return_counts=True)

    if (counts > 1).any():
        raise NonUniqueYearMonths(unique_vals, counts)

    return out


def default_convert_year_month_to_cftime(year: int, month: int) -> cftime.datetime:
    """
    Convert year-month information to [cftime.datetime][], default implementation

    Parameters
    ----------
    year
        Year

    month
        Month

    Returns
    -------
        Equivalent [cftime.datetime][]
    """
    return cftime.datetime(year, month, 1)


def get_start_of_next_month(
    y: int,
    m: int,
    convert_year_month_to_cftime: Callable[[int, int], cftime.datetime] | None = None,
) -> cftime.datetime:
    """
    Get start of next month

    Parameters
    ----------
    y
        Year

    m
        Month

    convert_year_month_to_cftime
        Callable to use to convert year-month to [cftime.datetime][].
        If not supplied, we use
        [`default_year_month_to_cftime_converter`][input4mips_validation.xarray_helpers.time.default_convert_year_month_to_cftime].

    Returns
    -------
        Start of next month
    """
    if convert_year_month_to_cftime is None:
        convert_year_month_to_cftime = default_convert_year_month_to_cftime

    if m == MONTHS_PER_YEAR:
        m_out = 1
        y_out = y + 1
    else:
        m_out = m + 1
        y_out = y

    return convert_year_month_to_cftime(y_out, m_out)


def add_time_bounds(
    ds: xr.Dataset,
    monthly_time_bounds: bool = True,
    yearly_time_bounds: bool = False,
    output_dim_bounds: str = "bounds",
    create_cftime_datetime: Callable[[int, int, int], cftime.datetime] | None = None,
) -> xr.Dataset:
    """
    Add time bounds to a dataset

    This should be pushed upstream to cf-xarray at some point probably

    Parameters
    ----------
    ds
        Dataset to which to add time bounds

    monthly_time_bounds
        Are we looking at monthly data i.e. should the time bounds run from
        the start of one month to the next (which isn't regular spacing but is
        most often what is desired/required)

    yearly_time_bounds
        Are we looking at yearly data i.e. should the time bounds run from
        the start of one year to the next (which isn't regular spacing but is
        sometimes what is desired/required)

    output_dim_bounds
        What is the name of the bounds dimension
        (either already in `ds` or that should be added)?

    create_cftime_datetime
        Function to use to create [cftime.datetime][] objects from date information.

        If not supplied, we use [cftime.datetime][].

    Returns
    -------
        Dataset with time bounds

    Raises
    ------
    ValueError
        Both `monthly_time_bounds` and `yearly_time_bounds` are `True`.

    Notes
    -----
    There is no copy here, `ds` is modified in place
    (call [xarray.Dataset.copy][] before passing if you don't want this).
    """
    # based on cf-xarray's implementation, to be pushed back upstream at some
    # point
    # https://github.com/xarray-contrib/cf-xarray/pull/441
    # https://github.com/pydata/xarray/issues/7860

    if create_cftime_datetime is None:
        create_cftime_datetime = cftime.datetime

    variable = "time"
    # The suffix _bounds is hard-coded in cf-xarray.
    # Match that here, even though it doesn't seem correct
    # and CF-conventions use "bnds".
    bname = f"{variable}_bounds"

    if bname in ds.variables:
        msg = f"Bounds variable name {bname!r} already exists!"
        raise ValueError(msg)

    if monthly_time_bounds:
        if yearly_time_bounds:
            msg = (
                "Only one of monthly_time_bounds and yearly_time_bounds should be true"
            )
            raise ValueError(msg)

        ds_ym = split_time_to_year_month(ds, time_axis=variable)

        bounds = xr.DataArray(
            [
                [create_cftime_datetime(y, m, 1), get_start_of_next_month(y, m)]
                for y, m in zip(ds_ym.year, ds_ym.month)
            ],
            dims=(variable, "bounds"),
            coords={variable: ds[variable], "bounds": [0, 1]},
        ).transpose(..., "bounds")

    elif yearly_time_bounds:
        # Hacks hacks hacks :)
        bounds = xr.DataArray(
            [
                [create_cftime_datetime(y, 1, 1), create_cftime_datetime(y + 1, 1, 1)]
                for y in ds["time"].dt.year
            ],
            dims=(variable, "bounds"),
            coords={variable: ds[variable], "bounds": [0, 1]},
        ).transpose(..., "bounds")

    else:
        raise NotImplementedError(monthly_time_bounds)

    ds[bname] = bounds
    ds[variable].attrs["bounds"] = bname
    # Ensure that bounds has the same encoding as the variable.
    # Very important for any file that is eventually written to disk.
    ds[bname].encoding = ds[variable].encoding

    return ds


def xr_time_min_max_to_single_value(
    v: xr.DataArray,
) -> cftime.datetime | dt.datetime | np.datetime64:
    """
    Convert the results from calling `min` or `max` to a single value

    Parameters
    ----------
    v
        The results of calling `min` or `max`

    Returns
    -------
        The single minimum or maximum value,
        converted from being an [xarray.DataArray][].
    """
    # TODO: work out what right access is. There must be a better way than this.
    res: cftime.datetime | dt.datetime | np.datetime64 = v.to_dict()["data"]

    return res
