"""
Inference of metadata from data
"""

from __future__ import annotations

import datetime as dt
from functools import partial
from typing import Union

import cftime
import numpy as np
import xarray as xr

from input4mips_validation.serialisation import format_date_for_time_range
from input4mips_validation.xarray_helpers.time import xr_time_min_max_to_single_value


def infer_frequency(ds: xr.Dataset, time_bounds: str = "time_bounds") -> str:
    """
    Infer frequency from data

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
    if time_bounds not in ds:
        # Fixed field
        return "fx"

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

    start_years = ds[time_bounds].sel(bounds=0).dt.year
    start_months = ds[time_bounds].sel(bounds=0).dt.month
    end_years = ds[time_bounds].sel(bounds=1).dt.year
    end_months = ds[time_bounds].sel(bounds=1).dt.month

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


def infer_time_start_time_end(
    ds: xr.Dataset,
    frequency_metadata_key: str,
    no_time_axis_frequency: str,
    time_dimension: str,
) -> tuple[
    Union[cftime.datetime, dt.datetime, np.datetime64, None],
    Union[cftime.datetime, dt.datetime, np.datetime64, None],
]:
    """
    Infter start and end time of the data in a dataset

    Parameters
    ----------
    ds
        Dataset from which to infer start and end time

    frequency_metadata_key
        The key in the data's metadata
        which points to information about the data's frequency

    no_time_axis_frequency
        The value of `frequency_metadata_key` in the metadata which indicates
        that the file has no time axis i.e. is fixed in time.

    time_dimension
        The time dimension of the data

    Returns
    -------
    time_start :
        Start time of the data

    time_end :
        End time of the data
    """
    if ds.attrs[frequency_metadata_key] != no_time_axis_frequency:
        time_start: Union[
            cftime.datetime, dt.datetime, np.datetime64, None
        ] = xr_time_min_max_to_single_value(ds[time_dimension].min())
        time_end: Union[
            cftime.datetime, dt.datetime, np.datetime64, None
        ] = xr_time_min_max_to_single_value(ds[time_dimension].max())

    else:
        time_start = time_end = None

    return time_start, time_end


def create_time_range(
    time_start: cftime.datetime | dt.datetime | np.datetime64,
    time_end: cftime.datetime | dt.datetime | np.datetime64,
    ds_frequency: str,
    start_end_separator: str = "-",
) -> str:
    """
    Create the time range information

    Parameters
    ----------
    time_start
        The start time (of the underlying dataset)

    time_end
        The end time (of the underlying dataset)

    ds_frequency
        The frequency of the underlying dataset

    start_end_separator
        The string(s) to use to separate the start and end time.

    Returns
    -------
        The time-range information,
        formatted correctly given the underlying dataset's frequency.
    """
    fd = partial(format_date_for_time_range, ds_frequency=ds_frequency)
    time_start_formatted = fd(time_start)
    time_end_formatted = fd(time_end)

    return start_end_separator.join([time_start_formatted, time_end_formatted])


VARIABLE_DATASET_CATEGORY_MAP = {
    "tos": "SSTsAndSeaIce",
    "siconc": "SSTsAndSeaIce",
    "sftof": "SSTsAndSeaIce",
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
    "solar_irradiance_per_unit_wavelength": "solar",
    "solar_irradiance": "solar",
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
    "solar_irradiance_per_unit_wavelength": "atmos",
    "solar_irradiance": "atmos",
    "areacella": "atmos",
}
"""
Mapping from variable names to realm

The variable names are generally CF standard names
(i.e. can include underscores)
rather than CMIP data request names
(which are meant to have no underscores or other special characters).

TODO: move this into CVs rather than hard-coding here
"""
