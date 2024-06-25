"""
Input4MIPs dataset model
"""
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Callable

import attr
import xarray as xr
from attrs import asdict, define, field

from input4mips_validation.attrs_helpers import (
    make_attrs_validator_compatible_input_only,
)
from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.dataset_validation import (
    assert_consistency_between_source_id_and_other_values,
    assert_in_cvs,
)
from input4mips_validation.exceptions import DatasetMetadataInconsistencyError

CVS: CVsInput4MIPs | None = None
"""Controlled vocabularies to use throughout"""


@define
class Input4MIPsDatasetMetadata:
    """
    Metadata for an input4MIPs dataset
    """

    activity_id: str
    """Activity ID that applies to the dataset"""

    source_id: str
    """Source ID that applies to the dataset"""

    variable_id: str
    """The ID of the variable contained in the dataset"""

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
    cvs: CVsInput4MIPs | None = None,
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

    cvs
        CVs to use for validation

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs`.
    """
    if cvs is None:
        cvs = load_cvs()

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


def validate_ds(
    ds: xr.Dataset,
    cvs: CVsInput4MIPs | None = None,
) -> None:
    """
    Validate that a {py:obj}`xr.Dataset` confirms to the required form

    Currently this is a no-op

    Parameters
    ----------
    ds
        Dataset to validate

    cvs
        CVs to use for validation

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs`.
    """
    if cvs is None:
        cvs = load_cvs()

    dataset_variable = list(ds.data_vars)
    if len(dataset_variable) != 1:
        msg = f"``ds`` must only have one variable. Received: {dataset_variable!r}"
        raise AssertionError(msg)


def validate_ds_metadata_consistency(
    instance: Input4MIPsDataset,
    attribute: attr.Attribute[Any],
    value: Input4MIPsDatasetMetadata,
    cvs: CVsInput4MIPs | None = None,
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

    cvs
        CVs to use for validation

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.cv_loading.load_cvs`.
    """
    if cvs is None:
        cvs = load_cvs()

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


@define
class Input4MIPsDataset:
    """
    Representation of an input4MIPs dataset
    """

    ds: xr.Dataset = field(
        validator=[
            make_attrs_validator_compatible_input_only(partial(validate_ds, cvs=CVS)),
        ]
    )
    """
    Dataset
    """

    metadata: Input4MIPsDatasetMetadata = field(
        validator=[
            partial(validate_ds_metadata, cvs=CVS),
            partial(validate_ds_metadata_consistency, cvs=CVS),
        ]
    )
    """
    Metadata about the dataset
    """

    @property
    def ds_var(self) -> str:
        """
        Get the name of the variable in ``self.ds``

        If xarray has a better way to do this, PRs welcome :)

        Returns
        -------
            Name of the variable in ``self.ds``
        """
        ds_var_l = list(self.ds.data_vars)
        if len(ds_var_l) != 1:  # pragma: no cover
            msg = "Should have been caught at initialisation"
            raise AssertionError(msg)

        return ds_var_l[0]

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

        Returns
        -------
            Initialised instance

        Raises
        ------
        AssertionError
            There is a clash between ``metadata_optional`` and the inferred metadata
        """
        if CVS is not None:
            cvs_h = CVS
        else:
            cvs_h = load_cvs()

        cvs_source_id_entry = cvs_h.source_id_entries[metadata_minimum.source_id]

        metadata = Input4MIPsDatasetMetadata(
            source_id=metadata_minimum.source_id,
            activity_id=cvs_source_id_entry.values.activity_id,
            metadata_non_cvs=metadata_non_cvs,
        )

        return cls(ds=ds, metadata=metadata)

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
