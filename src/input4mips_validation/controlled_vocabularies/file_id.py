"""
Tools for helping with file identification
"""
from __future__ import annotations

import datetime as dt
import uuid


def generate_tracking_id() -> str:
    """
    Generate tracking ID

    Returns
    -------
        Tracking ID
    """
    return "hdl:21.14100/" + str(uuid.uuid4())


def generate_creation_timestamp() -> str:
    """
    Generate creation timestamp

    Returns
    -------
        Creation timestamp
    """
    ts = dt.datetime.utcnow().replace(
        microsecond=0  # remove microseconds from creation_timestamp
    )

    return f"{ts.isoformat()}Z"  # Z indicates timezone is UTC
