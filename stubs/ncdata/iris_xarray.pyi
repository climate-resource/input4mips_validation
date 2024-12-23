from typing import Any

import iris.cube
import xarray as xr

def cubes_from_xarray(ds: xr.Dataset) -> iris.cube.CubeList: ...
def cubes_to_xarray(
    cubes: iris.cube.CubeList, xr_load_kwargs: dict[str, Any]
) -> xr.Dataset: ...
