"""
Input/output of data to/from disk
"""

from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path
from typing import Any

import iris
import ncdata.iris_xarray
import xarray as xr

from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.validation.creation_date import CREATION_DATE_FORMAT
from input4mips_validation.validation.datasets_to_write_to_disk import (
    validate_ds_to_write_to_disk,
)

iris.FUTURE.save_split_attrs = True


def write_ds_to_disk(
    ds: xr.Dataset, out_path: Path, cvs: Input4MIPsCVs, **kwargs: Any
) -> Path:
    """
    Write a dataset to disk

    A note for users of this function.
    We convert the dataset to a list of [iris.cube.Cube][]
    with [ncdata.iris_xarray.cubes_from_xarray][]
    and then write the file to disk with [iris][]
    because [iris][] adds CF-conventions upon writing,
    which is needed for input4MIPs data.
    This works smoothly in our experience,
    but the conversion can be tricky to debug.
    If you are having issues, this may be the reason.

    Parameters
    ----------
    ds
        Dataset to write to disk.
        May contain one or more variables.

    out_path
        Path in which to write the dataset

    cvs
        CVs to use to validate the dataset before writing

    **kwargs
        Passed through to [iris.save][]

    Returns
    -------
        Path in which the dataset was written
    """
    # As part of https://github.com/climate-resource/input4mips_validation/issues/14
    # add final validation here for bullet proofness
    # - tracking ID, creation date, comparison with DRS from cvs etc.
    validate_ds_to_write_to_disk(ds=ds, out_path=out_path, cvs=cvs)

    # Having validated, make the target directory and write
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # This raises a warning,
    # because xarray uses a coordinates attribute
    # and iris says this is not allowed.
    # TODO: MR into ncdata to fix/discuss fixing this.
    cubes = ncdata.iris_xarray.cubes_from_xarray(ds)
    iris.save(cubes, out_path, **kwargs)

    return out_path


def generate_tracking_id() -> str:
    """
    Generate tracking ID

    Returns
    -------
        Tracking ID
    """
    # TODO: ask Paul what this hdl business is about
    return "hdl:21.14100/" + str(uuid.uuid4())


def generate_creation_timestamp() -> str:
    """
    Generate creation timestamp, formatted as needed for input4MIPs files

    Returns
    -------
        Creation timestamp
    """
    ts = dt.datetime.now(dt.timezone.utc).replace(
        microsecond=0  # remove microseconds from creation_timestamp
    )

    return ts.strftime(CREATION_DATE_FORMAT)
