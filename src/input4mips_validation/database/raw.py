# This file is auto-generated by pre-commit, do not edit by hand!!
"""
Raw database definition

This only contains the fields, no methods.
For a more useful class, see
[`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile].
"""

from typing import Union

from attrs import field, frozen


@frozen
class Input4MIPsDatabaseEntryFileRaw:
    """
    Raw data model for a file entry in the input4MIPs database
    """

    Conventions: str
    """CF conventions used in the file"""

    activity_id: str
    """Activity ID that applies to the file"""

    contact: str
    """Email addresses to contact in case of questions about the file"""

    creation_date: str
    """Date the file was created"""

    dataset_category: str
    """The file's category"""

    datetime_end: Union[str, None]
    """
    The file's end time

    If the file has no time axis or is a fixed file, this should be `None`
    """

    datetime_start: Union[str, None]
    """
    The file's start time

    If the file has no time axis or is a fixed file, this should be `None`
    """

    esgf_dataset_master_id: str
    """
    Master ID as used by the ESGF

    This applies to the dataset level, not the file level.
    However, it is still useful to capture.
    """

    filepath: str
    """Full path in which the file is written"""

    frequency: str
    """Frequency of the data in the file"""

    further_info_url: str
    """URL where further information about the file/data in the file can be found"""

    grid_label: str = field()
    """
    Label that identfies the file's grid

    [TODO: cross-ref to the CVs]
    """

    institution_id: str
    """ID of the institute that created the file"""

    license: str
    """License information for the dataset"""

    mip_era: str
    """The MIP era to which this file belong"""

    nominal_resolution: str
    """Nominal resolution of the data in the file"""

    realm: str
    """The realm of the data in the file"""

    sha256: str
    """sha256 hash of the file"""

    source_id: str
    """The ID of the file's source"""

    source_version: str
    """The version of the file, as defined by the source"""

    target_mip: str
    """The MIP that this file targets"""

    time_range: Union[str, None]
    """
    The file's time range

    If the file has no time axis or is a fixed file, this should be `None`
    """

    tracking_id: str
    """
    Tracking ID of the file

    This should be unique for every file.
    We typically use the uuid library to generate this.

    ```python
    # For example
    import uuid  # part of the standard library

    tracking_id = f"hdl:21.14100/{uuid.uuid4()}"
    ```
    """

    variable_id: str
    """The ID of the variable contained in the file"""

    version: str
    """
    The version of the file, as defined by the DRS

    The ESGF also has a _version_ attribute for each file entry,
    which is different again.

    """

    comment: Union[str, None] = None
    """
    Comments that apply to the file

    These are the comments included in the file itself.
    As a result, they can only apply to the file at the time of writing.
    For comments made about the file after the fact,
    e.g. reasons for deprecation,
    see `comment_post_publication`.
    """

    comment_post_publication: Union[str, None] = None
    """
    Comments that apply to the file but are added after its publication

    These comments can be added to the file after it has been published.
    For example, e.g. reasons for deprecating the file.
    For the comments that were made at the time of writing the file, see `comment`.

    """

    data_node: Union[str, None] = None
    """Data node on which this file is stored on ESGF"""

    doi: Union[str, None] = None
    """The digital object identifier (DOI) associated with the file."""

    grid: Union[str, None] = None
    """Long-form description of the grid referred to by `grid_label`"""

    institution: Union[str, None] = None
    """Long-form description of the institute referred to by `institution_id`"""

    latest: Union[bool, None] = None
    """
    Is this data set still valid?

    A value of `None` indicates that the file has not been published yet.
    A value of `False` indicates that this file has been deprecated.
    See `comment_post_publication` for an explanation of why.
    """

    license_id: Union[str, None] = None
    """ID of the license that applies to this dataset"""

    publication_status: str = "in_publishing_queue"
    """The file's publication status"""

    product: Union[str, None] = None
    """The kind of data in the file"""

    references: Union[str, None] = None
    """References relevant to the file"""

    region: Union[str, None] = None
    """The region of the data in the file"""

    replica: Union[bool, None] = None
    """Is this dataset a replica on its ESGF node or the 'original'"""

    source: Union[str, None] = None
    """Long-form description of the source referred to by `source_id`"""

    timestamp: Union[str, None] = None
    """
    Timestamp of the last modification to the file's ESGF entry

    This is scraped from the ESGF.
    """

    validated_input4mips: Union[bool, None] = None
    """
    Has this file been validated by the input4MIPs team?

    If `None`, the file has not been validated yet.
    If `True`, the file passed valdiation.
    If `False`, the file failed validation.

    """

    xlink: Union[tuple[str], None] = None
    """Cross-link to more information about the file (DOI?)"""
