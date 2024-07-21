"""
Data model of our input4MIPs database
"""

from __future__ import annotations

import datetime as dt
from collections import OrderedDict
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

import attr._make
import cftime
import numpy as np
import pandas as pd
import xarray as xr
from attrs import NOTHING, Attribute, define, field, fields, make_class

from input4mips_validation.inference.from_data import create_time_range
from input4mips_validation.xarray_helpers.time import xr_time_min_max_to_single_value

if TYPE_CHECKING:
    from input4mips_validation.cvs import Input4MIPsCVs


@define
class Input4MIPsDatabaseEntryFile:
    """
    Data model for a file entry in the input4MIPs database
    """

    Conventions: str
    """CF conventions used in the file"""
    # TODO: validation
    # string that matches CF-X.Y

    activity_id: str
    """Activity ID that applies to the file"""
    # TODO: validation
    # Should be in CVs

    contact: str
    """Email addresses to contact in case of questions about the file"""
    # TODO: validation
    # Should follow some sort of standard form

    creation_date: str
    """Date the file was created"""
    # TODO: validation
    # YYYY-MM-DDTHH:MM:ssZ I think

    dataset_category: str
    """The file's category"""
    # TODO: validation
    # Should be in CVs

    datetime_end: str
    """The file's end time"""
    # TODO: validation
    # Should have specific form, based on file's frequency or standard,
    # unclear right now

    datetime_start: str
    """The file's starting time"""
    # TODO: validation
    # Should have specific form, based on file's frequency or standard,
    # unclear right now

    frequency: str
    """Frequency of the data in the file"""
    # TODO: validation
    # Should be in CVs

    further_info_url: str
    """URL where further information about the file/data in the file can be found"""
    # TODO: validation
    # Should be URL

    grid_label: str = field()
    """
    Label that identifies the file's grid

    [TODO: cross-ref to controlled vocabulary]
    """
    # TODO: validation
    # Should be in CVs

    institution_id: str
    """ID of the institute that created the file"""
    # TODO: validation
    # Should be in CVs

    license: str
    """License information for the dataset"""
    # TODO: validation
    # Should be in CVs

    license_id: str
    """ID of the license that applies to this dataset"""
    # TODO: validation
    # Should be in CVs

    mip_era: str
    """The MIP era to which this file belong"""
    # TODO: validation
    # Should be in CVs

    nominal_resolution: str
    """Nominal resolution of the data in the file"""
    # TODO: validate against CV/tool
    # https://github.com/PCMDI/nominal_resolution
    # May need to add more bins to the tool

    product: str
    """The kind of data in the file"""
    # TODO: validation
    # Should be in CVs

    realm: str
    """The realm of the data in the file"""
    # TODO: validation
    # Should be in CVs

    region: str
    """The region of the data in the file"""
    # TODO: validation
    # Has to be validated against CV/CF conventions
    # https://github.com/PCMDI/obs4MIPs-cmor-tables/blob/master/obs4MIPs_region.json

    source_id: str
    """The ID of the file's source"""
    # TODO: validation
    # Should be in CVs
    # Other fields which must be consistent with source ID values should match

    source_version: str
    """The version of the file, as defined by the source"""
    # TODO: validation
    # Should be consistent with CVs

    target_mip: str
    """The MIP that this file targets"""
    # TODO: validation
    # Should be in CVs

    time_range: str
    """The file's time range"""
    # TODO: validation
    # Should have specific form, based on file's frequency.
    # Should match file name

    tracking_id: str
    """Tracking ID of the file"""
    # TODO: validation
    # Should match specific regexp

    variable_id: str
    """The ID of the variable contained in the file"""
    # TODO: validation (?)
    # Should match file contents/CF conventions (?)

    version: str
    """The version of the file, as defined by the ESGF index"""
    # TODO: validation
    # Should be "vYYYYMMDD", where YYYYMMDD is the date that it was put into the DRS
    # (which is unverifiable)

    grid: str | None = None
    """Long-form description of the grid referred to by `grid_label`"""
    # No validation, any string is fine

    institution: str | None = None
    """Long-form description of the institute referred to by `institution_id`"""
    # No validation, any string is fine

    references: str | None = None
    """References relevant to the file"""
    # TODO: validation (?) e.g. expect only DOIs?

    source: str | None = None
    """Long-form description of the source referred to by `source_id`"""
    # No validation, any string is fine

    # Things to consider:
    # - comment_provider and comment_esgf
    #   - split so that provider can provide comments,
    #     but we can also add comments to ESGF database after the file is published
    #
    # - title
    #   - seems to make little sense to track this in the database

    @classmethod
    def from_file(
        cls,
        file: Path,
        cvs: Input4MIPsCVs,
        frequency_metadata_key: str = "frequency",
        no_time_axis_frequency: str = "fx",
        time_dimension: str = "time",
    ) -> Input4MIPsDatabaseEntryFile:
        """
        Initialise based on a file

        Parameters
        ----------
        file
            File from which to extract data to create the database entry

        cvs
            Controlled vocabularies that were used when writing the file

        frequency_metadata_key
            The key in the data's metadata
            which points to information about the data's frequency.

        no_time_axis_frequency
            The value of "frequency" in the metadata which indicates
            that the file has no time axis i.e. is fixed in time.


        time_dimension
            Time dimension of `ds`

        Returns
        -------
            Initialised database entry
        """
        ds = xr.load_dataset(file)
        # Having to re-infer all of this is silly,
        # would be much simpler if all data was just in the file.
        metadata_attributes = ds.attrs

        metadata_data = {}
        if metadata_attributes[frequency_metadata_key] != no_time_axis_frequency:
            # Technically, this should probably use the bounds...
            time_start = xr_time_min_max_to_single_value(ds[time_dimension].min())
            time_end = xr_time_min_max_to_single_value(ds[time_dimension].max())

            metadata_data["datetime_start"] = format_datetime_for_db(time_start)
            metadata_data["datetime_end"] = format_datetime_for_db(time_end)
            metadata_data["time_range"] = create_time_range(
                time_start=time_start,
                time_end=time_end,
                ds_frequency=metadata_attributes[frequency_metadata_key],
            )

        else:
            metadata_data["datetime_start"] = None
            metadata_data["datetime_end"] = None
            metadata_data["time_range"] = None

        metadata_directories_all = cvs.DRS.extract_metadata_from_path(file.parent)
        # Only get metadata from directories/files that we don't have elsewhere.
        # Reason: the values in the filepath have special characters removed,
        # so may not be correct if used for direct inference.
        metadata_directories_keys_to_use = (
            set(metadata_directories_all.keys())
            .difference(set(metadata_attributes.keys()))
            .difference(set(metadata_data.keys()))
        )
        metadata_directories = {
            k: metadata_directories_all[k] for k in metadata_directories_keys_to_use
        }

        all_metadata = {}
        for md in (metadata_attributes, metadata_data, metadata_directories):
            keys_to_check = md.keys() & all_metadata
            for ktc in keys_to_check:
                if all_metadata[ktc] != md[ktc]:
                    msg = f"Value clash for {ktc}. {all_metadata[ktc]=}, {md[ktc]=}"
                    raise AssertionError(msg)

            all_metadata = all_metadata | md

        # Make sure we only pass metadata that is actully of interest to the database
        cls_fields = [v.name for v in fields(cls)]
        init_kwargs = {k: v for k, v in all_metadata.items() if k in cls_fields}

        return cls(**init_kwargs)


def format_datetime_for_db(time: cftime.datetime | dt.datetime | np.datetime64) -> str:
    """
    Format a "datetime_*" value for storing in the database

    Parameters
    ----------
    time
        Time value to format

    Returns
    -------
        Formatted time value
    """
    if isinstance(time, np.datetime64):
        ts: cftime.datetime | dt.datetime = pd.to_datetime(str(time))

    else:
        ts = time

    return f"{ts.isoformat()}Z"  # Z indicates timezone is UTC


database_entry_file_fields = {f.name: f for f in fields(Input4MIPsDatabaseEntryFile)}


def attr_to_field(
    attr: Attribute, attributes_to_copy: tuple[str, ...] = ("default", "type")
) -> attr._make._CountingAttr:
    """
    Convert an attribute into a field which can be used to create a new class

    Unclear if this is a good way to do this, but seems an ok solution for now.

    Parameters
    ----------
    attr
        Attribute to convert into the input of [`field`][attrs.field].

    Returns
    -------
        Output of [`field`][attrs.field], called with information from `attr`.
    """
    field_kwargs = {k: getattr(attr, k) for k in attributes_to_copy}

    # Hate this, but see if it will work for now
    if field_kwargs["type"] == "str":
        field_kwargs["type"] = str

    return field(**field_kwargs)


def make_class_from_database_entry_file_fields(
    class_name: str,
    fields_to_include: Iterable[str],
) -> type:
    """
    Make a class from the fields of [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]

    Parameters
    ----------
    class_name
        Name of the class to create

    fields_to_include
        Fields from the fields of
        [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
        to include in the created class's attributes.

    Returns
    -------
        Created class
    """
    properties_no_default = []
    properties_default = []
    for ff in fields_to_include:
        if database_entry_file_fields[ff].default == NOTHING:
            properties_no_default.append(database_entry_file_fields[ff])

        else:
            properties_default.append(database_entry_file_fields[ff])

    properties = OrderedDict()
    for v in [*properties_no_default, *properties_default]:
        properties[v.name] = attr_to_field(v)

    created = make_class(
        class_name,
        properties,
    )

    return created
