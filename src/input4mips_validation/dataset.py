"""
Input4MIPs dataset model
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

import attr
import xarray as xr
from attrs import asdict, define, field, frozen

from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.dataset_validation import (
    assert_consistency_between_source_id_and_other_values,
    assert_in_cvs,
)
from input4mips_validation.exceptions import DatasetMetadataInconsistencyError


@define
class Input4MIPsDatasetMetadata:
    """
    Metadata for an input4MIPs dataset
    """

    activity_id: str
    """Activity ID that applies to the dataset"""

    dataset_category: str
    """The dataset's category"""

    frequency: str
    """Frequency of the data in the dataset"""

    grid_label: str
    """Grid label of the data in the dataset"""

    institution_id: str
    """Institution ID of the institution that created the dataset"""

    mip_era: str
    """The MIP era that applies to the dataset"""

    realm: str
    """The dataset's realm"""

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
        res = {k: v for k, v in asdict(self).items() if k != "metadata_non_cvs"}
        if self.metadata_non_cvs is not None:
            # Add other keys in too
            res = self.metadata_non_cvs | res

        return res


@define
class Input4MIPsDatasetMetadataDataProducerMinimum:
    """
    Minimum metadata required from an input4MIPs dataset producer
    """

    source_id: str
    """Source ID that applies to the dataset"""


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
        activity_id=value.activity_id,
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
    def _load_default_cvs(self):
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
        dimensions: tuple[str, ...],
        time_dimension: str,
        metadata_minimum: Input4MIPsDatasetMetadataDataProducerMinimum,
        metadata_non_cvs: dict[str, Any] | None = None,
        add_time_bounds: Callable[[xr.Dataset], xr.Dataset] | None = None,
        copy: bool = True,
        cvs: CVsInput4MIPs | None = None,
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

        metadata_minimum
            Minimum metadata required from the data producer

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

        Returns
        -------
            Initialised instance

        Raises
        ------
        AssertionError
            There is a clash between ``metadata_optional`` and the inferred metadata
        """
        if cvs is None:
            cvs = load_cvs()

        cvs_source_id_entry = cvs.source_id_entries[metadata_minimum.source_id]

        metadata = Input4MIPsDatasetMetadata(
            source_id=metadata_minimum.source_id,
            activity_id=cvs_source_id_entry.values.activity_id,
            variable_id=get_ds_var_assert_single(ds),
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

        # # Must be unique for every written file,
        # # so we deliberately don't provide a way
        # # for the user to overwrite this at present
        # ds_disk.attrs["tracking_id"] = generate_tracking_id()
        # ds_disk.attrs["creation_date"] = generate_creation_timestamp()

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

    # Having validated, make the target directory and write
    out_path.parent.mkdir(parents=True, exist_ok=True)
    ds.to_netcdf(out_path, unlimited_dims=unlimited_dims, encoding=encoding)

    return out_path
