"""
Helpers for interchanging with iris
"""

from __future__ import annotations

import iris
import ncdata.iris_xarray
import xarray as xr
from iris.cube import CubeList

from input4mips_validation.xarray_helpers.variables import (
    XRVariableHelper,
    XRVariableProcessorLike,
)

iris.FUTURE.save_split_attrs = True


def ds_from_iris_cubes(
    cubes: CubeList,
    xr_variable_processor: XRVariableProcessorLike = XRVariableHelper(),
) -> xr.Dataset:
    """
    Load an [xarray.Dataset][] from [iris.cube.CubeList][]

    This is a thin wrapper around [ncdata.iris_xarray.cubes_to_xarray][]
    that also handles setting bounds as co-ordinates.

    TODO: raise issue in https://github.com/pp-mo/ncdata

    Parameters
    ----------
    cubes
        Cubes from which to create the dataset

    xr_variable_processor
        Helper to use for processing the variables in xarray objects.

    Returns
    -------
    :
        Loaded dataset
    """
    ds = ncdata.iris_xarray.cubes_to_xarray(cubes)
    bnds_guess = xr_variable_processor.get_ds_bounds_variables(
        ds,
    )
    ds = ds.set_coords(bnds_guess)

    return ds
