"""
Validation of ORCID's
"""

from __future__ import annotations

from input4mips_validation.validation.regexp import (
    validate_matches_regexp,
)

REGEXP_CHECKER: str = r"[0-9]{4}-[0-9]{4}-[0-9]{4}-[0-9]{3}[0-9X]"
"""
Regular expression to use to check that the ORCID is correct.

Technically, this regular expression is not strict enough to check the ORCID
is actually valid.
However, this is a helpful first check
(if this fails, the ORCID is definitely wrong).

This constant is exposed for clarity.
If you change it, we do not guarantee correct performance of the codebase.
"""


def validate_orcid(orcid: str) -> None:
    """
    Validate that an ORCID is (probably) valid

    Using the information [here](https://support.orcid.org/hc/en-us/articles/360006897674-Structure-of-the-ORCID-Identifier#:~:text=ORCID%20iDs%20always%20require%20all,should%2Fcan%20not%20be%20shared.)
    to define valid.

    Parameters
    ----------
    orcid
        ORCID to validate

    Raises
    ------
    ValueError
        `orcid` is clearly not an ORCID
    """
    validate_matches_regexp(
        value=orcid,
        regexp_to_match=REGEXP_CHECKER,
    )
