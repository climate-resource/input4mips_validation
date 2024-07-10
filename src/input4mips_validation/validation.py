"""
Validation of data
"""

from __future__ import annotations

from pathlib import Path

import iris
import xarray as xr
from attrs import fields

from input4mips_validation.dataset import Input4MIPsDatasetMetadataEntry


def validate_file(infile: Path | str) -> Input4MIPsDatasetMetadataEntry:
    # TODO: wrap things in try catch so we can report errors well

    ds = xr.load_dataset(infile)

    # Check we can create metadata from file
    dataset_entry_keys = [v.name for v in fields(Input4MIPsDatasetMetadataEntry)]
    dataset_entry = Input4MIPsDatasetMetadataEntry(
        **{k: v for k, v in ds.attrs.items() if k in dataset_entry_keys}
    )

    # TODO: call validate_dataset_metadata_entry here

    # Make sure we can load with iris too
    iris.load_cube(infile)

    return dataset_entry
