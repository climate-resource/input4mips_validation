"""
Integration tests of the Conventions attribute
"""

from __future__ import annotations

import re

import iris
import ncdata.iris
import netCDF4
import pytest

from input4mips_validation.testing import (
    get_valid_out_path_and_disk_ready_ds,
)
from input4mips_validation.validation.error_catching import ValidationResultsStoreError
from input4mips_validation.validation.file import get_validate_file_result


def test_invalid_Conventions_raises(test_cvs, tmpdir):
    """
    Test that an invalid value raises

    For a full list of edge case tests,
    see `tests/unit/validation/test_Conventions_validation.py`.
    """
    invalid_value = "1.7"

    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    cubes = ncdata.iris_xarray.cubes_from_xarray(valid_disk_ready_ds)

    # Have to write file to disk as Conventions disappear on load
    filename = "test.nc"
    tmp_file = tmpdir / filename

    # Write the file to disk
    iris.save(
        cubes,
        str(tmp_file),
        unlimited_dimensions=("time",),
    )

    # Edit the file
    ds = netCDF4.Dataset(tmp_file, "a")
    ds.setncattr("Conventions", invalid_value)
    ds.close()

    res = get_validate_file_result(
        tmp_file,
        cvs=test_cvs,
    )

    error_msg = re.escape("ValueError: The `Conventions`")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()


def test_no_Conventions_raises(test_cvs, tmpdir):
    out_path, valid_disk_ready_ds = get_valid_out_path_and_disk_ready_ds(
        cv_source=test_cvs
    )

    cubes = ncdata.iris_xarray.cubes_from_xarray(valid_disk_ready_ds)

    # Have to write file to disk as Conventions disappear on load
    filename = "test.nc"
    tmp_file = tmpdir / filename

    # Write the file to disk
    iris.save(
        cubes,
        str(tmp_file),
        unlimited_dimensions=("time",),
    )

    # Edit the file
    ds = netCDF4.Dataset(tmp_file, "a")
    ds.delncattr("Conventions")
    ds.close()

    res = get_validate_file_result(
        tmp_file,
        cvs=test_cvs,
    )

    error_msg = re.escape("MissingAttributeError: 'Conventions'")
    with pytest.raises(ValidationResultsStoreError, match=error_msg):
        res.raise_if_errors()
