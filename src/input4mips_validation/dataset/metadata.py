# This file is auto-generated by pre-commit, do not edit by hand!!
"""
Metadata for `Input4MIPsDataset` objects

See [Input4MIPsDataset][input4mips_validation.dataset.dataset.Input4MIPsDataset]
"""

from typing import Union

from attrs import define, field


@define
class Input4MIPsDatasetMetadata:
    """
    Metadata for an input4MIPs dataset
    """

    activity_id: str
    """Activity ID that applies to the file"""

    contact: str
    """Email addresses to contact in case of questions about the file"""

    dataset_category: str
    """The file's category"""

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

    source_id: str
    """The ID of the file's source"""

    source_version: str
    """The version of the file, as defined by the source"""

    target_mip: str
    """The MIP that this file targets"""

    variable_id: str
    """The ID of the variable contained in the file"""

    comment: Union[str, None] = None
    """
    Comments that apply to the file

    These are the comments included in the file itself.
    As a result, they can only apply to the file at the time of writing.
    For comments made about the file after the fact,
    e.g. reasons for deprecation,
    see `comment_post_publication`.
    """

    institution: Union[str, None] = None
    """Long-form description of the institute referred to by `institution_id`"""

    license_id: Union[str, None] = None
    """ID of the license that applies to this dataset"""

    product: Union[str, None] = None
    """The kind of data in the file"""

    region: Union[str, None] = None
    """The region of the data in the file"""

    source: Union[str, None] = None
    """Long-form description of the source referred to by `source_id`"""
