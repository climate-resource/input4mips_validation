"""Helpers for working with {py:mod}`xarray`"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Protocol

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


def convert_time_to_year_month(
    inp: xr.Dataset,
    time_axis: str = "time",
) -> xr.Dataset:
    """
    Convert the time dimension to year and month co-ordinates

    Parameters
    ----------
    inp
        Data to convert

    Returns
    -------
        Data with year and month co-ordinates
    """
    return split_time_to_year_month(
        inp=inp,
        time_axis=time_axis,
    ).unstack(time_axis)


class YearMonthToCFTimeConverter(Protocol):
    """
    Callable that supports converting year month information to :obj:`cftime.datetime`
    """

    def __call__(
        self,
        year: int,
        month: int,
    ) -> cftime.datetime:
        """
        Convert year and month to an :obj:`cftime.datetime`
        """


def get_start_of_next_month(
    y: int,
    m: int,
    convert_year_month_to_cftime: YearMonthToCFTimeConverter | None = None,
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
        Callable to use to convert year-month to :obj:`cftime.datetime`.
        If not supplied, we use :func:`default_year_month_to_cftime_converter`.

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


def default_convert_year_month_to_cftime(year: int, month: int) -> cftime.datetime:
    """
    Convert year-month information to :obj:`cftime.datetime`, default implementation

    Parameters
    ----------
    year
        Year

    month
        Month

    Returns
    -------
        Equivalent :obj:`cftime.datetime`
    """
    return cftime.datetime(year, month, 1)


def add_time_bounds(
    ds: xr.Dataset,
    monthly_time_bounds: bool = True,
    yearly_time_bounds: bool = False,
    output_dim: str = "bounds",
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

    Returns
    -------
        Dataset with time bounds

    Raises
    ------
    ValueError
        Both ``monthly_time_bounds`` and ``yearly_time_bounds`` are ``True``.

    Notes
    -----
    There is no copy here, ``ds`` is modified in place (call
    :meth:`xarray.Dataset.copy` before passing if you don't
    want this).
    """
    # based on cf-xarray's implementation, to be pushed back upstream at some
    # point
    # https://github.com/xarray-contrib/cf-xarray/pull/441
    # https://github.com/pydata/xarray/issues/7860
    variable = "time"
    bname = f"{variable}_bounds"

    if bname in ds.variables:
        raise ValueError(  # noqa: TRY003
            f"Bounds variable name {bname!r} will conflict!"
        )

    if monthly_time_bounds:
        if yearly_time_bounds:
            msg = (
                "Only one of monthly_time_bounds and yearly_time_bounds should be true"
            )
            raise ValueError(msg)

        ds_ym = split_time_to_year_month(ds, time_axis=variable)

        # This may need to be refactored to allow the cftime_converter to be
        # injected, same idea as `convert_to_time`
        bounds = xr.DataArray(
            [
                [cftime.datetime(y, m, 1), get_start_of_next_month(y, m)]
                for y, m in zip(ds_ym.year, ds_ym.month)
            ],
            dims=(variable, "bounds"),
            coords={variable: ds[variable], "bounds": [0, 1]},
        ).transpose(..., "bounds")

    elif yearly_time_bounds:
        # Hacks hacks hacks :)
        # This may need to be refactored to allow the cftime_converter to be
        # injected, same idea as `convert_to_time`
        bounds = xr.DataArray(
            [
                [cftime.datetime(y, 1, 1), cftime.datetime(y + 1, 1, 1)]
                for y in ds["time"].dt.year
            ],
            dims=(variable, "bounds"),
            coords={variable: ds[variable], "bounds": [0, 1]},
        ).transpose(..., "bounds")

    else:
        # TODO: fix this, quite annoying now.
        # This will require some thinking because `ds.cf.add_bounds(dim)`
        # doesn't work with cftime.datetime objects. Probably needs an issue upstream
        # and then a monkey patch or custom function here as a workaround.
        raise NotImplementedError(monthly_time_bounds)

    ds.coords[bname] = bounds
    ds[variable].attrs["bounds"] = bname

    return ds
