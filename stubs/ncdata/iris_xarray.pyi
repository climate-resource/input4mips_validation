import iris.cube
import xarray as xr

def cubes_from_xarray(ds: xr.Dataset) -> iris.cube.CubeList: ...
