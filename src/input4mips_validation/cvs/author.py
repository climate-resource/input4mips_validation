"""
Definition of an author of a dataset.
"""

from __future__ import annotations

from attrs import frozen


@frozen
class Author:
    """Author of a dataset"""

    name: str
    """Name of the author"""

    # TODO: validation
    email: str
    """
    Contact email for the author

    Needed in case of clarifications related to the dataset
    """

    affiliations: tuple[str, ...]
    """
    Affiliation(s) of the author

    There is no validation done on these strings, they are deliberately free-form
    to allow authors to write their affiliations as they wish.
    """

    # TODO: validation
    orcid: str
    """
    ORCID of the author
    """
