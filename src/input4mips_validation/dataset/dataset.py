"""
Dataset class definition
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Optional, Protocol

import attr
import cf_xarray  # noqa: F401
import cftime
import iris
import ncdata
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
)
from input4mips_validation.validation.datasets_to_write_to_disk import (
    get_ds_to_write_to_disk_validation_result,
)
from input4mips_validation.xarray_helpers.time import xr_time_min_max_to_single_value

CF_XARRAY_BOUNDS_SUFFIX: str = "_bounds"
"""
The suffix added by cf-xarray when adding bounds variables.

This is a global variable because this value is currently hard-coded in cf-xarray.
See https://github.com/xarray-contrib/cf-xarray/blob/22ee634433b988bd101e45e9f9728bbf59915259/cf_xarray/accessor.py#L2507.
"""


class PrepareFuncLike(Protocol):
    """
    A callable that is suitable for use when preparing data in the class methods below
    """

    def __call__(
        self,
        ds_raw: xr.Dataset,
        copy_ds: bool,
    ) -> tuple[xr.Dataset, str]:
        """
        Prepare data

        The function should ensure that:

        - all dimensions have bounds information
        - all variables have a "long_name" or "standard_name" attribute

        Parameters
        ----------
        ds_raw
            Raw data to prepare

        copy_ds
            Should we copy `ds_raw` before modifying the metadata
            or simply modify the existing dataset?

        Returns
        -------
        :
            Prepared data and inferred frequency metadata
        """


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

    non_input4mips_metadata: Optional[dict[str, str]] = field(default=None)
    """
    Metadata that isn't part of input4MIPs' data model
    This will simply be written as attributes to the file,
    as long as it doesn't clash with any of the input4MIPs keys.
    """

    @non_input4mips_metadata.validator
    def _no_clash_with_metadata_attributes(
        self, attribute: attr.Attribute[Any], value: dict[str, Any] | None
    ) -> None:
        if value is None:
            return

        clashing_keys = [key for key in value if key in asdict(self.metadata).keys()]
        if clashing_keys:
            msg = (
                f"{attribute.name} must not contain any keys "
                "that clash with the `self.metadata`. "
                f"Keys in both {attribute.name} and `self.metadata`: {clashing_keys}"
            )
            raise AssertionError(msg)

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

        if cvs is None:
            res = Input4MIPsDataset(
                data=ds_stripped,
                metadata=metadata,
                non_input4mips_metadata=non_input4mips_metadata,
            )

        else:
            res = Input4MIPsDataset(
                data=ds_stripped,
                metadata=metadata,
                non_input4mips_metadata=non_input4mips_metadata,
                cvs=cvs,
            )

        return res

    @classmethod
    def from_data_producer_minimum_information(  # noqa: PLR0913
        cls,
        data: xr.Dataset,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMinimum,
        cvs: Input4MIPsCVs | None = None,
        prepare_func: PrepareFuncLike | None = None,
        copy_ds: bool = True,
        activity_id: str = "input4MIPs",
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

        cvs
            CVs to use for inference and validation

            If not supplied, this will be retrieved with
            [`load_cvs`][input4mips_validation.cvs.load_cvs]

        prepare_func
            Function to use to prepare the data, retrieve source ID values from the CVs
            and infer the frequency metadata.

            If not supplied, we use
            [`input4mips_validation.dataset.dataset.prepare_ds_and_get_frequency`].

        copy_ds
            Should `ds` be copied before we create the `Input4MIPsDataset`?

        activity_id
            Activity ID that applies to the dataset.

            Given this is an Input4MIPsDataset, you shouldn't need to change this.

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
        :
            Initialised instance
        """
        variable_id = get_ds_var_assert_single(data)

        ### These lines are exactly the same as in
        # `from_data_producer_minimum_information_multiple_variable`.
        # This is on purpose, the extra layer of abstraction
        # and coupling isn't worth it right now.
        if cvs is None:
            cvs = load_cvs()

        if prepare_func is None:
            prepare_func_use: PrepareFuncLike = prepare_ds_and_get_frequency  # type: ignore # can't get mypy to behave
        else:
            prepare_func_use = prepare_func

        if copy_ds:
            data = data.copy()

        data, frequency = prepare_func_use(
            ds_raw=data,
            # Copying handled above
            copy_ds=False,
        )

        # [TODO: remove this once we are confident in our license checks]
        cvs_source_id_entry = cvs.source_id_entries[metadata_minimum.source_id]
        cvs_source_id_values = cvs_source_id_entry.values
        if cvs_source_id_values.license_id is None:
            msg = "License ID must be specified in the CVs source ID"
            raise AssertionError(msg)
        ### End of identical lines

        if dataset_category is None:
            dataset_category = VARIABLE_DATASET_CATEGORY_MAP[variable_id]

        if realm is None:
            realm = VARIABLE_REALM_MAP[variable_id]

        metadata = Input4MIPsDatasetMetadata(
            activity_id=activity_id,
            contact=cvs_source_id_values.contact,
            dataset_category=dataset_category,
            frequency=frequency,
            further_info_url=cvs_source_id_values.further_info_url,
            grid_label=metadata_minimum.grid_label,
            # # TODO: look this up from central CVs
            # institution=cvs_source_id_values.institution,
            institution_id=cvs_source_id_values.institution_id,
            license=cvs.license_entries[
                cvs_source_id_values.license_id
            ].values.conditions,
            license_id=cvs_source_id_values.license_id,
            mip_era=cvs_source_id_values.mip_era,
            nominal_resolution=metadata_minimum.nominal_resolution,
            realm=realm,
            source_id=metadata_minimum.source_id,
            source_version=cvs_source_id_values.source_version,
            target_mip=metadata_minimum.target_mip,
            variable_id=variable_id,
        )

        return cls(data=data, metadata=metadata, cvs=cvs)

    @classmethod
    def from_data_producer_minimum_information_multiple_variable(  # noqa: PLR0913
        cls,
        data: xr.Dataset,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum,
        cvs: Input4MIPsCVs | None = None,
        prepare_func: PrepareFuncLike | None = None,
        copy_ds: bool = True,
        activity_id: str = "input4MIPs",
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

        cvs
            CVs to use for inference and validation

            If not supplied, this will be retrieved with
            [`load_cvs`][input4mips_validation.cvs.loading.load_cvs].

        prepare_func
            Function to use to prepare the data, retrieve source ID values from the CVs
            and infer the frequency metadata.

            If not supplied, we use
            [`input4mips_validation.dataset.dataset.prepare_ds_and_get_frequency`].

        copy_ds
            Should `ds` be copied before we create the `Input4MIPsDataset`?

        activity_id
            Activity ID that applies to the dataset.

            Given this is an Input4MIPsDataset, you shouldn't need to change this.

        variable_id
            The variable ID to use.

            For multi-variable datasets, as far as we are aware,
            this is always "multiple", hence you shouldn't need to change the defaults.

        Returns
        -------
        :
            Initialised instance
        """
        ### These lines are exactly the same as in
        # `from_data_producer_minimum_information`.
        # This is on purpose, the extra layer of abstraction
        # and coupling isn't worth it right now.
        if cvs is None:
            cvs = load_cvs()

        if prepare_func is None:
            prepare_func_use: PrepareFuncLike = prepare_ds_and_get_frequency  # type: ignore # can't get mypy to behave
        else:
            prepare_func_use = prepare_func

        if copy_ds:
            data = data.copy()

        data, frequency = prepare_func_use(
            ds_raw=data,
            # Copying handled above
            copy_ds=False,
        )

        # [TODO: remove this once we are confident in our license checks]
        cvs_source_id_entry = cvs.source_id_entries[metadata_minimum.source_id]
        cvs_source_id_values = cvs_source_id_entry.values
        if cvs_source_id_values.license_id is None:
            msg = "License ID must be specified in the CVs source ID"
            raise AssertionError(msg)
        ### End of identical lines

        metadata = Input4MIPsDatasetMetadata(
            activity_id=activity_id,
            contact=cvs_source_id_values.contact,
            dataset_category=metadata_minimum.dataset_category,
            frequency=frequency,
            further_info_url=cvs_source_id_values.further_info_url,
            grid_label=metadata_minimum.grid_label,
            # # TODO: look this up from central CVs
            # institution=cvs_values.institution,
            institution_id=cvs_source_id_values.institution_id,
            license=cvs.license_entries[
                cvs_source_id_values.license_id
            ].values.conditions,
            license_id=cvs_source_id_values.license_id,
            mip_era=cvs_source_id_values.mip_era,
            nominal_resolution=metadata_minimum.nominal_resolution,
            realm=metadata_minimum.realm,
            source_id=metadata_minimum.source_id,
            source_version=cvs_source_id_values.source_version,
            target_mip=metadata_minimum.target_mip,
            variable_id=variable_id,
        )

        return cls(data=data, metadata=metadata, cvs=cvs)

    def get_out_path_and_disk_ready_dataset(  # noqa: PLR0913
        self,
        root_data_dir: Path,
        pint_dequantify_format: str = "cf",
        frequency_metadata_key: str = "frequency",
        no_time_axis_frequency: str = "fx",
        time_dimension: str = "time",
    ) -> tuple[Path, xr.Dataset]:
        """
        Get path in which to write and a disk-ready dataset

        Parameters
        ----------
        root_data_dir
            Root directory in which to write the file

        pint_dequantify_format
            Format to use when dequantifying variables with Pint.

            It is unlikely that you will want to change this.

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
        :
            Path in which to write the file
            and the [iris.cube.Cube][]'s to write in the file.

        Notes
        -----
        You will generally not want to write the output of this directly to disk,
        because it will not be CF-compliant.
        To see how to write CF-compliant files,
        see [`write`][input4mips_validation.dataset.Input4MIPsDataset.write].

        See Also
        --------
        [`write`][input4mips_validation.dataset.Input4MIPsDataset.write]
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
        ds_disk.attrs = convert_input4mips_metadata_to_ds_attrs(self.metadata)
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
        # and we deliberately overwrite any existing values.
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

        return out_path, ds_disk

    def write(  # noqa: PLR0913
        self,
        root_data_dir: Path,
        pint_dequantify_format: str = "cf",
        unlimited_dimensions: tuple[str, ...] = ("time",),
        frequency_metadata_key: str = "frequency",
        no_time_axis_frequency: str = "fx",
        time_dimension: str = "time",
    ) -> Path:
        """
        Write to disk

        This takes a very opionated view of how to write to disk.
        If you need to alter this, please take the source code of this method
        as a template then alter as required.

        Parameters
        ----------
        root_data_dir
            Root directory in which to write the file

        pint_dequantify_format
            Format to use when dequantifying variables with Pint.

            It is unlikely that you will want to change this.
            If you are not using pint for unit handling, this will be ignored.

        unlimited_dimensions
            Dimensions which should be unlimited in the written file

            This is passed to [iris.save][].

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
        :
            Path in which the file was written
        """
        out_path, ds_disk_ready = self.get_out_path_and_disk_ready_dataset(
            root_data_dir=root_data_dir,
            pint_dequantify_format=pint_dequantify_format,
            frequency_metadata_key=frequency_metadata_key,
            no_time_axis_frequency=no_time_axis_frequency,
            time_dimension=time_dimension,
        )

        # Validate
        # As part of https://github.com/climate-resource/input4mips_validation/issues/14
        # add final validation here for bullet proofness
        # - tracking ID, creation date, comparison with DRS from cvs etc.
        validation_result = get_ds_to_write_to_disk_validation_result(
            ds=ds_disk_ready, out_path=out_path, cvs=self.cvs
        )
        validation_result.raise_if_errors()

        # Convert to cubes with ncdata
        cubes = ncdata.iris_xarray.cubes_from_xarray(ds_disk_ready)

        # Having validated and converted to cubes, make the target directory.
        out_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file to disk
        iris.save(
            cubes,
            out_path,
            unlimited_dimensions=unlimited_dimensions,
        )

        return out_path


def prepare_ds_and_get_frequency(  # noqa: PLR0913
    ds_raw: xr.Dataset,
    dimensions: tuple[str, ...] | None = None,
    time_dimension: str = "time",
    add_time_bounds: AddTimeBoundsLike | None = None,
    time_bounds_name: str = f"time{CF_XARRAY_BOUNDS_SUFFIX}",
    standard_and_or_long_names: dict[str, dict[str, str]] | None = None,
    guess_coord_axis: bool = True,
    copy_ds: bool = False,
) -> tuple[xr.Dataset, str]:
    """
    Prepare a raw dataset for initialising a dataset and return frequency metadata.

    Specifically, this function is for initialising a
    [`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset].
    This is a useful function, but is also intended to serve as a template
    for other implementations
    (which can then be injected into the relevant class methods).

    Parameters
    ----------
    ds_raw
        Raw data to prepare

    dimensions
        Dimensions of the dataset, other than the time dimension.

        Passed to [`add_bounds`][input4mips_validation.dataset.dataset.add_bounds].

    time_dimension
        Time dimension of the dataset.

        This is singled out because handling time bounds is often a special case.

    add_time_bounds
        Function that adds bounds to the time variable.

        Passed to [`add_bounds`][input4mips_validation.dataset.dataset.add_bounds].

    time_bounds_name
        The name of the time bounds variable.

        Provided so that users can change this value if they provide custom
        functionality in `add_time_bounds`
        or have a non-default for `time_dimension`.

    standard_and_or_long_names
        Standard/long names to use for the variables in `ds_raw`.

        All variables that are not bounds
        must have attributes that contain a value for at least one of
        `standard_name` and `long_name`.
        Hence this argument is only required
        if the attributes of the variable do not already have these values.

        Each key should be a variable in `ds_raw`.
        The value of `standard_and_or_long_name`
        should itself be a dictionary with keys
        `"standard_name"` for the variable's standard name
        and/or `"long_name"` for the variable's long name.

        E.g.
        `standard_and_or_long_names = {"variable_name": {"standard_name": "flux"}}`

    guess_coord_axis
        Should we guess the co-ordinate axes of the dataset?

    copy_ds
        Should we copy `ds_raw` before modifying the metadata
        or simply modify the existing dataset?

    Returns
    -------
    :
        Prepared data and inferred frequency metadata based on `ds_raw`.
    """
    if copy_ds:
        ds = ds_raw.copy()
    else:
        ds = ds_raw

    ds = add_bounds(
        ds=ds,
        dimensions=dimensions,
        time_dimension=time_dimension,
        add_time_bounds=add_time_bounds,
        # Copying handled above
        copy_ds=False,
    )

    if guess_coord_axis:
        ds = ds.cf.guess_coord_axis()
    ds = ds.cf.add_canonical_attributes()

    ds = handle_ds_standard_long_names(
        ds,
        standard_and_or_long_names=standard_and_or_long_names,
        # Can hard-code input value here because
        # we use cf-xarray to add bounds in `add_bounds`,
        # and that is hard-coded above.
        bounds_indicator=CF_XARRAY_BOUNDS_SUFFIX.strip("_"),
        # No need to copy here as that is already handled on entry
        copy_ds=False,
    )

    frequency = infer_frequency(
        ds,
        time_bounds=time_bounds_name,
    )

    if time_dimension in ds:
        # Make sure time appears first as this is what CF conventions expect
        ds = ds.transpose(time_dimension, ...)

    return ds, frequency


def add_bounds(  # noqa: PLR0913
    ds: xr.Dataset,
    dimensions: Iterable[str] | None = None,
    time_dimension: str = "time",
    add_time_bounds: AddTimeBoundsLike | None = None,
    bounds_dim: str = "bounds",
    copy_ds: bool = False,
) -> xr.Dataset:
    """
    Add bounds to a dataset

    This uses [`cf_xarray`](https://github.com/xarray-contrib/cf-xarray)
    for adding all bounds except for the time bound.
    If you want to follow a different pattern, please feel free to use
    this function as a template.

    Parameters
    ----------
    ds
        Dataset to which to add bounds

    dimensions
        Dimensions of the dataset, excluding the time dimension.

        If not supplied, we simply use all the dimensions of `ds`
        in the order they appear in the dataset.

    time_dimension
        The name of the time dimension

    add_time_bounds
        Function to use to add time bounds.

        If not supplied, we use
        [`add_time_bounds`][input4mips_validation.xarray_helpers.add_time_bounds].

    bounds_dim
        Name of the bounds dimension

        (The dimension used for specifying whether we are at the start or end
        of the bounds, not the suffix used for identifying bounds variables
        or the name of bounds variables.)

    copy_ds
        Should we copy the dataset before modifying it?

    Returns
    -------
    :
        `ds` with added bounds variables.
    """
    if copy_ds:
        ds = ds.copy()

    if dimensions is None:
        dimensions_use: Iterable[str] = tuple(str(v) for v in ds.dims)
    else:
        dimensions_use = dimensions

    if add_time_bounds is None:
        # Can't make mypy behave, hence type ignore
        add_time_bounds_use: AddTimeBoundsLike = iv_xr_helpers.add_time_bounds  # type: ignore
    else:
        add_time_bounds_use = add_time_bounds

    for dim in dimensions_use:
        if dim == time_dimension:
            ds = add_time_bounds_use(ds, output_dim_bounds=bounds_dim)
        else:
            ds = ds.cf.add_bounds(dim, output_dim=bounds_dim)
            # Remove the bounds variable from co-ordinates
            # to avoid iris screaming about CF-conventions later.
            ds = ds.reset_coords(f"{dim}{CF_XARRAY_BOUNDS_SUFFIX}")

    return ds


def handle_ds_standard_long_names(
    ds: xr.Dataset,
    standard_and_or_long_names: dict[str, dict[str, str]] | None,
    bounds_indicator: str,
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

    bounds_indicator
        String which indicates that the variable is a bounds variable.

        These variables don't need standard/long name information.

    copy_ds
        Should we copy `ds` before modifying the metadata?

    Returns
    -------
    :
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
        if bounds_indicator in ds_variable:
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
    Convert metadata to xarray attribute compatible values

    Metadata is of the form
    [Input4MIPsDatasetMetadata][input4mips_validation.dataset.metadata.Input4MIPsDatasetMetadata]
    and the attributes are [xarray.Dataset.attrs][].

    Returns
    -------
        [xarray.Dataset.attrs][] compatible values
    """
    res = {k: v for k, v in asdict(metadata).items() if v is not None}

    return res
