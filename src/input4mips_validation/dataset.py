"""
Input4MIPs dataset model
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import attr
import cf_xarray  # noqa: F401
import xarray as xr
from attrs import asdict, define, field, frozen

import input4mips_validation.xarray_helpers as iv_xr_helpers
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.cvs_inference import (
    VARIABLE_DATASET_CATEGORY_MAP,
    VARIABLE_REALM_MAP,
    infer_frequency,
    infer_time_range,
)
from input4mips_validation.cvs_handling.input4MIPs.dataset_validation import (
    assert_consistency_between_source_id_and_other_values,
    assert_in_cvs,
)
from input4mips_validation.cvs_handling.input4MIPs.general_validation import (
    assert_is_url_like,
)
from input4mips_validation.dataset_writing_helpers import (
    generate_creation_timestamp,
    generate_tracking_id,
)
from input4mips_validation.exceptions import DatasetMetadataInconsistencyError


# TODO: describe data model more generally
@define
class Input4MIPsDatasetMetadataFromFiles:
    """
    Data model for metadata that comes from a dataset's file(s)
    """

    Conventions: str
    """CF conventions used when writing the dataset"""

    activity_id: str
    """Activity ID that applies to the dataset"""

    contact: str
    """Email addresses to contact in case of questions about the dataset"""

    creation_date: str
    """Date the dataset was created"""

    dataset_category: str
    """The dataset's category"""

    datetime_end: str
    """The dataset's end time"""

    datetime_start: str
    """The dataset's starting time"""

    frequency: str
    """Frequency of the data in the dataset"""

    further_info_url: str
    """URL where further information about the dataset can be found"""

    grid_label: str
    """Grid label of the data in the dataset"""

    institution_id: str
    """ID of the institute that created the dataset"""

    license: str
    """License information for the dataset"""

    mip_era: str
    """The MIP era that applies to the dataset"""

    nominal_resolution: str
    """Nominal resolution of the data in the dataset"""

    product: str
    """The kind of data that this dataset is"""

    realm: str
    """The dataset's realm"""
    #
    # region: str
    # """The dataset's region"""
    # # Has to be validated against CV/CF conventions

    # # Should be looked up from central CMIP stuff based on source_id,
    # # hence ignoring for now
    # source: str
    # """Longer name of the source that created the dataset"""

    source_id: str
    """Source ID that applies to the dataset"""

    target_mip: str
    """The dataset's target MIP"""

    time_range: str
    """The dataset's time range"""

    tracking_id: str
    """Tracking ID of the dataset"""

    variable_id: str
    """The ID of the variable contained in the dataset"""

    version: str
    """The version ID of the dataset as defined by the provider"""
    # TODO: introduce the below and rename the above to source_version
    # version: str
    # """
    # Datestamp of the day on which the dataset was produced
    #
    # This is used to provide a unique version on the ESGF,
    # which can't handle versions with special characters
    # (which is what goes in ``source_version``).
    # The uniqueness of this version obviously relies on data
    # being published daily or less frequently to ESGF.
    # This is a fine assumption for now.
    # """

    institution: str | None = None
    """Longer name of the institute that created the dataset"""


@define
class Input4MIPsDatasetMetadataFromESGF:
    """
    Data model for metadata that is managed by the ESGF
    """

    data_node: str | None = None
    """Data node on which the dataset is held"""

    latest: bool | None = None
    """
    Whether this dataset is the latest in its series

    Series is not precisely defined.
    """

    publication_status: str | None = "in_publishing_queue"
    """Publication status of the dataset"""
    # Should match CVs

    replica: bool | None = None
    """Whether the data on this node is a replica of the original data"""

    timestamp: str | None = None
    """Timestamp of the dataset on the ESGF index"""

    xlink: str | None = None
    """Link to the dataset on the ESGF"""


@define
class Input4MIPsDatasetMetadataEntry:
    """
    Data model for a single dataset entry in the input4MIPs collection

    For validation, see [TODO: {py:func}`validate_dataset_metadata`]
    """

    file: Input4MIPsDatasetMetadataFromFiles
    """Dataset metadata that is contained in the file"""

    esgf: Input4MIPsDatasetMetadataFromESGF
    """Dataset metadata that is managed by the ESGF"""

    # TODO: remove Input4MIPsDatasetMetadata as that is a duplicate


@define
class Input4MIPsDatasetMetadata:
    """
    Metadata for an input4MIPs dataset
    """

    activity_id: str
    """Activity ID that applies to the dataset"""

    contact: str
    """Email addresses to contact in case of questions"""
    # TODO: add validation that this is an email

    dataset_category: str
    """The dataset's category"""

    datetime_end: str
    """The end time of the dataset"""
    # TODO: validation based on agreement with frequency
    # TODO: validation based on agreement with time_range

    datetime_start: str
    """The starting time of the dataset"""
    # TODO: validation based on agreement with frequency
    # TODO: validation based on agreement with time_range

    frequency: str
    """Frequency of the data in the dataset"""

    further_info_url: str
    """URL that provides further information about the data"""

    grid_label: str
    """Grid label of the data in the dataset"""

    institution_id: str
    """Institution ID of the institution that created the dataset"""

    license_id: str
    """License ID for the information in the dataset"""
    # Needs to be validated against CVs
    # (but note that CVs values are moving)

    license: str
    """License information for the dataset"""
    # Needs to be validated against CVs
    # (but note that CVs values are moving)

    mip_era: str
    """The MIP era that applies to the dataset"""

    nominal_resolution: str
    """Nominal resolution of the data in the dataset"""
    # Validation rules completely unclear

    product: str
    """The kind of data that this dataset is"""
    # Has to match CVs

    realm: str
    """The dataset's realm"""

    # # Should be looked up from central CMIP stuff based on source_id,
    # hence ignoring for now
    # source: str
    # """Longer name of the source that created the dataset"""

    source_id: str
    """Source ID that applies to the dataset"""

    target_mip: str
    """The dataset's target MIP"""

    time_range: str
    """The dataset's time range"""

    variable_id: str
    """The ID of the variable contained in the dataset"""

    version: str
    """The version ID of the dataset"""

    metadata_non_cvs: dict[str, Any] | None = field(default=None)
    """Other metadata fields that aren't covered by the CVs"""

    institution: str | None = None
    """Longer name of the institution that created the dataset"""

    @metadata_non_cvs.validator
    def _no_clash_with_other_attributes(
        self, attribute: attr.Attribute[Any], value: dict[str, Any] | None
    ) -> None:
        if value is None:
            return

        self_keys = set(asdict(self).keys() - {attribute.name})

        clashing_keys = [key for key in value if key in self_keys]
        if clashing_keys:
            msg = (
                f"{attribute.name} must not contain any keys "
                "that clash with the other metadata. "
                f"Clashing keys: {clashing_keys}"
            )
            raise AssertionError(msg)

    @property
    def to_ds_metadata(self) -> dict[str, str]:
        """
        Convert to {py:attr}`xr.Dataset.attrs` compatible values

        For example, this ensures that {py:attr}`metadata_non_cvs`
        is only included if it is not ``None``.

        Returns
        -------
            {py:attr}`xr.Dataset.attrs` compatible values
        """
        res = {
            k: v
            for k, v in asdict(self).items()
            if (k != "metadata_non_cvs") and (v is not None)
        }
        if self.metadata_non_cvs is not None:
            # Add other keys in too
            res = self.metadata_non_cvs | res

        return res


@define
class Input4MIPsDatasetMetadataDataProducerMinimum:
    """
    Minimum metadata required from an input4MIPs dataset producer
    """

    grid_label: str
    """
    The grid label that applies to the dataset

    We may be able to remove this in future,
    but right now the rules around calculating grid label are not clear to us.
    """

    nominal_resolution: str
    """
    The nominal resolution of the data in the dataset

    We may be able to remove this in future,
    but right now the rules around calculating nominal resolution are not clear to us.
    """

    product: str
    """The kind of data that this dataset is"""

    source_id: str
    """Source ID that applies to the dataset"""

    target_mip: str
    """
    The dataset's target MIP

    This should be inferrable in the future, but isn't currently
    because we don't include the target experiment information
    nor a mapping from experiment to target MIP.
    """


def validate_ds_metadata(
    instance: Input4MIPsDataset,
    attribute: attr.Attribute[Any],
    value: Input4MIPsDatasetMetadata,
) -> None:
    """
    Validate the metadata of an {py:obj}`Input4MIPsDataset`

    Parameters
    ----------
    instance
        Instance being validated

    attribute
        Attribute being initialised

    value
        Value being set
    """
    cvs = instance.cvs

    # Activity ID
    assert_in_cvs(
        value=value.activity_id,
        cvs_key="activity_id",
        cv_values=cvs.activity_id_entries.activity_ids,
        cvs=cvs,
    )

    # Further info URL
    assert_is_url_like(
        value=value.further_info_url,
        description="further_info_url",
    )

    # Institution ID
    assert_in_cvs(
        value=value.institution_id,
        cvs_key="institution_id",
        cv_values=cvs.institution_ids,
        cvs=cvs,
    )

    # Source ID
    assert_in_cvs(
        value=value.source_id,
        cvs_key="source_id",
        cv_values=cvs.source_id_entries.source_ids,
        cvs=cvs,
    )

    # Consistency with source ID
    assert_consistency_between_source_id_and_other_values(
        source_id=value.source_id,
        further_info_url=value.further_info_url,
        institution_id=value.institution_id,
        cvs=cvs,
    )


def get_ds_var_assert_single(ds: xr.Dataset) -> str:
    """
    Get a {py:obj}`xr.Dataset`'s variable, asserting that there is only one

    Parameters
    ----------
    ds
        {py:obj}`xr.Dataset` from which to retrieve the variable

    Returns
    -------
        ``ds``'s variable
    """
    ds_var_l: list[str] = list(ds.data_vars)
    if len(ds_var_l) != 1:
        msg = f"``ds`` must only have one variable. Received: {ds_var_l!r}"
        raise AssertionError(msg)

    return ds_var_l[0]


def validate_ds(
    instance: Input4MIPsDataset,
    attribute: attr.Attribute[Any],
    value: xr.Dataset,
) -> None:
    """
    Validate that a {py:obj}`xr.Dataset` confirms to the required form

    Currently this is a no-op

    Parameters
    ----------
    instance
        Instance being validated
    attribute
        Attribute being set

    value
        Value being used to set ``attribute``
    """
    # cvs = instance.cvs

    try:
        get_ds_var_assert_single(value)
    except AssertionError as exc:
        msg = (
            f"The value used for `{attribute.name}` must only contain a single variable"
        )
        raise AssertionError(msg) from exc


def validate_ds_metadata_consistency(
    instance: Input4MIPsDataset,
    attribute: attr.Attribute[Any],
    value: Input4MIPsDatasetMetadata,
) -> None:
    """
    Check consistency between the dataset and metadata of an {py:obj}`Input4MIPsDataset`

    Parameters
    ----------
    instance
        Instance being validated

    attribute
        Attribute being initialised

    value
        Value being set
    """
    # cvs = instance.cvs

    metadata = value

    # Variable ID
    dataset_variable = instance.ds_var

    if dataset_variable != metadata.variable_id:
        raise DatasetMetadataInconsistencyError(
            ds_key="The dataset's variable",
            ds_key_value=f"{dataset_variable=}",
            metadata_key="metadata.variable_id",
            metadata_key_value=f"{metadata.variable_id=!r}",
        )


@frozen
class Input4MIPsDataset:
    """
    Representation of an input4MIPs dataset
    """

    ds: xr.Dataset = field(validator=[validate_ds])
    """
    Dataset
    """

    metadata: Input4MIPsDatasetMetadata = field(
        validator=[
            validate_ds_metadata,
            validate_ds_metadata_consistency,
        ]
    )
    """
    Metadata about the dataset
    """

    cvs: CVsInput4MIPs = field()
    """
    Controlled vocabularies to use with this dataset

    If not supplied, we create these with
    {py:func}`input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs`
    """

    @cvs.default
    def _load_default_cvs(self) -> CVsInput4MIPs:
        return load_cvs()

    @property
    def ds_var(self) -> str:
        """
        Get the name of the variable in ``self.ds``

        If xarray has a better way to do this, PRs welcome :)

        Returns
        -------
            Name of the variable in ``self.ds``
        """
        return get_ds_var_assert_single(self.ds)

    @classmethod
    def from_data_producer_minimum_information(  # noqa: PLR0913
        cls,
        ds: xr.Dataset,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMinimum,
        dimensions: tuple[str, ...] | None = None,
        time_dimension: str = "time",
        metadata_non_cvs: dict[str, Any] | None = None,
        add_time_bounds: Callable[[xr.Dataset], xr.Dataset] | None = None,
        copy: bool = True,
        cvs: CVsInput4MIPs | None = None,
        activity_id: str = "input4MIPs",
    ) -> Input4MIPsDataset:
        """
        Initialise from the minimum required information from the data producer

        Parameters
        ----------
        ds
            Raw dataset

        metadata_minimum
            Minimum metadata required from the data producer

        dimensions
            Dimensions of the dataset other than the time dimension,
            these are checked for appropriate bounds.
            Bounds are added if they are not present.

            If not supplied, we simply use all the dimensions of ``ds``
            in the order they appear in the dataset.

        time_dimension
            Time dimension of the dataset.
            This is singled out because handling time bounds is often a special case.

        metadata_non_cvs
            Any other metadata the data producer would like to provider

            This must not clash with any of our inferred metadata.

        add_time_bounds

        copy
            Callable to use to add time bounds.
            If not supplied, uses
            :func:`input4mips_validation.xarray_helpers.add_time_bounds`.

        cvs
            CVs to use for inference and validation

            If not supplied, this will be retrieved with
            {py:func}`input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs`.

        activity_id
            Activity ID that applies to the dataset.

            Given this is an Input4MIPsDataset, you shouldn't need to change this.

        Returns
        -------
            Initialised instance

        Raises
        ------
        AssertionError
            There is a clash between ``metadata_optional`` and the inferred metadata
        """
        if dimensions is None:
            dimensions = tuple(ds.dims)  # type: ignore

        if add_time_bounds is None:
            add_time_bounds = iv_xr_helpers.add_time_bounds

        if cvs is None:
            cvs = load_cvs()

        cvs_source_id_entry = cvs.source_id_entries[metadata_minimum.source_id]

        # add extra metadata following CF conventions, not really sure what
        # this does but it's free so we include it on the assumption that they
        # know more than we do
        ds = ds.cf.guess_coord_axis().cf.add_canonical_attributes()

        # add bounds to dimensions
        for dim in dimensions:
            if dim == time_dimension:
                ds = add_time_bounds(ds)
            else:
                ds = ds.cf.add_bounds(dim)

        cvs_values = cvs_source_id_entry.values
        variable_id = get_ds_var_assert_single(ds)
        frequency = infer_frequency(ds, time_bounds=f"{time_dimension}_bounds")

        start_end_separator = "-"
        time_range = infer_time_range(
            ds,
            frequency=frequency,
            time_dimension=time_dimension,
            start_end_separator=start_end_separator,
        )
        datetime_start, datetime_end = time_range.split(start_end_separator)

        metadata = Input4MIPsDatasetMetadata(
            activity_id=activity_id,
            contact=cvs_values.contact,
            dataset_category=VARIABLE_DATASET_CATEGORY_MAP[variable_id],
            datetime_end=datetime_end,
            datetime_start=datetime_start,
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
            product=metadata_minimum.product,
            realm=VARIABLE_REALM_MAP[variable_id],
            source_id=metadata_minimum.source_id,
            target_mip=metadata_minimum.target_mip,
            time_range=time_range,
            variable_id=variable_id,
            version=cvs_values.version,
            metadata_non_cvs=metadata_non_cvs,
        )

        return cls(ds=ds, metadata=metadata, cvs=cvs)

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
        cvs = self.cvs

        if encoding_kwargs is None:
            encoding_kwargs = DEFAULT_ENCODING_KWARGS

        out_path = root_data_dir / cvs.get_file_path(self.metadata)

        # Can shallow copy as we don't alter the data from here on
        ds_disk = self.ds.copy(deep=False).pint.dequantify(
            format=PINT_DEQUANTIFY_FORMAT
        )

        # Add all the metadata
        ds_disk.attrs = self.metadata.to_ds_metadata

        # Must be unique for every written file,
        # so we deliberately don't provide a way
        # for the user to overwrite this at present
        ds_disk.attrs["tracking_id"] = generate_tracking_id()
        ds_disk.attrs["creation_date"] = generate_creation_timestamp()

        return write(
            ds=ds_disk,
            out_path=out_path,
            unlimited_dims=unlimited_dims,
            encoding={self.ds_var: encoding_kwargs},
        )


PINT_DEQUANTIFY_FORMAT = "cf"
"""
Format string to use when dequantifying variables with pint
"""

DEFAULT_ENCODING_KWARGS = {"zlib": True, "complevel": 5}
"""Default values to use when encoding netCDF files"""


def write(
    ds: xr.Dataset,
    out_path: Path,
    unlimited_dims: tuple[str, ...],
    encoding: dict[str, Any],
) -> Path:
    """
    Write a dataset to disk

    Parameters
    ----------
    ds
        Dataset to write to disk

    out_path
        Path in which to write the dataset

    unlimited_dims
        Dimensions which should be written as unlimited

    encoding
        Encoding to apply when writing

    Returns
    -------
        Path in which the dataset was written
    """
    # As part of https://github.com/climate-resource/input4mips_validation/issues/14
    # add final validation here for bullet proofness
    # - tracking ID, creation date etc.

    # Having validated, make the target directory and write
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(out_path, unlimited_dims=unlimited_dims, encoding=encoding)

    return out_path
