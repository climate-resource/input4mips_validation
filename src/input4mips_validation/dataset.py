"""
Input4MIPs dataset model
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import xarray as xr
from attrs import define, field


@define
class Input4MIPsDatasetMetadata:
    """
    Metadata for an input4MIPs dataset
    """

    # Required fields as attributes
    # Then a field for everything else, e.g.
    non_cvs_metadata: dict[str, Any]
    # Validation, no clash with attributes of self


@define
class Input4MIPsDatasetMetadataDataProducerMinimum:
    """
    Minimum metadata required from an input4MIPs dataset producer
    """

    # Required fields as attributes


@define
class Input4MIPsDataset:
    """
    Representation of an input4MIPs dataset
    """

    ds: xr.Dataset = field(
        # validator=[
        #     make_attrs_validator_compatible_input_only(validate_ds),
        # ]
    )
    """
    Dataset
    """

    metadata: Input4MIPsDatasetMetadata = field(
        # make_attrs_validator_compatible_input_only(validate_ds_metadata),
        # make_attrs_validator_compatible_input_only(validate_ds_metadata_consistency),
    )
    """
    Metadata about the dataset
    """

    @classmethod
    def from_data_producer_minimum_information(  # noqa: PLR0913
        cls,
        ds: xr.Dataset,
        dimensions: tuple[str, ...],
        time_dimension: str,
        metadata: Input4MIPsDatasetMetadataDataProducerMinimum,
        metadata_optional: dict[str, Any] | None = None,
        add_time_bounds: Callable[[xr.Dataset], xr.Dataset] | None = None,
        copy: bool = True,
    ) -> Input4MIPsDataset:
        """
        Initialise from the minimum required information from the data producer

        Parameters
        ----------
        ds
            Raw dataset

        dimensions
            Dimensions of the dataset other than the time dimension,
            these are checked for appropriate bounds.
            Bounds are added if they are not present.

        time_dimension
            Time dimension of the dataset.
            This is singled out because handling time bounds is often a special case.

        metadata
            Metadata required from the data producer

        metadata_optional
            Any other metadata the data producer would like to provider

            This must not clash with any of our inferred metadata.

        add_time_bounds

        copy
            Callable to use to add time bounds.
            If not supplied, uses
            :func:`input4mips_validation.xarray_helpers.add_time_bounds`.

        Returns
        -------
            Initialised instance

        Raises
        ------
        AssertionError
            There is a clash between ``metadata_optional`` and the inferred metadata
        """
        # Only check on metadata_optional, no clash with
        # keys we can infer/create
        ...

    def write(
        self,
        root_data_dir: Path,
        unlimited_dims: tuple[str, ...] = ("time",),
        encoding_kwargs: dict[str, Any] | None = None,
    ) -> Path:
        """
        Write to disk

        Parameters
        ----------
        root_data_dir
            Root directory in which to write the file

        unlimited_dims
            Dimensions which should be unlimited in the written file

        encoding_kwargs
            Kwargs to use when encoding to disk.
            These are passed to :meth:`xr.Dataset.to_netcdf`.
            If not supplied, we use :const:`DEFAULT_ENCODING_KWARGS`

        Returns
        -------
            Path in which the file was written
        """
        ...
