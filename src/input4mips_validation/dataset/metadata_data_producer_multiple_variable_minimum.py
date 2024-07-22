# This file is auto-generated by pre-commit, do not edit by hand!!
"""
Minimum metadata required from an input4MIPs dataset producer for a multi-variable file
"""

from attrs import define, field


@define
class Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum:
    """
    Minimum metadata required from input4MIPs dataset producer for a multi-variable file

    This is the minimum metadata required to create a valid
    [`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
    [`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable].
    """

    grid_label: str = field()
    """
    Label that identfies the file's grid

    [TODO: cross-ref to the CVs]
    """

    nominal_resolution: str
    """Nominal resolution of the data in the file"""

    product: str
    """The kind of data in the file"""

    region: str
    """The region of the data in the file"""

    source_id: str
    """The ID of the file's source"""

    target_mip: str
    """The MIP that this file targets"""

    dataset_category: str
    """The file's category"""

    realm: str
    """The realm of the data in the file"""
