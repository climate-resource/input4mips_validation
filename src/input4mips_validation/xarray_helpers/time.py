"""
Helpers for time handling
"""

from __future__ import annotations

import xarray as xr


def add_time_bounds(
    ds: xr.Dataset,
    monthly_time_bounds: bool = True,
    yearly_time_bounds: bool = False,
    output_dim_bounds: str = "bounds",
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
                [create_datetime(y, m, 1), get_start_of_next_month(y, m)]
                for y, m in zip(ds_ym.year, ds_ym.month)
            ],
            dims=(variable, "bounds"),
            coords={variable: ds[variable], "bounds": [0, 1]},
        ).transpose(..., "bounds")

    elif yearly_time_bounds:
        # Hacks hacks hacks :)
        bounds = xr.DataArray(
            [
                [create_datetime(y, 1, 1), cftime.datetime(y + 1, 1, 1)]
                for y in ds["time"].dt.year
            ],
            dims=(variable, "bounds"),
            coords={variable: ds[variable], "bounds": [0, 1]},
        ).transpose(..., "bounds")

    else:
        raise NotImplementedError(monthly_time_bounds)

    ds.coords[bname] = bounds
    ds[variable].attrs["bounds"] = bname
    # Ensure that bounds has the same encoding as the variable.
    # Very important for any file that is eventually written to disk.
    ds.coords[bname].encoding = ds[variable].encoding

    return ds
