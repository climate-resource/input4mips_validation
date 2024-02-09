"""
Input4MIPs dataset handling
"""
from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Any, Callable

import xarray as xr
from attrs import define, field

import input4mips_validation.xarray_helpers
from input4mips_validation.attrs_helpers import (
    make_attrs_validator_compatible_input_only,
)
from input4mips_validation.controlled_vocabularies.file_id import (
    generate_creation_timestamp,
    generate_tracking_id,
)
from input4mips_validation.controlled_vocabularies.inference import (
    format_creation_date_into_version_string,
    format_date_for_filename,
    infer_metadata,
)
from input4mips_validation.controlled_vocabularies.validators import (
    validate_ds_metadata,
    validate_ds_metadata_consistency,
)
from input4mips_validation.metadata import (
    Input4MIPsMetadata,
    Input4MIPsMetadataOptional,
)
from input4mips_validation.validation import assert_dataset_is_valid
from input4mips_validation.xarray_helpers import get_ds_variable

DEFAULT_DIRECTORY_TEMPLATE = str(
    Path("{activity_id}")
    / "{mip_era}"
    / "{target_mip}"
    / "{institution_id}"
    / "{source_id}"
    / "{realm}"
    / "{frequency}"
    / "{variable_id}"
    / "{grid_label}"
    / "v{version}"
)
"""
Default directory template to use when creating :obj:`Input4MIPsDataset`'s.

The separator is whatever the operating system's separator is.
"""

METADATA_SEPARATOR_IN_FILENAME = "_"
"""Separator to use when separating metadata in filenames"""

DEFAULT_FILENAME_TEMPLATE = METADATA_SEPARATOR_IN_FILENAME.join(
    (
        "{variable_id}",
        "{activity_id}",
        "{dataset_category}",
        "{target_mip}",
        "{source_id}",
        "{grid_label}",
        "{start_date}",
        "{end_date}.nc",
    )
)
"""
Default filename template to use when creating :obj:`Input4MIPsDataset`'s.
"""
# Note: We can use attrs validators on the Input4MIPsDatase class
# to add extra checks of filename and data for when
# we have the more complicated cases with extra grid IDs etc.

DEFAULT_ENCODING_KWARGS = {"zlib": True, "complevel": 5}
"""Default values to use when encoding netCDF files"""


# If you're thinking about sub-classing this to update it for e.g. CMIP7,
# please consider instead implementing something which uses the builder pattern.
# That will make the business logic and creation choices easier
# to follow for future developers
# (and the business logic really belongs to the class creation,
# once the rules about what can go in the class are decided,
# everything else follows pretty simply).
@define
class Input4MIPsDataset:
    """
    Representation of an input4MIPs dataset

    The class holds datasets and provides methods for reading them from disk
    and writing them to disk in an input4MIPs-compliant way.
    """

    ds: xr.Dataset = field(
        validator=[
            make_attrs_validator_compatible_input_only(validate_ds_metadata),
            make_attrs_validator_compatible_input_only(
                validate_ds_metadata_consistency
            ),
        ]
    )
    """
    Dataset

    The dataset should already have all the required attributes
    as part of its :attr:`Input4MIPsDataset.attrs` attribute.
    These are valid at initialisation time.
    """

    directory_template: str = field(default=DEFAULT_DIRECTORY_TEMPLATE)
    """
    Template used to determine the directory in which to save the data
    """

    filename_template: str = field(default=DEFAULT_FILENAME_TEMPLATE)
    """
    Template used to determine the filename when saving the data
    """

    @classmethod
    def from_raw_dataset(  # noqa: PLR0913
        cls,
        ds: xr.Dataset,
        dimensions: tuple[str, ...],
        time_dimension: str,
        metadata: Input4MIPsMetadata,
        metadata_optional: Input4MIPsMetadataOptional | None = None,
        add_time_bounds: Callable[[xr.Dataset], xr.Dataset] | None = None,
        copy: bool = True,
        **kwargs: Any,
    ) -> Input4MIPsDataset:
        """
        Create instance from a raw dataset

        We add the metadata to the dataset, infer other metadata based on the data
        and add bounds for the given dataset dimensions.

        Parameters
        ----------
        ds
            Dataset

        dimensions
            Dimensions of the dataset other than the time dimension,
            these are checked for appropriate bounds.
            Bounds are added if they are not present.

        time_dimension
            Time dimension of the dataset.
            This is singled out because handling time bounds is often a special case.

        metadata
            Required metadata which cannot be inferred from the data.

        metadata_optional
            Optional metadata.

        add_time_bounds
            Callable to use to add time bounds.
            If not supplied, uses
            :func:`input4mips_validation.xarray_helpers.add_time_bounds`.

        copy
            Should a copy of the dataset be made? If no, the data is modified
            in place which can cause unexpected changes if references are not
            appropriately managed.

        **kwargs
            Other initialisation arguments for the instance. They are passed
            directly to the constructor.

        Returns
        -------
            Prepared instance

        Raises
        ------
        AssertionError
            ``ds.attrs`` is already set or there is more than one variable in ``ds``
        """
        # TODO: test this properly
        if add_time_bounds is None:
            add_time_bounds = input4mips_validation.xarray_helpers.add_time_bounds

        if ds.attrs:
            raise AssertionError("All metadata should be autogenerated")  # noqa: TRY003

        if time_dimension not in dimensions:
            msg = (
                "``dimensions`` must include ``time_dimension`` "
                "(This choice is made "
                "so you have full control over the order of dimensions). "
                f"Receieved {dimensions=}, {time_dimension=}"
            )
            raise ValueError(msg)

        if copy:
            ds = ds.copy(deep=True)
        else:
            # TODO: think through how we want this to work before opening up
            raise NotImplementedError(copy)

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

        # transpose to match dimensions
        ds = ds.transpose(*dimensions, ...)

        # Get info from metadata
        attributes = {**metadata.to_dataset_attributes(), **infer_metadata(ds)}
        if metadata_optional is not None:
            attributes.update(metadata_optional.to_dataset_attributes())

        ds.attrs = attributes

        return cls(ds, **kwargs)

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
        if encoding_kwargs is None:
            encoding_kwargs = DEFAULT_ENCODING_KWARGS

        # TODO: consider whether this should be hard-coded or not.
        PINT_DEQUANTIFY_FORMAT = "cf"
        # Can shallow copy here as we don't need to worry about mangling the
        # data because the ref (ds_disk) is not retured.
        ds_disk = self.ds.copy(deep=False).pint.dequantify(
            format=PINT_DEQUANTIFY_FORMAT
        )

        # Must be unique for every written file,
        # so we deliberately don't provide a way
        # for the user to overwrite this at present
        ds_disk.attrs["tracking_id"] = generate_tracking_id()
        ds_disk.attrs["creation_date"] = generate_creation_timestamp()
        ds_disk.attrs["version"] = format_creation_date_into_version_string(
            ds_disk.attrs["creation_date"]
        )

        assert_dataset_is_valid(ds_disk)

        out_path = self.get_filepath(
            ds_disk,
            root_data_dir,
        )

        out_path.parent.mkdir(parents=True, exist_ok=True)

        ds_disk.to_netcdf(
            out_path,
            unlimited_dims=unlimited_dims,
            encoding={get_ds_variable(ds_disk): encoding_kwargs},
        )

        return out_path

    def get_filepath(
        self,
        ds_disk: xr.Dataset,
        root_data_dir: Path,
    ) -> Path:
        """
        Get filepath

        Parameters
        ----------
        ds_disk
            Disk-ready dataset

        root_data_dir
            Root directory in which to generate the filepath

        Returns
        -------
            Filepath
        """
        format_date_h = partial(
            format_date_for_filename, ds_frequency=ds_disk.attrs["frequency"]
        )
        available_metadata = {
            **ds_disk.attrs,
            "start_date": format_date_h(ds_disk.time.values.min()),
            "end_date": format_date_h(ds_disk.time.values.max()),
        }

        # TODO: refactor so this is injectable
        metadata_file_path_compatible = {
            k: v.replace(METADATA_SEPARATOR_IN_FILENAME, "-")
            for k, v in available_metadata.items()
        }

        out_dir = self.directory_template.format(**metadata_file_path_compatible)
        out_fname = self.filename_template.format(**metadata_file_path_compatible)

        return root_data_dir / out_dir / out_fname
