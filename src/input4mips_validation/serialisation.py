"""
Serialisation of Python objects to standard data exchange formats
"""

from __future__ import annotations

import json
from typing import Any

import cattrs.preconf.json

converter_json = cattrs.preconf.json.make_converter()


def json_dumps_cv_style(inp: Any) -> str:
    """
    JSON dump raw data

    This ensures that consistent settings can be used for writing of all JSON data.

    Parameters
    ----------
    inp
        Raw data to dump to JSON

    Returns
    -------
        JSON form of the raw data, formatted using standard CV form
    """
    return json.dumps(
        inp,
        ensure_ascii=True,
        sort_keys=True,
        indent=4,
        separators=(",", ":"),
    )
