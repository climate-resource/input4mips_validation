"""
Helpers for writing datasets
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
    # TODO: ask Paul what this hdl business is about
    return "hdl:21.14100/" + str(uuid.uuid4())


def generate_creation_timestamp() -> str:
    """
    Generate creation timestamp, formatted as needed for input4MIPs files

    Returns
    -------
        Creation timestamp
    """
    ts = dt.datetime.now(dt.UTC).replace(
        microsecond=0  # remove microseconds from creation_timestamp
    )

    return f"{ts.isoformat()}Z"  # Z indicates timezone is UTC
