"""
Data model of our input4MIPs database
"""

from __future__ import annotations

from collections.abc import Iterable

import attr._make
from attrs import Attribute, define, field, fields, make_class


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
    return field(**{k: getattr(attr, k) for k in attributes_to_copy})


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
    created = make_class(
        class_name,
        {
            database_entry_file_fields[k].name: attr_to_field(
                database_entry_file_fields[k]
            )
            for k in fields_to_include
        },
    )

    return created
