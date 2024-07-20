"""
Classes that define an input4MIPs dataset and associated metadata
"""

from __future__ import annotations

import xarray as xr
from attrs import field, frozen

from input4mips_validation.database import make_class_from_database_entry_file_fields

DATASET_PRODUCER_MINIMUM_FIELDS = (
    "grid_label",
    "nominal_resolution",
    "product",
    "region",
    "source_id",
    "target_mip",
)

Input4MIPsDatasetMetadataDataProducerMinimum = (
    make_class_from_database_entry_file_fields(
        "Input4MIPsDatasetMetadataDataProducerMinimum",
        DATASET_PRODUCER_MINIMUM_FIELDS,
    )
)
"""
Minimum metadata from input4MIPs dataset producer

This is the minimum metadata required to create a valid
[`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
[`from_data_producer_minimum_information`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information].

For an explanation of the required fields,
see [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
"""
# Adding docstrings like this is a hack while this issue is ongoing:
# https://github.com/python-attrs/attrs/issues/1309

# multi-variable minimum

DATASET_PRODUCER_MULTI_VARIABLE_MINIMUM_FIELDS = (
    *DATASET_PRODUCER_MINIMUM_FIELDS,
    "dataset_category",
    "realm",
)

Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum = (
    make_class_from_database_entry_file_fields(
        "Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum",
        DATASET_PRODUCER_MULTI_VARIABLE_MINIMUM_FIELDS,
    )
)
"""
Minimum metadata from input4MIPs dataset producer for a multi-variable file

This is the minimum metadata required to create a valid
[`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
[`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable].

For an explanation of the required fields,
see [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
"""
# Adding docstrings like this is a hack while this issue is ongoing:
# https://github.com/python-attrs/attrs/issues/1309

DATASET_METADATA_FIELDS = (
    # "activity_id",
    # "contact",
    # "dataset_category",
    # "frequency",
    # "further_info_url",
    "grid_label",
    # "institution",
    # "institution_id",
    # "license",
    # "license_id",
    # "mip_era",
    # "nominal_resolution",
    # "product",
    # "realm",
    # "region",
    # "source",
    # "source_id",
    # "source_version",
    # "target_mip",
    # "variable_id",
)
Input4MIPsDatasetMetadata = make_class_from_database_entry_file_fields(
    "Input4MIPsDatasetMetadata",
    DATASET_METADATA_FIELDS,
)
"""
Metadata for an input4MIPs dataset

For an explanation of the fields,
see [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
"""
# Adding docstrings like this is a hack while this issue is ongoing:
# https://github.com/python-attrs/attrs/issues/1309

# CV handling
# - can also pull those tests back in


@frozen
class Input4MIPsDataset:
    """
    Representation of an input4MIPs dataset

    For validation, see [`validate_ds`][input4mips_validation.validation.validate_input4mips_ds].
    TODO: check cross-reference once we switch to mkdocs,
    help here I think https://pypi.org/project/mkdocstrings/0.9.0/
    maybe also here https://mkdocstrings.github.io/usage/
    """

    data: xr.Dataset
    """
    Data
    """

    metadata: Input4MIPsDatasetMetadata
    """
    Metadata
    """

    cvs: Input4MIPsCVs = field()
    """
    Controlled vocabularies to use with this dataset

    If not supplied, we create these with
    [`load_cvs`][input4mips_validation.cvs.loading.load_cvs]
    """

    @cvs.default
    def _load_default_cvs(self) -> Input4MIPsCVs:
        return load_cvs()
