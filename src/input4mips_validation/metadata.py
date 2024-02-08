"""
Metadata handling
"""
from __future__ import annotations

from attrs import define


@define
class Input4MIPsMetadata:
    """
    Input4MIPs metadata

    These are all required fields.
    """


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
