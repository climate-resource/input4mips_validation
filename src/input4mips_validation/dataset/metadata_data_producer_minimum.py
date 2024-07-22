# This file is auto-generated, do not edit by hand!!
"""Minimum metadata required from an input4MIPs dataset producer"""

from attrs import define, field


@define
class Input4MIPsDatasetMetadataDataProducerMinimum:
    """
    Minimum metadata required from an input4MIPs dataset producer

    This is the minimum metadata required to create a valid
    [`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
    [`from_data_producer_minimum_information`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information].
    """

    grid_label: str = field()
    """
    Label that identfies the file's grid

    [TODO: cross-ref to the CVs]
    """
