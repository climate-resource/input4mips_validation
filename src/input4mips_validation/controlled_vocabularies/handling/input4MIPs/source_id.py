"""
Data model for source IDs
"""
from __future__ import annotations

from attrs import define


@define
class SourceIDEntry:
    """A source ID entry"""

    source_id: str
    """Name/key of the source ID"""

    activity_id: str
    """Activity ID the source relates to"""
    # TODO: add validation from activity ID JSON

    contact: str
    """Email addresses to contact in case of questions"""
    # TODO: add email validation

    further_info_url: str
    """URL where further information can be found"""
    # TODO: add validation

    institution: str
    """Institution with which this source should be associated"""

    institution_id: str
    """ID of the institution with which this source should be associated"""
    # TODO: add validation

    license: str
    """License information for this source"""
    # TODO: add validation

    mip_era: str
    """MIP era to which the source applies"""
    # TODO: add validation

    source_version: str
    """Version identifier for this source"""

    # TODO: work out if/how this is meant to differ from source_version
    version: str
    """Version identifier for this source"""
