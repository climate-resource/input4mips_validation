"""
Support for testing

This covers (or could cover) both testing (e.g. comparing objects)
and generation of test/example instances.
"""

from __future__ import annotations

import os
from collections.abc import Collection
from functools import partial
from pathlib import Path
from typing import Any, Optional, Union

import cftime
import numpy as np
import pint
import xarray as xr

from input4mips_validation.cvs import Input4MIPsCVs, load_cvs
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadataDataProducerMinimum,
)
from input4mips_validation.dataset.dataset import (
    prepare_ds_and_get_frequency,
)
from input4mips_validation.hashing import get_file_hash_sha256


def get_valid_ds_min_metadata_example(
    variable_id: str = "siconc",
    units: str = "%",
    unit_registry: Union[pint.registry.UnitRegistry, None] = None,
    fixed_field: bool = False,
) -> tuple[xr.Dataset, Input4MIPsDatasetMetadataDataProducerMinimum]:
    """
    Get an example of a valid dataset and associated minimum metadata

    The results can be combined to create a
    [`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset].

    Parameters
    ----------
    variable_id
        Variable ID to apply to the dataset

    units
        Units to attach to the dataset

    unit_registry
        Unit registry to use.
        If not supplied, we retrieve it with
        [pint.get_application_registry][].

    fixed_field
        Should we return a fixed field dataset?

    Returns
    -------
    dataset :
        Example valid dataset

    minimum_metadata :
        Example minimum metadata
    """
    if unit_registry is None:
        ur: pint.registry.UnitRegistry = pint.get_application_registry()  # type: ignore

    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
        grid_label="gn",
        nominal_resolution="10000 km",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
    )

    lon = np.arange(-165.0, 180.0, 15.0, dtype=np.float64)
    lat = np.arange(-82.5, 90.0, 15.0, dtype=np.float64)

    rng = np.random.default_rng()
    if not fixed_field:
        time = [
            cftime.datetime(y, m, 1)
            for y in range(2000, 2010 + 1)
            for m in range(1, 13)
        ]

        ds_data = ur.Quantity(
            rng.random((lat.size, lon.size, len(time))),
            units,
        )
        dimensions = ["lat", "lon", "time"]
        coords = dict(
            lon=("lon", lon),
            lat=("lat", lat),
            time=time,
        )

    else:
        ds_data = ur.Quantity(
            rng.random((lat.size, lon.size)),
            units,
        )
        dimensions = ["lat", "lon"]
        coords = dict(
            lon=("lon", lon),
            lat=("lat", lat),
        )

    ds = xr.Dataset(
        data_vars={
            variable_id: (dimensions, ds_data),
        },
        coords=coords,
        attrs={},
    )

    return ds, metadata_minimum


def get_valid_ds_min_metadata_example_climatology(
    variable_id: str = "co2",
    units: str = "ppm",
    unit_registry: Union[pint.registry.UnitRegistry, None] = None,
) -> tuple[xr.Dataset, Input4MIPsDatasetMetadataDataProducerMinimum]:
    """
    Get an example of a valid climatology dataset and associated minimum metadata

    The results can be combined to create a
    [`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset].

    Parameters
    ----------
    variable_id
        Variable ID to apply to the dataset

    units
        Units to attach to the dataset

    unit_registry
        Unit registry to use.
        If not supplied, we retrieve it with
        [pint.get_application_registry][].

    Returns
    -------
    dataset :
        Example valid dataset

    minimum_metadata :
        Example minimum metadata
    """
    if unit_registry is None:
        ur: pint.registry.UnitRegistry = pint.get_application_registry()  # type: ignore

    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
        grid_label="gn",
        nominal_resolution="10000 km",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
    )

    lon = np.arange(-165.0, 180.0, 15.0, dtype=np.float64)
    lat = np.arange(-82.5, 90.0, 15.0, dtype=np.float64)

    rng = np.random.default_rng()

    time = [cftime.datetime(2000, m, 1) for m in range(1, 13)]
    climatology_bounds = []
    for time_point in time:
        start_year = 1985
        if time_point.month == 12:
            start_month = 12
            end_month = 1
            end_year = 2016

        else:
            start_month = time_point.month
            end_month = start_month + 1
            end_year = 2015

        climatology_bounds.append(
            [
                cftime.datetime(start_year, start_month, 1),
                cftime.datetime(end_year, end_month, 1),
            ]
        )

    ds_data = ur.Quantity(
        rng.random((lat.size, lon.size, len(time))),
        units,
    )
    dimensions = ["lat", "lon", "time"]
    coords = dict(
        lon=("lon", lon),
        lat=("lat", lat),
        time=time,
        climatology_bounds=(("time", "nv"), climatology_bounds),
    )

    ds = xr.Dataset(
        data_vars={
            variable_id: (dimensions, ds_data),
        },
        coords=coords,
        attrs={},
    )
    ds[variable_id].attrs = {"cell_methods": "time: mean over years"}
    ds["time"].attrs = {"climatology": "climatology_bounds"}

    return ds, metadata_minimum


def get_valid_out_path_and_disk_ready_ds(
    variable_name: str = "mole_fraction_of_carbon_dioxide_in_air",
    time_encoding: dict[str, Any] | None = None,
    cv_source: str | Input4MIPsCVs = "gh:v6.6.0",
    root_data_dir: Path = Path("/to/somewhere"),
) -> tuple[Path, xr.Dataset]:
    """
    Get a valid ouput path and disk-ready dataset

    Parameters
    ----------
    variable_name
        Variable to write in the dataset

    time_encoding
        Encoding to use with the time axis

        If not supplied, we use basic defaults.

    cv_source
        Source for the CVs.

    root_data_dir
        Root data directory to use when generating the output path.

    Returns
    -------
    :
        Valid output path and disk-ready dataset
    """
    ds, metadata_minimum = get_valid_ds_min_metadata_example(variable_id=variable_name)

    if time_encoding is None:
        time_encoding = {
            "calendar": "proleptic_gregorian",
            "units": "days since 1850-01-01 00:00:00",
            # Time has to be encoded as float
            # to ensure that half-days etc. are handled.
            "dtype": np.dtypes.Float32DType,
        }

    ds["time"].encoding = time_encoding

    if isinstance(cv_source, Input4MIPsCVs):
        cvs = cv_source
    else:
        cvs = load_cvs(cv_source)

    input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
        data=ds,
        metadata_minimum=metadata_minimum,
        cvs=cvs,
        prepare_func=partial(
            prepare_ds_and_get_frequency,
            standard_and_or_long_names={
                variable_name: {"standard_name": variable_name}
            },
        ),
    )

    out_path, valid_disk_ready_ds = input4mips_ds.get_out_path_and_disk_ready_dataset(
        root_data_dir=root_data_dir
    )

    return out_path, valid_disk_ready_ds


def create_files_in_tree(  # noqa: PLR0913
    variable_ids: Collection[str],
    units: Collection[str],
    fixed_fields: Collection[bool],
    tree_root: Path,
    cvs: Input4MIPsCVs,
    dataset_category: Optional[str] = None,
) -> list[Path]:
    """
    Create test files in a tree

    Parameters
    ----------
    variable_ids
        Variable IDs to write in the created files

    units
        Units to use in/assign to the created files

    fixed_fields
        Should the created files be fixed field files?

        For example, cell area files.

    tree_root
        Root of the tree in which to write the files

    cvs
        CVs to use when writing the files

    dataset_category
        Dataset category to apply to the created files

    Returns
    -------
    :
        List of created files
    """
    if len(variable_ids) != len(units):
        raise AssertionError

    if len(variable_ids) != len(fixed_fields):
        raise AssertionError

    written_files = []
    for variable_id, units, fixed_field in zip(variable_ids, units, fixed_fields):
        ds, metadata_minimum = get_valid_ds_min_metadata_example(
            variable_id=variable_id, units=units, fixed_field=fixed_field
        )
        if "time" in ds:
            ds["time"].encoding = {
                "calendar": "proleptic_gregorian",
                "units": "days since 1850-01-01 00:00:00",
                # Ensure half-days are encoded correctly
                "dtype": np.dtypes.Float32DType,
            }

        input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
            data=ds,
            metadata_minimum=metadata_minimum,
            cvs=cvs,
            prepare_func=partial(
                prepare_ds_and_get_frequency,
                standard_and_or_long_names={
                    variable_id: {"standard_name": variable_id}
                },
            ),
            dataset_category=dataset_category,
        )

        written_file = input4mips_ds.write(root_data_dir=tree_root)

        written_files.append(written_file)

    return written_files


def create_files_in_tree_return_info(
    tree_root: Path, **kwargs: Any
) -> dict[str, dict[str, str]]:
    """
    Create files in tree, returning information about them useful for testing

    Parameters
    ----------
    tree_root
        Root of the tree in which to write the files

    **kwargs
        Passed to
        [`create_files_in_tree`][input4mips_validation.testing.create_files_in_tree]

    Returns
    -------
    :
        Information about the files useful for testing
    """
    written_files = create_files_in_tree(tree_root=tree_root, **kwargs)
    info = {}
    for written_file in written_files:
        ds = xr.open_dataset(written_file, decode_cf=False)

        variable_id = ds.attrs["variable_id"]
        info[variable_id] = {k: ds.attrs[k] for k in ["creation_date", "tracking_id"]}
        info[variable_id]["sha256"] = get_file_hash_sha256(written_file)
        info[variable_id]["filepath"] = str(written_file)
        info[variable_id]["esgf_dataset_master_id"] = str(
            written_file.relative_to(tree_root).parent
        ).replace(os.sep, ".")

    return info
