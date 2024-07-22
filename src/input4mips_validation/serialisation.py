"""
Serialisation of Python objects to standard data exchange formats
"""

from __future__ import annotations

import datetime as dt
import json
from typing import Any

import cattrs.preconf.json
import cftime
import numpy as np
import pandas as pd

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


def format_date_for_time_range(
    date: cftime.datetime | dt.datetime | np.datetime64,
    ds_frequency: str,
) -> str:
    """
    Format date for providing time-range information

    Parameters
    ----------
    date
        Date to format

    ds_frequency
        Frequency of the underlying dataset

    Returns
    -------
        Formatted date
    """
    if isinstance(date, np.datetime64):
        date_safe: cftime.datetime | dt.datetime = pd.to_datetime(str(date))

    else:
        date_safe = date

    if ds_frequency.startswith("mon"):
        return date_safe.strftime("%Y%m")

    if ds_frequency.startswith("yr"):
        return date_safe.strftime("%Y")

    if ds_frequency.startswith("day"):
        return date_safe.strftime("%Y%m%d")

    if ds_frequency.startswith("3hr"):
        return date_safe.strftime("%Y%m%d%H%M")

    raise NotImplementedError(ds_frequency)
