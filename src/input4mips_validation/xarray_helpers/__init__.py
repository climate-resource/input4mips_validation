"""
Helpers for working with [xarray][]
"""

# Docs on cross-references for the above:
# https://mkdocstrings.github.io/usage/#cross-references-to-other-projects-inventories
from __future__ import annotations

import xarray as xr

from input4mips_validation.xarray_helpers.time import add_time_bounds

__all__ = [
    "add_time_bounds",
    "xr_time_min_max_to_single_value",
]


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
    return v.to_dict()["data"]
