"""
Constants related to controlled vocabularies
"""
from __future__ import annotations

import re

CREATION_DATE_REGEX: re.Pattern[str] = re.compile(
    r"^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z$"
)
"""
Regular expression that checks the creation date is formatted correctly
"""

UUID_REGEX: re.Pattern[str] = re.compile(
    r"^hdl:21.14100\/[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{12}$"
)
"""
Regular expression that checks the creation date is formatted correctly
"""
