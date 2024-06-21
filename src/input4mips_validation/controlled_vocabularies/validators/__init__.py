"""
Validation related to controlled vocabularies
"""
from __future__ import annotations

from functools import partial
from typing import Any, Callable, TypeVar

import xarray as xr
from typing_extensions import TypeAlias

from input4mips_validation.controlled_vocabularies.validators.comparison_with_cvs import (  # noqa: E501
    assert_value_matches_controlled_vocabulary,
)
from input4mips_validation.controlled_vocabularies.validators.ds_metadata_consistency import (  # noqa: E501
    assert_dataset_category_matches_ds,
    assert_metadata_value_matches_ds_variable,
)
from input4mips_validation.controlled_vocabularies.validators.email import (
    assert_includes_email,
)

T = TypeVar("T")

MetadataValidator: TypeAlias = Callable[[T], None]
MetadataValidators: TypeAlias = dict[str, MetadataValidator[Any]]

DS_METADATA_VALIDATORS: MetadataValidators = {
    "contact": assert_includes_email,
    **{
        k: partial(assert_value_matches_controlled_vocabulary, key=k)
        for k in [
            # Uncomment once we work out how to handle the CVs properly
            # "dataset_category",
            # uncomment once I work out what source of truth should be
            # (currently not clear what comes from where and institution id
            # is not in input4MIPs_CVs)
            # "institution_id",
            # "variable_id",  # Also has CV I presume...
        ]
    },
    # Further validators can be added here (or above) as we work them out
}
"""
Validators used to check the a data set's metdata

Note: All compulsory metadata keys
which do not need to be consistent with the underlying data
will be included in this list.
The only exception to this is the creation date and the UUID
because they are added only at the time of writing the file.
"""


def validate_ds_metadata(
    dataset: xr.Dataset,
    validators: MetadataValidators | None = None,
) -> None:
    """
    Validate that the metadata in a :obj:`xr.Dataset` is valid

    This assumes the rules that apply to input4MIPs data.

    Parameters
    ----------
    dataset
        :obj:`xr.Dataset` to check

    validators
        Validators to use for the checks.
        If not supplied, we use :const:`DS_METADATA_VALIDATORS`.

    Raises
    ------
    ValueError
        If there is a problem validating one of the metadata keys.
    """
    # TODO: test this properly
    if validators is None:
        validators = DS_METADATA_VALIDATORS

    for metadata_key, validator in validators.items():
        try:
            validator(dataset.attrs[metadata_key])
        except Exception as exc:
            # Could do something much more fancy here,
            # can update as we start to see use cases
            raise ValueError(metadata_key) from exc


DatasetMetadataConsistencyValidator: TypeAlias = Callable[[xr.Dataset, str], None]
DatasetMetadataConsistencyValidators: TypeAlias = dict[
    str, DatasetMetadataConsistencyValidator
]

DS_METADATA_CONSISTENCY_VALIDATORS: DatasetMetadataConsistencyValidators = {
    "variable_id": assert_metadata_value_matches_ds_variable,
    "dataset_category": assert_dataset_category_matches_ds,
    # Further validators can be added here as we work them out
}
"""
Validators used to check the consistency between the dataset and its metadata

Note: All compulsory metadata keys which need to be consistent
with the underlying data will be included in this list.
"""


def validate_ds_metadata_consistency(
    dataset: xr.Dataset,
    validators: DatasetMetadataConsistencyValidators | None = None,
) -> None:
    """
    Validate that the data in a :obj:`xr.Dataset` is consistent with its metadata

    This assumes the rules that apply to input4MIPs data.

    Parameters
    ----------
    dataset
        :obj:`xr.Dataset` to check

    validators
        Validators to use for the checks.
        If not supplied, we use :const:`DS_METADATA_CONSISTENCY_VALIDATORS`.

    Raises
    ------
    ValueError
        If there is a problem validating one of the metadata keys.
    """
    # TODO: test this properly
    if validators is None:
        validators = DS_METADATA_CONSISTENCY_VALIDATORS

    for metadata_key, validator in validators.items():
        try:
            validator(dataset, metadata_key)
        except Exception as exc:
            # Could do something much more fancy here,
            # can update as we start to see use cases
            raise ValueError(metadata_key) from exc
