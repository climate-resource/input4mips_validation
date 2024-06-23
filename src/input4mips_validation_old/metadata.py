"""
Metadata handling
"""
from __future__ import annotations

import attrs.validators as av
from attrs import asdict, define, field
from input4mips_validation.controlled_vocabularies.constants import (
    INCLUDES_EMAIL_REGEX,
)


@define
class Input4MIPsMetadata:
    """
    Input4MIPs metadata

    These are all required fields that cannot be inferred from the data.
    """

    activity_id: str = field(
        # TODO: fix this validator, should be based on source ID value
        # validator=make_attrs_validator_compatible_attribute_value_input(
        #     assert_attribute_being_set_matches_controlled_vocabulary
        # )
    )
    """Activity ID for the dataset"""

    contact: str = field(validator=av.matches_re(INCLUDES_EMAIL_REGEX))
    # TODO: add validation based on source ID too
    """Contact for the dataset"""

    mip_era: str = field(
        # TODO: fix this validator, should be based on source ID value
        # validator=make_attrs_validator_compatible_attribute_value_input(
        #     assert_attribute_being_set_matches_controlled_vocabulary
        # )
    )
    """MIP era for the dataset"""

    target_mip: str = field(
        # TODO: add validator back in once we've worked out the logic
        # validator=assert_target_mip_attribute_matches_controlled_vocabulary
    )
    """Target MIP for the dataset"""

    institution_id: str = field(
        # TODO: fix this validator, should be based on source ID value
        # validator=make_attrs_validator_compatible_attribute_value_input(
        #     assert_attribute_being_set_matches_controlled_vocabulary
        # )
    )
    """Institution ID for the dataset"""

    source_id: str = field(
        # TODO: turn this back on once we work out how it works
        # validator=make_attrs_validator_compatible_attribute_value_input(
        #     assert_attribute_being_set_matches_controlled_vocabulary
        #     # TODO: check if there are actually more restrictions on this e.g.
        #     # consistency with institution_id
        # )
    )
    """Source ID for the dataset"""

    grid_label: str = field(
        # TODO: turn this back on once we work out how it works
        # validator=make_attrs_validator_compatible_attribute_value_input(
        #     assert_attribute_being_set_matches_controlled_vocabulary
        #     # TODO: check if there are actually more restrictions on this e.g.
        #     # consistency with data
        #     # (such checks should then go into validate_ds_metadata_consistency)
        # )
    )
    """Grid label for the dataset"""

    def to_dataset_attributes(self) -> dict[str, str]:
        """
        Convert to a format that can be used as dataset attributes
        """
        out = {k: v for k, v in asdict(self).items()}

        return out


@define
class Input4MIPsMetadataOptional:
    """
    Input4MIPs optional metadata

    These are all optional fields.

    TODO: ask Paul what the logic is.
    For example, do people have free reign in optional metdata?
    Or, are there keys which are optional, but if they're there,
    they have to take certain values?
    Or something else?
    """

    comment: str | None = None
    """
    Comment(s) about the dataset

    This is a free-form field with no restriction other than being a string
    """

    def to_dataset_attributes(self) -> dict[str, str]:
        """
        Convert to a format that can be used as dataset attributes
        """
        out = {k: v for k, v in asdict(self).items() if v is not None}

        return out
