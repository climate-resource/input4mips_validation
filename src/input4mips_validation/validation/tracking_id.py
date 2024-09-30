"""
Validation of the `tracking_id` attribute
"""

from __future__ import annotations

import uuid

from input4mips_validation.validation.regexp import (
    DoesNotMatchRegexpError,
    validate_matches_regexp,
)

PREFIX: str = r"hdl:21.14100/"
"""
Prefix that we expect to start the tracking ID values.

This constant is exposed for clarity.
If you change it, we do not guarantee correct performance of the codebase.
"""

REGEXP_CHECKER: str = (
    r"hdl\:21\.14100\/[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12}"
)
"""
Regular expression to use to check that the tracking ID is correct.

Technically, this regular expression is not strict enough to check the UUID
is actually correctly formatted.
However, this is a helpful first check
(if this fails, the tracking ID is definitely wrong)
and ensures that the correct prefix is used.

This constant is exposed for clarity.
If you change it, we do not guarantee correct performance of the codebase.
"""


def validate_tracking_id(tracking_id: str) -> None:
    """
    Validate the tracking ID value

    Parameters
    ----------
    tracking_id
        Tracking ID value to validate

    Raises
    ------
    ValueError
        `tracking_id`'s value is not correctly formed
    """
    try:
        validate_matches_regexp(
            value=tracking_id,
            regexp_to_match=REGEXP_CHECKER,
        )

        tracking_id_uuid_part = tracking_id.split(PREFIX)[-1]
        uuid.UUID(tracking_id_uuid_part, version=4)

    except (DoesNotMatchRegexpError, ValueError) as exc:
        msg = (
            "The `tracking_id` attribute must start with the prefix 'hdl:21.14100/', "
            "followed by a version 4 universally unique identifier (UUID4). "
            "If it does this, it will match the following regular expression, "
            f"{REGEXP_CHECKER!r}. "
            f"Received {tracking_id=!r}. "
            "To see how to generate a correct tracking ID, "
            "see `input4mips_validation.io.generate_tracking_id`."
        )
        raise ValueError(msg) from exc
