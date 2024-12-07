"""
Helpers for determining what is and isn't a variable
"""

from __future__ import annotations

from collections.abc import Collection

import xarray as xr


def get_ds_bounds_variables(
    ds: xr.Dataset, bnds_coord_indicators: Collection[str]
) -> tuple[str, ...]:
    """
    Get the bounds variables in a dataset

    Parameters
    ----------
    ds
        Dataset to check

    bnds_coord_indicators
        Strings that indicate that a variable is a bounds variable

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    Returns
    -------
    :
        Bounds variables in the dataset.
    """
    return tuple(
        str(v)
        for v in ds.data_vars
        if any(bci in str(v) for bci in bnds_coord_indicators)
    )


def get_ds_variables(
    ds: xr.Dataset, bnds_coord_indicators: Collection[str]
) -> tuple[str, ...]:
    """
    Get the variables in a dataset

    Parameters
    ----------
    ds
        Dataset to check

    bnds_coord_indicators
        Strings that indicate that a variable is a bounds variable

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    Returns
    -------
    :
        Variables in the dataset, excluding bounds variables.
    """
    bounds_vars = get_ds_bounds_variables(ds, bnds_coord_indicators)

    return tuple(str(v) for v in ds.data_vars if v not in bounds_vars)
