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

    grid_label: str = field()
    """
    Label that identifies the file's grid

    [TODO: cross-ref to controlled vocabulary]
    """


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
