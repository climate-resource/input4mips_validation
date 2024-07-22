"""
Classes that define an input4MIPs dataset and associated metadata
"""

from __future__ import annotations

from input4mips_validation.dataset.dataset import Input4MIPsDataset
from input4mips_validation.dataset.metadata import Input4MIPsDatasetMetadata
from input4mips_validation.dataset.metadata_data_producer_minimum import (
    Input4MIPsDatasetMetadataDataProducerMinimum,
)
from input4mips_validation.dataset.metadata_data_producer_multiple_variable_minimum import (  # noqa: E501
    Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum,
)

__all__ = [
    "Input4MIPsDataset",
    "Input4MIPsDatasetMetadata",
    "Input4MIPsDatasetMetadataDataProducerMinimum",
    "Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum",
]
