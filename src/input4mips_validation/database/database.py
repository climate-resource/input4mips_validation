"""
Data model of our input4MIPs database
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import TYPE_CHECKING, Union

import cftime
import numpy as np
import pandas as pd
import xarray as xr
from attrs import define, fields

from input4mips_validation.database.raw import Input4MIPsDatabaseEntryFileRaw
from input4mips_validation.inference.from_data import create_time_range
from input4mips_validation.xarray_helpers.time import xr_time_min_max_to_single_value

if TYPE_CHECKING:
    from input4mips_validation.cvs import Input4MIPsCVs


@define
class Input4MIPsDatabaseEntryFile(Input4MIPsDatabaseEntryFileRaw):
    """
    Data model for a file entry in the input4MIPs database
    """

    @classmethod
    def from_file(  # noqa: PLR0913
        cls,
        file: Path,
        cvs: Input4MIPsCVs,
        frequency_metadata_key: str = "frequency",
        no_time_axis_frequency: str = "fx",
        time_dimension: str = "time",
    ) -> Input4MIPsDatabaseEntryFile:
        """
        Initialise based on a file

        Parameters
        ----------
        file
            File from which to extract data to create the database entry

        cvs
            Controlled vocabularies that were used when writing the file

        frequency_metadata_key
            The key in the data's metadata
            which points to information about the data's frequency.

        no_time_axis_frequency
            The value of "frequency" in the metadata which indicates
            that the file has no time axis i.e. is fixed in time.


        time_dimension
            Time dimension of `ds`

        Returns
        -------
            Initialised database entry
        """
        ds = xr.load_dataset(file)
        # Having to re-infer all of this is silly,
        # would be much simpler if all data was just in the file.
        metadata_attributes: dict[str, Union[str, None]] = ds.attrs

        metadata_data: dict[str, Union[str, None]] = {}

        frequency = metadata_attributes[frequency_metadata_key]
        if frequency is not None and frequency != no_time_axis_frequency:
            # Technically, this should probably use the bounds...
            time_start = xr_time_min_max_to_single_value(ds[time_dimension].min())
            time_end = xr_time_min_max_to_single_value(ds[time_dimension].max())

            md_datetime_start: Union[str, None] = format_datetime_for_db(time_start)
            md_datetime_end: Union[str, None] = format_datetime_for_db(time_end)

            md_datetime_time_range: Union[str, None] = create_time_range(
                time_start=time_start,
                time_end=time_end,
                ds_frequency=frequency,
            )

        else:
            md_datetime_start = None
            md_datetime_end = None
            md_datetime_time_range = None

        metadata_data["datetime_start"] = md_datetime_start
        metadata_data["datetime_end"] = md_datetime_end
        metadata_data["time_range"] = md_datetime_time_range

        metadata_directories_all = cvs.DRS.extract_metadata_from_path(file.parent)
        # Only get metadata from directories/files that we don't have elsewhere.
        # Reason: the values in the filepath have special characters removed,
        # so may not be correct if used for direct inference.
        metadata_directories_keys_to_use = (
            set(metadata_directories_all.keys())
            .difference(set(metadata_attributes.keys()))
            .difference(set(metadata_data.keys()))
        )
        metadata_directories = {
            k: metadata_directories_all[k] for k in metadata_directories_keys_to_use
        }

        all_metadata: dict[str, Union[str, None]] = {}
        for md in (metadata_attributes, metadata_data, metadata_directories):
            keys_to_check = md.keys() & all_metadata
            for ktc in keys_to_check:
                if all_metadata[ktc] != md[ktc]:
                    msg = f"Value clash for {ktc}. {all_metadata[ktc]=}, {md[ktc]=}"
                    raise AssertionError(msg)

            all_metadata = all_metadata | md

        # Make sure we only pass metadata that is actully of interest to the database
        cls_fields = [v.name for v in fields(cls)]
        init_kwargs = {k: v for k, v in all_metadata.items() if k in cls_fields}

        return cls(**init_kwargs)  # type: ignore # mypy confused for some reason


def format_datetime_for_db(time: cftime.datetime | dt.datetime | np.datetime64) -> str:
    """
    Format a "datetime_*" value for storing in the database

    Parameters
    ----------
    time
        Time value to format

    Returns
    -------
        Formatted time value
    """
    if isinstance(time, np.datetime64):
        ts: cftime.datetime | dt.datetime | pd.Timestamp = pd.to_datetime(str(time))

    else:
        ts = time

    return f"{ts.isoformat()}Z"  # Z indicates timezone is UTC
