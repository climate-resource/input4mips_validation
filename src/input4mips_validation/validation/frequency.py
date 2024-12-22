"""
Validation of the `frequency` attribute
"""

from __future__ import annotations

import xarray as xr

from input4mips_validation.inference.from_data import (
    BoundsInfo,
    FrequencyMetadataKeys,
    infer_frequency,
)


def validate_frequency(
    frequency: str,
    ds: xr.Dataset,
    frequency_metadata_keys: FrequencyMetadataKeys = FrequencyMetadataKeys(),
    bounds_info: BoundsInfo = BoundsInfo(),
) -> None:
    """
    Validate the frequency value

    Parameters
    ----------
    frequency
        Frequency value to validate.

    ds
        Dataset to which the frequency metadata applies.

    frequency_metadata_keys
        Metadata definitions for frequency information

    bounds_info
        Metadata definitions for bounds handling

    Raises
    ------
    ValueError
        `frequency`'s value is incorrect
    """
    try:
        expected_frequency = infer_frequency(
            ds=ds,
            no_time_axis_frequency=frequency_metadata_keys.no_time_axis_frequency,
            time_bounds=bounds_info.time_bounds,
            bounds_dim=bounds_info.bounds_dim,
            bounds_dim_lower_val=bounds_info.bounds_dim_lower_val,
            bounds_dim_upper_val=bounds_info.bounds_dim_upper_val,
        )
    except NotImplementedError as exc:
        msg = f"The expected `frequency` attribute value could not be obtained. {exc}"
        raise NotImplementedError(msg) from exc

    if frequency != expected_frequency:
        msg = (
            "Given the time axis in the data, "
            f"the frequency attribute must be {expected_frequency!r}. "
            f"Received {frequency=!r}."
            f"{bounds_info=}. {ds=}"
        )
        raise ValueError(msg)
