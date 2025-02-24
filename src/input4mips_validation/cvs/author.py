"""
Definition of an author of a dataset.
"""

from __future__ import annotations

from attrs import field, frozen, validators

from input4mips_validation.attrs_helpers import (
    make_attrs_validator_compatible_single_input,
)
from input4mips_validation.validation.email import validate_email
from input4mips_validation.validation.orcid import validate_orcid


@frozen
class Author:
    """Author of a dataset"""

    name: str
    """Name of the author"""

    email: str = field(
        validator=[make_attrs_validator_compatible_single_input(validate_email)]
    )
    """
    Contact email for the author

    Needed in case of clarifications related to the dataset
    """

    affiliations: tuple[str, ...] = field(validator=[validators.instance_of(tuple)])
    """
    Affiliation(s) of the author

    There is no validation done on these strings, they are deliberately free-form
    to allow authors to write their affiliations as they wish.
    """

    orcid: str = field(
        validator=[make_attrs_validator_compatible_single_input(validate_orcid)]
    )
    """
    ORCID of the author
    """
