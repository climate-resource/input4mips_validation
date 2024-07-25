"""
Dataset class definition
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import Any, Optional, Protocol

import cf_xarray  # noqa: F401
import cftime
import numpy as np
import xarray as xr
from attrs import asdict, field, fields, frozen
from loguru import logger

import input4mips_validation.xarray_helpers as iv_xr_helpers
from input4mips_validation.cvs import Input4MIPsCVs, load_cvs
from input4mips_validation.dataset.metadata import Input4MIPsDatasetMetadata
from input4mips_validation.dataset.metadata_data_producer_minimum import (
    Input4MIPsDatasetMetadataDataProducerMinimum,
)
from input4mips_validation.dataset.metadata_data_producer_multiple_variable_minimum import (  # noqa: E501
    Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum,
)
from input4mips_validation.inference.from_data import (
    VARIABLE_DATASET_CATEGORY_MAP,
    VARIABLE_REALM_MAP,
    infer_frequency,
)
from input4mips_validation.io import (
    generate_creation_timestamp,
    generate_tracking_id,
    write_ds_to_disk,
)
from input4mips_validation.xarray_helpers.time import xr_time_min_max_to_single_value


class AddTimeBoundsLike(Protocol):
    """A callable that is suitable for use when adding time bounds"""

    def __call__(
        self, ds: xr.Dataset, *args: Any, output_dim_bounds: str, **kwargs: Any
    ) -> xr.Dataset:
        """
        Add time-bounds to `ds`
        """


@frozen
class Input4MIPsDataset:
    """
    Representation of an input4MIPs dataset

    For validation, see
    [TODO: `validate_input4mips_ds` function and then cross-ref here].
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

    non_input4mips_metadata: Optional[dict[str, str]] = None
    """
    Metadata that isn't part of input4MIPs' data model

    This will simply be written as attributes to the file,
    as long as it doesn't clash with any of the input4MIPs keys.
    """
    # TODO: add check that there are no clashes with other metadata

    @cvs.default
    def _load_default_cvs(self) -> Input4MIPsCVs:
        return load_cvs()

    @classmethod
    def from_ds(
        cls,
        ds: xr.Dataset,
        cvs: Input4MIPsCVs | None,
    ) -> Input4MIPsDataset:
        """
        Initialise from an existing dataset

        Parameters
        ----------
        ds
            Dataset from which to initialise.

            We infer the metdata from `ds.attrs`.

        cvs
            Controlled vocabularies to use with the dataset

        Returns
        -------
            Initialised instance
        """
        ds_stripped = ds.copy()
        ds_stripped.attrs = {}

        metadata_fields = [
            f.name for f in fields(Input4MIPsDatasetMetadata) if f.name in ds.attrs
        ]
        metadata = Input4MIPsDatasetMetadata(
            **{k: ds.attrs[k] for k in metadata_fields}
        )
        non_input4mips_metadata = {
            k: v for k, v in ds.attrs.items() if k not in metadata_fields
        }

        init_kwargs = dict(
            data=ds_stripped,
            metadata=metadata,
            non_input4mips_metadata=non_input4mips_metadata,
        )
        if cvs is not None:
            init_kwargs["cvs"] = cvs

        res = Input4MIPsDataset(**init_kwargs)

        return res

    @classmethod
    def from_data_producer_minimum_information(  # noqa: PLR0913
        cls,
        data: xr.Dataset,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMinimum,
        dimensions: tuple[str, ...] | None = None,
        time_dimension: str = "time",
        add_time_bounds: AddTimeBoundsLike | None = None,
        copy_ds: bool = True,
        cvs: Input4MIPsCVs | None = None,
        activity_id: str = "input4MIPs",
        standard_and_or_long_names: dict[str, dict[str, str]] | None = None,
        dataset_category: str | None = None,
        realm: str | None = None,
    ) -> Input4MIPsDataset:
        """
        Initialise from the minimum information required from the data producer

        This applies to dataset's that have a single variable.
        For multi-variable datasets, see
        [`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable].

        Parameters
        ----------
        data
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
            we use
            [`add_time_bounds`][input4mips_validation.xarray_helpers.add_time_bounds].

        copy_ds
            Should `ds` be copied before we create the `Input4MIPsDataset`?

        cvs
            CVs to use for inference and validation

            If not supplied, this will be retrieved with
            [`load_cvs`][input4mips_validation.cvs.loading.load_cvs]

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

        dataset_category
            The category of the data.

            If not supplied, we will try and infer this based on
            [`VARIABLE_DATASET_CATEGORY_MAP`][input4mips_validation.inference.from_data.VARIABLE_DATASET_CATEGORY_MAP].

        realm
            The realm of the data.

            If not supplied, we will try and infer this based on
            [`VARIABLE_REALM_MAP`][input4mips_validation.inference.from_data.VARIABLE_REALM_MAP].

        Returns
        -------
            Initialised instance
        """
        if dimensions is None:
            dimensions_use: tuple[str, ...] = tuple(str(v) for v in data.dims)
        else:
            dimensions_use = dimensions

        if add_time_bounds is None:
            # Can't make mypy behave, hence type ignore
            add_time_bounds_use: AddTimeBoundsLike = iv_xr_helpers.add_time_bounds  # type: ignore
        else:
            add_time_bounds_use = add_time_bounds

        if cvs is None:
            cvs = load_cvs()

        # Add bounds to dimensions.
        # It feels like there should be a better way to do this.
        bounds_dim = "bounds"
        for dim in dimensions_use:
            if dim == time_dimension:
                data = add_time_bounds_use(data, output_dim_bounds=bounds_dim)
            else:
                data = data.cf.add_bounds(dim, output_dim=bounds_dim)

        # Get whatever other metadata information we can for free from cf-xarray.
        # TODO: check if any of this conflicts with CF-conventions,
        # given that naming of bounds seems to be wrong.
        data = data.cf.guess_coord_axis().cf.add_canonical_attributes()

        data = handle_ds_standard_long_names(
            data,
            standard_and_or_long_names=standard_and_or_long_names,
            bounds_dim=bounds_dim,
            # No need to copy here as that is already handled on entry
            copy_ds=False,
        )

        cvs_source_id_entry = cvs.source_id_entries[metadata_minimum.source_id]
        cvs_values = cvs_source_id_entry.values
        if cvs_values.license_id is None:
            msg = "License ID must be specified in the CVs source ID"
            raise AssertionError(msg)

        variable_id = get_ds_var_assert_single(data)

        # cf-xarray uses suffix bounds, hence hard-code this
        frequency = infer_frequency(data, time_bounds=f"{time_dimension}_bounds")

        if dataset_category is None:
            dataset_category = VARIABLE_DATASET_CATEGORY_MAP[variable_id]

        if realm is None:
            realm = VARIABLE_REALM_MAP[variable_id]

        metadata = Input4MIPsDatasetMetadata(
            activity_id=activity_id,
            contact=cvs_values.contact,
            dataset_category=dataset_category,
            frequency=frequency,
            further_info_url=cvs_values.further_info_url,
            grid_label=metadata_minimum.grid_label,
            # # TODO: look this up from central CVs
            # institution=cvs_values.institution,
            institution_id=cvs_values.institution_id,
            license=cvs.license_entries[cvs_values.license_id].values.conditions,
            license_id=cvs_values.license_id,
            mip_era=cvs_values.mip_era,
            nominal_resolution=metadata_minimum.nominal_resolution,
            realm=realm,
            source_id=metadata_minimum.source_id,
            source_version=cvs_values.source_version,
            target_mip=metadata_minimum.target_mip,
            variable_id=variable_id,
        )

        # Make sure time appears first as this is what CF conventions expect
        return cls(data=data.transpose(time_dimension, ...), metadata=metadata, cvs=cvs)

    @classmethod
    def from_data_producer_minimum_information_multiple_variable(  # noqa: PLR0913
        cls,
        data: xr.Dataset,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum,
        dimensions: tuple[str, ...] | None = None,
        time_dimension: str = "time",
        add_time_bounds: AddTimeBoundsLike | None = None,
        copy_ds: bool = True,
        cvs: Input4MIPsCVs | None = None,
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
        data
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
            we use
            [`add_time_bounds`][input4mips_validation.xarray_helpers.add_time_bounds].

        copy_ds
            Should `ds` be copied before we create the `Input4MIPsDataset`?

        cvs
            CVs to use for inference and validation

            If not supplied, this will be retrieved with
            [`load_cvs`][input4mips_validation.cvs.loading.load_cvs].

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
            Initialised instance
        """
        if dimensions is None:
            dimensions_use: tuple[str, ...] = tuple(str(v) for v in data.dims)
        else:
            dimensions_use = dimensions

        if add_time_bounds is None:
            # Can't make mypy behave, hence type ignore
            add_time_bounds_use: AddTimeBoundsLike = iv_xr_helpers.add_time_bounds  # type: ignore
        else:
            add_time_bounds_use = add_time_bounds

        if cvs is None:
            cvs = load_cvs()

        # Add bounds to dimensions.
        # It feels like there should be a better way to do this.
        bounds_dim = "bounds"
        for dim in dimensions_use:
            if dim == time_dimension:
                data = add_time_bounds_use(data, output_dim_bounds=bounds_dim)
            else:
                data = data.cf.add_bounds(dim, output_dim=bounds_dim)

        # Get whatever other metadata information we can for free from cf-xarray.
        # TODO: check if any of this conflicts with CF-conventions,
        # given that naming of bounds seems to be wrong.
        data = data.cf.guess_coord_axis().cf.add_canonical_attributes()

        data = handle_ds_standard_long_names(
            data,
            standard_and_or_long_names=standard_and_or_long_names,
            bounds_dim=bounds_dim,
            # No need to copy here as that is already handled on entry
            copy_ds=False,
        )

        cvs_source_id_entry = cvs.source_id_entries[metadata_minimum.source_id]
        cvs_values = cvs_source_id_entry.values
        if cvs_values.license_id is None:
            msg = "License ID must be specified in the CVs source ID"
            raise AssertionError(msg)

        # cf-xarray uses suffix bounds, hence hard-code this
        frequency = infer_frequency(data, time_bounds=f"{time_dimension}_bounds")

        metadata = Input4MIPsDatasetMetadata(
            activity_id=activity_id,
            contact=cvs_values.contact,
            dataset_category=metadata_minimum.dataset_category,
            frequency=frequency,
            further_info_url=cvs_values.further_info_url,
            grid_label=metadata_minimum.grid_label,
            # # TODO: look this up from central CVs
            # institution=cvs_values.institution,
            institution_id=cvs_values.institution_id,
            license=cvs.license_entries[cvs_values.license_id].values.conditions,
            license_id=cvs_values.license_id,
            mip_era=cvs_values.mip_era,
            nominal_resolution=metadata_minimum.nominal_resolution,
            realm=metadata_minimum.realm,
            source_id=metadata_minimum.source_id,
            source_version=cvs_values.source_version,
            target_mip=metadata_minimum.target_mip,
            variable_id=variable_id,
        )

        # Make sure time appears first as this is what CF conventions expect
        return cls(data=data.transpose(time_dimension, ...), metadata=metadata, cvs=cvs)

    def write(  # noqa: PLR0913
        self,
        root_data_dir: Path,
        pint_dequantify_format: str = "cf",
        unlimited_dimensions: tuple[str, ...] = ("time",),
        encoding_kwargs: dict[str, Any] | None = None,
        frequency_metadata_key: str = "frequency",
        no_time_axis_frequency: str = "fx",
        time_dimension: str = "time",
    ) -> Path:
        """
        Write to disk

        Parameters
        ----------
        root_data_dir
            Root directory in which to write the file

        pint_dequantify_format
            Format to use when dequantifying variables with Pint.

            It is unlikely that you will want to change this.

        unlimited_dimensions
            Dimensions which should be unlimited in the written file

            This is passed to [iris.save][].

        encoding_kwargs
            Kwargs to use when encoding to disk.

            These are passed as arguments to
            [`write_ds_to_disk`][input4mips_validation.io.write_ds_to_disk].

        frequency_metadata_key
            The key in the data's metadata
            which points to information about the data's frequency.

        no_time_axis_frequency
            The value of "frequency" in the metadata which indicates
            that the file has no time axis i.e. is fixed in time.

        time_dimension
            The time dimension of the data.

            Required so that we know
            what information to pass to the path generating algorithm,
            in case the path generating algorithm requires time axis information.

        Returns
        -------
            Path in which the file was written
        """
        cvs = self.cvs

        # Can shallow copy as we don't alter the data from here on
        ds_disk = self.data.copy(deep=False)
        try:
            ds_disk = ds_disk.pint.dequantify(format=pint_dequantify_format)
        except AttributeError:
            logger.debug(
                "Not dequantifying with pint, "
                "I assume you know what you're doing with units"
            )

        # Add all the metadata
        if self.non_input4mips_metadata is not None:
            # Merge the metadata.
            # Validation ensures that there will be no clash of keys.
            ds_disk.attrs = (
                self.non_input4mips_metadata
                | convert_input4mips_metadata_to_ds_attrs(self.metadata)
            )

        else:
            ds_disk.attrs = convert_input4mips_metadata_to_ds_attrs(self.metadata)

        # Must be unique for every written file,
        # so we deliberately don't provide a way
        # for the user to overwrite this at present
        # and overwrite any existing values.
        ds_disk.attrs["tracking_id"] = generate_tracking_id()
        ds_disk.attrs["creation_date"] = generate_creation_timestamp()

        if ds_disk.attrs[frequency_metadata_key] != no_time_axis_frequency:
            time_start: cftime.datetime | dt.datetime | np.datetime64 | None = (
                xr_time_min_max_to_single_value(ds_disk[time_dimension].min())
            )
            time_end: cftime.datetime | dt.datetime | np.datetime64 | None = (
                xr_time_min_max_to_single_value(ds_disk[time_dimension].max())
            )
        else:
            time_start = time_end = None

        out_path = cvs.DRS.get_file_path(
            root_data_dir=root_data_dir,
            available_attributes=ds_disk.attrs,
            time_start=time_start,
            time_end=time_end,
        )

        written_path = write_ds_to_disk(
            ds=ds_disk,
            out_path=out_path,
            cvs=cvs,
            unlimited_dimensions=unlimited_dimensions,
            **(encoding_kwargs if encoding_kwargs else {}),
        )

        return written_path


def handle_ds_standard_long_names(
    ds: xr.Dataset,
    standard_and_or_long_names: dict[str, dict[str, str]] | None,
    bounds_dim: str,
    copy_ds: bool = False,
) -> xr.Dataset:
    """
    Handle setting and checking of the data variables' name information

    This means setting standard_name and/or long_name information.

    Parameters
    ----------
    ds
        Dataset on which to set the metadata

    standard_and_or_long_names
        Standard/long names to use for the variables in `ds`.

        E.g.
        `standard_and_or_long_names = {"variable_name": {"standard_name": "flux"}}`

        If not provided, then this function just checks metadata but won't set it.

    bounds_dim
        String which indicates that the variable is a bounds variable.
        These variables don't need standard/long name information.

    copy_ds
        Should we copy `ds` before modifying the metadata?

    Returns
    -------
        `ds` with standard and/or long name metadata set.

    Raises
    ------
    ValueError
        `ds` is missing standard/long name variable information
        for a variable and `standard_and_or_long_names` is not provided.

        Standard/long name information is missing for a variable in `ds`,
        even after applying the information in `standard_and_or_long_names`.

    KeyError
        No standard or long name information for a variable is provided.
    """
    if copy_ds:
        ds = ds.copy()

    for ds_variable in [*ds.data_vars, *ds.coords]:
        if bounds_dim in ds_variable:
            continue

        if not any(k in ds[ds_variable].attrs for k in ["standard_name", "long_name"]):
            # Ensure these key IDs are there
            if standard_and_or_long_names is None:
                msg = (
                    f"Variable {ds_variable} "
                    "does not have either standard_name or long_name set. "
                    "Hence you must supply `standard_and_or_long_names`."
                )
                raise ValueError(msg)

            try:
                var_info = standard_and_or_long_names[ds_variable]
            except KeyError as exc:
                msg = f"Standard or long name for {ds_variable} must be supplied"
                raise KeyError(msg) from exc

            if "standard_name" in var_info:
                ds[ds_variable].attrs["standard_name"] = var_info["standard_name"]

            if "long_name" in var_info:
                ds[ds_variable].attrs["long_name"] = var_info["long_name"]

            if (
                "standard_name" not in ds[ds_variable].attrs
                and "long_name" not in ds[ds_variable].attrs
            ):
                msg = (
                    "One of standard_name and long_name "
                    "must be in ds[ds_variable].attrs. "
                    f"Received {ds[ds_variable].attrs=}"
                )
                raise ValueError(msg)

    return ds


def get_ds_var_assert_single(ds: xr.Dataset) -> str:
    """
    Get a [xarray.Dataset][]'s variable, asserting that there is only one

    Parameters
    ----------
    ds
        Data from which to retrieve the variable

    Returns
    -------
        Variable
    """
    ds_var_l: list[str] = list(ds.data_vars)
    if len(ds_var_l) != 1:
        msg = f"`ds` must only have one variable. Received: {ds_var_l!r}"
        raise AssertionError(msg)

    return ds_var_l[0]


def convert_input4mips_metadata_to_ds_attrs(
    metadata: Input4MIPsDatasetMetadata,
) -> dict[str, str]:
    """
    Convert [Input4MIPsDatasetMetadata][input4mips_validation.dataset.metadata.Input4MIPsDatasetMetadata] to [xarray.Dataset.attrs][] compatible values

    Returns
    -------
        [xarray.Dataset.attrs][] compatible values
    """  # noqa: E501
    res = {k: v for k, v in asdict(metadata).items() if v is not None}

    # Put back in if/when we add non CVs metadata handling back in
    # if self.metadata_non_cvs is not None:
    #     # Add other keys in too
    #     res = self.metadata_non_cvs | res

    return res
