# This file is auto-generated by pre-commit, do not edit by hand!!
"""
Raw database definition

This only contains the fields, no methods.
For a more useful class, see
[`Input4MIPsDatabaseEntryFile`][Input4MIPsDatabaseEntryFile].
"""

from typing import Union

from attrs import define, field


@define
class Input4MIPsDatabaseEntryFileRaw:
    """
    Raw data model for a file entry in the input4MIPs database
    """

    Conventions: str
    """CF conventions used in the file"""

    grid_label: str = field()
    """
    Label that identfies the file's grid

    [TODO: cross-ref to the CVs]
    """

    grid: Union[str, None] = None
    """Long-form description of the grid referred to by `grid_label`"""
