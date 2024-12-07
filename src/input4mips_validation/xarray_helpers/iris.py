"""
Helpers for interchanging with iris
"""

from __future__ import annotations

from collections.abc import Collection

import iris
import ncdata.iris_xarray
import xarray as xr
from iris.cube import CubeList

from input4mips_validation.xarray_helpers.variables import get_ds_bounds_variables

iris.FUTURE.save_split_attrs = True


def ds_from_iris_cubes(
    cubes: CubeList,
    bnds_coord_indicators: Collection[str] = {"bnds", "bounds"},
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

    bnds_coord_indicators
        Strings that indicate that a variable is a bounds variable

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    Returns
    -------
    :
        Loaded dataset
    """
    ds = ncdata.iris_xarray.cubes_to_xarray(cubes)
    # Guess that everything which has "bnds" in it is a co-ordinate.
    # This is definitely a pain point when loading data from a file written with iris.
    # TBD whether a true expert has any ideas.
    bnds_guess = get_ds_bounds_variables(
        ds, bnds_coord_indicators=bnds_coord_indicators
    )
    ds = ds.set_coords(bnds_guess)

    return ds
