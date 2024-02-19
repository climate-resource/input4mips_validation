"""
Helpers for working with xarray
"""
from __future__ import annotations

import cftime
import xarray as xr

from input4mips_validation.time import get_start_of_next_month, split_time_to_year_month


def get_ds_variable(dataset: xr.Dataset) -> str:
    """
    Get the variable held by an :obj:`xr.Dataset```

    Parameters
    ----------
    dataset
        Dataset from which to retrieve the variable

    Returns
    -------
        Variable held by the dataset

    Raises
    ------
    AssertionError
        More than one variable is in the dataset.
        For these processing flows, we expect to be handling
        single variable datasets.
    """
    variables: list[str] = list(dataset.data_vars)

    if len(variables) != 1:
        msg = (
            "More than one variable in your data set? "
            "This isn't supported by input4MIPs. "
            f"Variables received: {variables}"
        )
        raise AssertionError(msg)

    return variables[0]


def add_time_bounds(
    ds: xr.Dataset,
    monthly_time_bounds: bool = False,
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
