"""
Inference of metadata based on datasets and the controlled vocabulary
"""
from __future__ import annotations

import datetime as dt

import cftime
import xarray as xr

from input4mips_validation.controlled_vocabularies.constants import (
    VARIABLE_DATASET_MAP,
    VARIABLE_REALM_MAP,
)
from input4mips_validation.xarray_helpers import get_ds_variable


def infer_metadata(ds: xr.Dataset) -> dict[str, str]:
    """
    Infer metadata based on the dataset

    May have to take in other metadata too here, let's see

    Parameters
    ----------
    ds
        Dataset for which to infer metadata

    Returns
    -------
        Inferred metadata
    """
    return {
        "dataset_category": infer_dataset_category(ds),
        "frequency": infer_frequency(ds),
        "realm": infer_realm(ds),
        "variable_id": get_ds_variable(ds),
    }


def infer_dataset_category(ds: xr.Dataset) -> str:
    """
    Infer dataset_category

    Parameters
    ----------
    ds
        Dataset

    Returns
    -------
        Inferred dataset_category
    """
    return VARIABLE_DATASET_MAP[get_ds_variable(ds)]


def infer_frequency(ds: xr.Dataset, time_bounds: str = "time_bounds") -> str:
    """
    Infer frequency

    Parameters
    ----------
    ds
        Dataset

    time_bounds
        Variable assumed to contain time bounds information

    Returns
    -------
        Inferred frequency
    """
    # # Urgh this doesn't work because October 5 to October 15 1582
    # # don't exist in the mixed Julian/Gregorian calendar,
    # # so you don't get the right number of days for October 1582
    # # if you do it like this.
    # # Hence have to use the hack below instead.
    # timestep_size = (
    #     ds["time_bounds"].sel(bounds=1) - ds["time_bounds"].sel(bounds=0)
    # ).dt.days
    #
    # MIN_DAYS_IN_MONTH = 28
    # MAX_DAYS_IN_MONTH = 31
    # if (
    #     (timestep_size >= MIN_DAYS_IN_MONTH) & (timestep_size <= MAX_DAYS_IN_MONTH)
    # ).all():
    #     return "mon"

    start_years = ds["time_bounds"].sel(bounds=0).dt.year
    start_months = ds["time_bounds"].sel(bounds=0).dt.month
    end_years = ds["time_bounds"].sel(bounds=1).dt.year
    end_months = ds["time_bounds"].sel(bounds=1).dt.month

    month_diff = end_months - start_months
    year_diff = end_years - start_years
    MONTH_DIFF_IF_END_OF_YEAR = -11
    if (
        (month_diff == 1)
        | ((month_diff == MONTH_DIFF_IF_END_OF_YEAR) & (year_diff == 1))
    ).all():
        return "mon"

    raise NotImplementedError(ds)


def infer_realm(ds: xr.Dataset) -> str:
    """
    Infer realm

    Parameters
    ----------
    ds
        Dataset

    Returns
    -------
        Inferred realm
    """
    return VARIABLE_REALM_MAP[get_ds_variable(ds)]


def format_creation_date_into_version_string(creation_date: str) -> str:
    """
    Generate version string

    Parameters
    ----------
    creation_date
        Creation date

    Returns
    -------
        Version string
    """
    return dt.datetime.strptime(creation_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%Y%m%d")


def format_date_for_filename(
    date: cftime.datetime | dt.datetime,
    ds_frequency: str,
) -> str:
    """
    Format date for filepath

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
    if ds_frequency.startswith("mon"):
        return date.strftime("%Y%m")

    if ds_frequency.startswith("yr"):
        return date.strftime("%Y")

    raise NotImplementedError(ds_frequency)
