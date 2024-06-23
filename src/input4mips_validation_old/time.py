"""
Time handling
"""
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Protocol

import cftime
import numpy as np

if TYPE_CHECKING:
    from collections.abc import Iterable
    from typing import Any

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


def convert_year_month_to_time(
    inp: xr.Dataset,
    day: int = 1,
    **kwargs: Any,
) -> xr.Dataset:
    """
    Convert year and month co-ordinates into a time axis

    This is a facade to :func:`convert_to_time`

    Parameters
    ----------
    inp
        Data to convert

    day
        Day of the month to assume in output

    **kwargs
        Passed to intialiser of :class:`cftime.datetime`

    Returns
    -------
        Data with time axis
    """
    return convert_to_time(
        inp,
        time_coords=("year", "month"),
        cftime_converter=partial(cftime.datetime, day=day, **kwargs),
    )


class CftimeConverter(Protocol):
    """
    Callable that supports converting stacked time to :obj:`cftime.datetime`
    """

    def __call__(
        self,
        *args: np.float_ | np.int_,
    ) -> cftime.datetime:
        """
        Convert input values to an :obj:`cftime.datetime`
        """


def convert_to_time(
    inp: xr.Dataset,
    time_coords: tuple[str, ...],
    cftime_converter: CftimeConverter,
) -> xr.Dataset:
    """
    Convert some co-ordinates representing time into a time axis

    Parameters
    ----------
    inp
        Data to convert

    time_coords
        Co-ordinates from which to create the time axis

    cftime_converter
        Callable that converts the stacked time co-ordinates to
        :obj:`cftime.datetime`

    Returns
    -------
        Data with time axis
    """
    inp = inp.stack(time=time_coords)
    times = inp["time"].to_numpy()

    inp = inp.drop_vars(("time", *time_coords)).assign_coords(
        {"time": [cftime_converter(*t) for t in times]}
    )

    return inp


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
