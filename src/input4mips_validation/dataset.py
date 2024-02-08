"""
Input4MIPs dataset handling
"""
from __future__ import annotations

from pathlib import Path

import xarray as xr
from attrs import define, field

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
# We can use attrs validators to add extra checks of filename and data for when
# we have the more complicated cases with extra grid IDs etc.


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

    ds: xr.Dataset
    """
    Dataset
    """

    directory_template: str = field(default=DEFAULT_DIRECTORY_TEMPLATE)
    """
    Template used to determine the directory in which to save the data
    """

    filename_template: str = field(default=DEFAULT_FILENAME_TEMPLATE)
    """
    Template used to determine the filename when saving the data
    """
