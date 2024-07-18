"""
Inference of values based on rules in or adjacent to the CVs
"""

from __future__ import annotations

import datetime as dt
from functools import partial

import cftime
import numpy as np
import pandas as pd
import xarray as xr

VARIABLE_DATASET_CATEGORY_MAP = {
    "tos": "SSTsAndSeaIce",
    "siconc": "SSTsAndSeaIce",
    "sftof": "SSTsAndSeaIce",
    "areacello": "SSTsAndSeaIce",
    "mole_fraction_of_carbon_dioxide_in_air": "GHGConcentrations",
    "mole_fraction_of_methane_in_air": "GHGConcentrations",
    "mole_fraction_of_nitrous_oxide_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc116_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc218_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc3110_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc4112_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc5114_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc6116_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc7118_in_air": "GHGConcentrations",
    "mole_fraction_of_pfc318_in_air": "GHGConcentrations",
    "mole_fraction_of_carbon_tetrachloride_in_air": "GHGConcentrations",
    "mole_fraction_of_carbon_tetrafluoride_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc11_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc113_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc114_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc115_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc12_in_air": "GHGConcentrations",
    "mole_fraction_of_dichloromethane_in_air": "GHGConcentrations",
    "mole_fraction_of_methyl_bromide_in_air": "GHGConcentrations",
    "mole_fraction_of_hcc140a_in_air": "GHGConcentrations",
    "mole_fraction_of_methyl_chloride_in_air": "GHGConcentrations",
    "mole_fraction_of_chloroform_in_air": "GHGConcentrations",
    "mole_fraction_of_halon1211_in_air": "GHGConcentrations",
    "mole_fraction_of_halon1301_in_air": "GHGConcentrations",
    "mole_fraction_of_halon2402_in_air": "GHGConcentrations",
    "mole_fraction_of_hcfc141b_in_air": "GHGConcentrations",
    "mole_fraction_of_hcfc142b_in_air": "GHGConcentrations",
    "mole_fraction_of_hcfc22_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc125_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc134a_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc143a_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc152a_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc227ea_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc23_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc236fa_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc245fa_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc32_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc365mfc_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc4310mee_in_air": "GHGConcentrations",
    "mole_fraction_of_nitrogen_trifluoride_in_air": "GHGConcentrations",
    "mole_fraction_of_sulfur_hexafluoride_in_air": "GHGConcentrations",
    "mole_fraction_of_sulfuryl_fluoride_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc11_eq_in_air": "GHGConcentrations",
    "mole_fraction_of_cfc12_eq_in_air": "GHGConcentrations",
    "mole_fraction_of_hfc134a_eq_in_air": "GHGConcentrations",
}
"""
Mapping from variable names to dataset category

The variable names are generally CF standard names
(i.e. can include underscores)
rather than CMIP data request names
(which are meant to have no underscores or other special characters).

TODO: move this into CVs rather than hard-coding here
"""

VARIABLE_REALM_MAP = {
    "tos": "ocean",
    "siconc": "seaIce",
    "sftof": "ocean",
    "areacello": "ocean",
    "mole_fraction_of_carbon_dioxide_in_air": "atmos",
    "mole_fraction_of_methane_in_air": "atmos",
    "mole_fraction_of_nitrous_oxide_in_air": "atmos",
    "mole_fraction_of_pfc116_in_air": "atmos",
    "mole_fraction_of_pfc218_in_air": "atmos",
    "mole_fraction_of_pfc3110_in_air": "atmos",
    "mole_fraction_of_pfc4112_in_air": "atmos",
    "mole_fraction_of_pfc5114_in_air": "atmos",
    "mole_fraction_of_pfc6116_in_air": "atmos",
    "mole_fraction_of_pfc7118_in_air": "atmos",
    "mole_fraction_of_pfc318_in_air": "atmos",
    "mole_fraction_of_carbon_tetrachloride_in_air": "atmos",
    "mole_fraction_of_carbon_tetrafluoride_in_air": "atmos",
    "mole_fraction_of_cfc11_in_air": "atmos",
    "mole_fraction_of_cfc113_in_air": "atmos",
    "mole_fraction_of_cfc114_in_air": "atmos",
    "mole_fraction_of_cfc115_in_air": "atmos",
    "mole_fraction_of_cfc12_in_air": "atmos",
    "mole_fraction_of_dichloromethane_in_air": "atmos",
    "mole_fraction_of_methyl_bromide_in_air": "atmos",
    "mole_fraction_of_hcc140a_in_air": "atmos",
    "mole_fraction_of_methyl_chloride_in_air": "atmos",
    "mole_fraction_of_chloroform_in_air": "atmos",
    "mole_fraction_of_halon1211_in_air": "atmos",
    "mole_fraction_of_halon1301_in_air": "atmos",
    "mole_fraction_of_halon2402_in_air": "atmos",
    "mole_fraction_of_hcfc141b_in_air": "atmos",
    "mole_fraction_of_hcfc142b_in_air": "atmos",
    "mole_fraction_of_hcfc22_in_air": "atmos",
    "mole_fraction_of_hfc125_in_air": "atmos",
    "mole_fraction_of_hfc134a_in_air": "atmos",
    "mole_fraction_of_hfc143a_in_air": "atmos",
    "mole_fraction_of_hfc152a_in_air": "atmos",
    "mole_fraction_of_hfc227ea_in_air": "atmos",
    "mole_fraction_of_hfc23_in_air": "atmos",
    "mole_fraction_of_hfc236fa_in_air": "atmos",
    "mole_fraction_of_hfc245fa_in_air": "atmos",
    "mole_fraction_of_hfc32_in_air": "atmos",
    "mole_fraction_of_hfc365mfc_in_air": "atmos",
    "mole_fraction_of_hfc4310mee_in_air": "atmos",
    "mole_fraction_of_nitrogen_trifluoride_in_air": "atmos",
    "mole_fraction_of_sulfur_hexafluoride_in_air": "atmos",
    "mole_fraction_of_sulfuryl_fluoride_in_air": "atmos",
    "mole_fraction_of_cfc11_eq_in_air": "atmos",
    "mole_fraction_of_cfc12_eq_in_air": "atmos",
    "mole_fraction_of_hfc134a_eq_in_air": "atmos",
}
"""
Mapping from variable names to realm

The variable names are generally CF standard names
(i.e. can include underscores)
rather than CMIP data request names
(which are meant to have no underscores or other special characters).

TODO: move this into CVs rather than hard-coding here
"""


def infer_frequency(ds: xr.Dataset, time_bounds: str = "time_bounds") -> str:
    """
    Infer frequency

    TODO: work out if/where these rules are captured anywhere else

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
    # ```
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
    # ```
    # # Hence have to use the hack below instead.

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

    if ((month_diff == 0) & (year_diff == 1)).all():
        return "yr"

    raise NotImplementedError(ds)


def infer_time_range(
    ds: xr.Dataset, frequency: str, time_dimension: str, start_end_separator: str = "-"
) -> str:
    """
    Infer time range information

    Parameters
    ----------
    ds
        Dataset for which to infer the information

    frequency
        Frequency of ``ds``

    time_dimension
        Time dimension of ``ds``

    start_end_separator
        Separator between the start and end time information

    Returns
    -------
        Time range information
    """
    fd = partial(format_date_for_time_range, ds_frequency=frequency)
    return start_end_separator.join(
        [fd(t.values) for t in [ds[time_dimension].min(), ds[time_dimension].max()]]
    )


def format_date_for_time_range(
    date: cftime.datetime | dt.datetime | np.datetime64,
    ds_frequency: str,
) -> str:
    """
    Format date for providing time range information

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

    raise NotImplementedError(ds_frequency)
