"""
Exceptions used in the top-level modules
"""

from __future__ import annotations


class DatasetMetadataInconsistencyError(ValueError):
    """
    Raised when there is an inconsistency between a dataset and the metadata
    """

    def __init__(
        self,
        ds_key: str,
        ds_key_value: str,
        metadata_key: str,
        metadata_key_value: str,
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        ds_key
            Key/identifier for the source of the value in the dataset

        ds_key_value
            Value of ``ds_key`` (often best to pre-format this so
            that the original variable name is included in the output)

        metadata_key
            Key/identifier for the source of the value in the metadata

        metadata_key_value
            Value of ``metadata_key`` (often best to pre-format this so
            that the original variable name is included in the output)
        """
        error_msg = (
            f"{ds_key} must match {metadata_key}. "
            f"{ds_key_value}, {metadata_key_value}"
        )

        super().__init__(error_msg)
