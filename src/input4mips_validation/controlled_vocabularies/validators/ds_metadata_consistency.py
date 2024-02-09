"""
Checks of consistency between datasets and their metadata
"""
from __future__ import annotations

import xarray as xr

from input4mips_validation.controlled_vocabularies.constants import VARIABLE_DATASET_MAP
from input4mips_validation.xarray_helpers import get_ds_variable


def assert_metadata_value_matches_ds_variable(dataset: xr.Dataset, key: str) -> None:
    """
    Assert that the metadata value matches the dataset's variable name

    Parameters
    ----------
    dataset
        Dataset to check

    key
        Metadata key to check is consistent with the variable in the dataset

    Raises
    ------
    AssertionError
        There is more than one variable in the dataset
        or the variable is inconsistent with ``key``'s value in the metadata.
    """
    metadata_value = dataset.attrs[key]
    variable = get_ds_variable(dataset)
    if metadata_value != variable:
        msg = (
            f"{key} is inconsistent with the dataset's variable. "
            f"{metadata_value=}. {variable=}"
        )
        raise AssertionError(msg)


def assert_dataset_category_matches_ds(dataset: xr.dataset, key: str) -> None:
    """
    Assert that the dataset_category metadata matches the dataset

    Parameters
    ----------
    dataset
        Dataset to check

    key
        Metadata key to check.
        At the moment, this has to be "dataset_category"
        but we take it as input for consistency with other validators.

    Raises
    ------
    AssertionError
        The dataset_category metadata and the variable are inconsistent.
        Also raises if a key other than "dataset_category" is provided.
    """
    if key != "dataset_category":
        msg = "I was only built to check dataset_category"
        raise AssertionError(msg)

    dataset_category = dataset.attrs["dataset_category"]

    variable = get_ds_variable(dataset)

    exp_dataset_category = VARIABLE_DATASET_MAP[variable]

    if dataset_category != exp_dataset_category:
        msg = (
            f"{key} is inconsistent with the dataset's variable. "
            f"For {variable=}, we expect that dataset_category={exp_dataset_category}, "
            f"but we received {dataset_category=}"
        )
        raise AssertionError(msg)
