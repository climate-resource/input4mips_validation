"""
Classes that define an input4MIPs dataset and associated metadata
"""

from __future__ import annotations

from typing import Callable

import xarray as xr
from attrs import field, frozen

import input4mips_validation.xarray_helpers as iv_xr_helpers
from input4mips_validation.database import make_class_from_database_entry_file_fields

DATASET_PRODUCER_MINIMUM_FIELDS = (
    "grid_label",
    "nominal_resolution",
    "product",
    "region",
    "source_id",
    "target_mip",
)

Input4MIPsDatasetMetadataDataProducerMinimum = (
    make_class_from_database_entry_file_fields(
        "Input4MIPsDatasetMetadataDataProducerMinimum",
        DATASET_PRODUCER_MINIMUM_FIELDS,
    )
)
"""
Minimum metadata from input4MIPs dataset producer

This is the minimum metadata required to create a valid
[`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
[`from_data_producer_minimum_information`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information].

For an explanation of the required fields,
see [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
"""
# Adding docstrings like this is a hack while this issue is ongoing:
# https://github.com/python-attrs/attrs/issues/1309

# multi-variable minimum

DATASET_PRODUCER_MULTI_VARIABLE_MINIMUM_FIELDS = (
    *DATASET_PRODUCER_MINIMUM_FIELDS,
    "dataset_category",
    "realm",
)

Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum = (
    make_class_from_database_entry_file_fields(
        "Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum",
        DATASET_PRODUCER_MULTI_VARIABLE_MINIMUM_FIELDS,
    )
)
"""
Minimum metadata from input4MIPs dataset producer for a multi-variable file

This is the minimum metadata required to create a valid
[`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
[`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable].

For an explanation of the required fields,
see [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
"""
# Adding docstrings like this is a hack while this issue is ongoing:
# https://github.com/python-attrs/attrs/issues/1309

DATASET_METADATA_FIELDS = (
    # "activity_id",
    # "contact",
    # "dataset_category",
    # "frequency",
    # "further_info_url",
    "grid_label",
    # "institution",
    # "institution_id",
    # "license",
    # "license_id",
    # "mip_era",
    # "nominal_resolution",
    # "product",
    # "realm",
    # "region",
    # "source",
    # "source_id",
    # "source_version",
    # "target_mip",
    # "variable_id",
)
Input4MIPsDatasetMetadata = make_class_from_database_entry_file_fields(
    "Input4MIPsDatasetMetadata",
    DATASET_METADATA_FIELDS,
)
"""
Metadata for an input4MIPs dataset

For an explanation of the fields,
see [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
"""
# Adding docstrings like this is a hack while this issue is ongoing:
# https://github.com/python-attrs/attrs/issues/1309

# CV handling
# - can also pull those tests back in


@frozen
class Input4MIPsDataset:
    """
    Representation of an input4MIPs dataset

    For validation, see [`validate_ds`][input4mips_validation.validation.validate_input4mips_ds].
    TODO: check cross-reference once we switch to mkdocs,
    help here I think https://pypi.org/project/mkdocstrings/0.9.0/
    maybe also here https://mkdocstrings.github.io/usage/
    """

    data: xr.Dataset
    """
    Data
    """

    metadata: Input4MIPsDatasetMetadata
    """
    Metadata
    """

    cvs: Input4MIPsCVs = field()
    """
    Controlled vocabularies to use with this dataset

    If not supplied, we create these with
    [`load_cvs`][input4mips_validation.cvs.loading.load_cvs]
    """

    @cvs.default
    def _load_default_cvs(self) -> Input4MIPsCVs:
        return load_cvs()

    @classmethod
    def from_data_producer_minimum_information(  # noqa: PLR0913
        cls,
        ds: xr.Dataset,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMinimum,
        dimensions: tuple[str, ...] | None = None,
        time_dimension: str = "time",
        # Make this an argument of write or an attribute of self
        # metadata_non_cvs: dict[str, Any] | None = None,
        add_time_bounds: Callable[[xr.Dataset], xr.Dataset] | None = None,
        copy_ds: bool = True,
        cvs: CVsInput4MIPs | None = None,
        activity_id: str = "input4MIPs",
        standard_and_or_long_names: dict[str, dict[str, str]] | None = None,
    ) -> Input4MIPsDataset:
        """
        Initialise from the minimum information required from the data producer

        This applies to dataset's that have a single variable.
        For multi-variable datasets, see
        [`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable].

        Parameters
        ----------
        ds
            Raw data

        metadata_minimum
            Minimum metadata required from the data producer

        dimensions
            Dimensions of the dataset, other than the time dimension.
            These are checked for appropriate bounds.
            Bounds are added if they are not present.

            If not supplied, we simply use all the dimensions of ``ds``
            in the order they appear in the dataset.

        time_dimension
            Time dimension of the dataset.
            This is singled out because handling time bounds is often a special case.

        add_time_bounds
            Function that adds bounds to the time variable.
            If not supplied,
            we use [`add_time_bounds`][input4mips_validation.xarray_helpers.add_time_bounds].

        copy_ds
            Should `ds` be copied before we create the `Input4MIPsDataset`?

        cvs
            CVs to use for inference and validation

            If not supplied, this will be retrieved with
            [`load_cvs`][input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs].

        activity_id
            Activity ID that applies to the dataset.

            Given this is an Input4MIPsDataset, you shouldn't need to change this.

        standard_and_or_long_names
            Standard/long names to use for the variables in `ds`.

            All variables that are not bounds
            must have attributes that contain a value for at least one of
            `standard_name` and `long_name`.
            Hence this argument is only required
            if the attributes of the variable do not already have these values.

            Each key should be a variable in `ds`.
            The value of `standard_and_or_long_name`
            should itself be a dictionary with keys
            `"standard_name"` for the variable's standard name
            and/or `"long_name"` for the variable's long name.

            E.g.
            `standard_and_or_long_names = {"variable_name": {"standard_name": "flux"}}`

        Returns
        -------
            Initialised `Input4MIPsDataset` instance
        """
        if dimensions is None:
            dimensions: tuple[str, ...] = tuple(ds.dims)

        if add_time_bounds is None:
            add_time_bounds = iv_xr_helpers.add_time_bounds

        if cvs is None:
            cvs = load_cvs()

        raise NotImplementedError()

    @classmethod
    def from_data_producer_minimum_information_multiple_variable(  # noqa: PLR0913
        cls,
        ds: xr.Dataset,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum,
        dimensions: tuple[str, ...] | None = None,
        time_dimension: str = "time",
        # Make this an argument of write or an attribute of self
        # metadata_non_cvs: dict[str, Any] | None = None,
        add_time_bounds: Callable[[xr.Dataset], xr.Dataset] | None = None,
        copy_ds: bool = True,
        cvs: CVsInput4MIPs | None = None,
        activity_id: str = "input4MIPs",
        standard_and_or_long_names: dict[str, dict[str, str]] | None = None,
        variable_id: str = "multiple",
    ) -> Input4MIPsDataset:
        """
        Initialise from the minimum information required from the data producer

        This applies to dataset's that have multiple variables.
        For single variable datasets, see
        [`from_data_producer_minimum_information`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information].

        Parameters
        ----------
        ds
            Raw data

        metadata_minimum
            Minimum metadata required from the data producer

        dimensions
            Dimensions of the dataset, other than the time dimension.
            These are checked for appropriate bounds.
            Bounds are added if they are not present.

            If not supplied, we simply use all the dimensions of ``ds``
            in the order they appear in the dataset.

        time_dimension
            Time dimension of the dataset.
            This is singled out because handling time bounds is often a special case.

        add_time_bounds
            Function that adds bounds to the time variable.
            If not supplied,
            we use [`add_time_bounds`][input4mips_validation.xarray_helpers.add_time_bounds].

        copy_ds
            Should `ds` be copied before we create the `Input4MIPsDataset`?

        cvs
            CVs to use for inference and validation

            If not supplied, this will be retrieved with
            [`load_cvs`][input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs].

        activity_id
            Activity ID that applies to the dataset.

            Given this is an Input4MIPsDataset, you shouldn't need to change this.

        standard_and_or_long_names
            Standard/long names to use for the variables in `ds`.

            All variables that are not bounds
            must have attributes that contain a value for at least one of
            `standard_name` and `long_name`.
            Hence this argument is only required
            if the attributes of the variable do not already have these values.

            Each key should be a variable in `ds`.
            The value of `standard_and_or_long_name`
            should itself be a dictionary with keys
            `"standard_name"` for the variable's standard name
            and/or `"long_name"` for the variable's long name.

            E.g.
            `standard_and_or_long_names = {"variable_name": {"standard_name": "flux"}}`

        variable_id
            The variable ID to use.

            For multi-variable datasets, as far as we are aware,
            this is always "multiple", hence you shouldn't need to change the defaults.

        Returns
        -------
            Initialised `Input4MIPsDataset` instance
        """
        raise NotImplementedError()
