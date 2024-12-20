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
from attrs import define
from loguru import logger

from input4mips_validation.serialisation import format_date_for_time_range
from input4mips_validation.xarray_helpers.time import xr_time_min_max_to_single_value


@define
class FrequencyMetadataKeys:
    """
    Definition of the keys used for frequency metadata

    We put this together for ease of explanation and conciseness.
    """

    frequency_metadata_key: str = "frequency"
    """
    The key in the data's metadata
    which points to information about the data's frequency
    """

    no_time_axis_frequency: str = "fx"
    """
    The value of `frequency_metadata_key` in the metadata which indicates
    that the file has no time axis i.e. is fixed in time.
    """


@define
class BoundsInfo:
    """
    Definition of the values used for bounds handling

    We put this together for ease of explanation and conciseness.
    """

    time_bounds: str = "time_bounds"
    """
    Name of the variable which represents the bounds of the time axis
    """

    bounds_dim: str = "bounds"
    """
    The name of the bounds dimension in the data
    """

    bounds_dim_lower_val: int = 0
    """
    Value of the lower bounds dimension, which allows us to select the lower bounds.
    """

    bounds_dim_upper_val: int = 1
    """
    Value of the upper bounds dimension, which allows us to select the upper bounds.
    """

    @classmethod
    def from_ds(cls, ds: xr.Dataset, time_dimension: str = "time") -> BoundsInfo:
        """
        Initialise from a dataset

        Parameters
        ----------
        ds
            Dataset from which to initialise
        time_dimension
            The name of the time dimension in the dataset

        Returns
        -------
        :
            Initialised class
        """
        if time_dimension in ds:
            climatology = "climatology" in ds[time_dimension].attrs
        else:
            climatology = False

        should_have_time_bounds = (time_dimension in ds) and (not climatology)

        if should_have_time_bounds:
            # Has to be like this according to CF-convention
            bounds_info_key = "bounds"
            time_bounds = ds[time_dimension].attrs[bounds_info_key]
            time_bounds_dims = ds[time_bounds].dims
            bounds_dim_l = [v for v in time_bounds_dims if v != time_dimension]
            if len(bounds_dim_l) != 1:
                msg = (
                    f"Expected to find just one non-time dimension for {time_bounds}. "
                    f"Derived: {bounds_dim_l=}. "
                    f"Original dimensions of {time_bounds}: {time_bounds_dims}"
                )
                raise AssertionError(msg)

            bounds_dim = bounds_dim_l[0]

        else:
            if climatology:
                logger.debug("climatology, guessing bounds info")
            else:
                logger.debug(
                    f"{time_dimension=} not in the dataset, guessing bounds info"
                )

            guesses = ("bounds", "bnds")
            for guess in guesses:
                if guess in ds.dims:
                    bounds_dim = guess
                    time_bounds = "not_used"
                    logger.debug(
                        f"Found {bounds_dim}, assuming that is the bounds variable"
                    )
                    break

            else:
                msg = (
                    "Could not guess which variable was the bounds variable. "
                    f"Tried {guesses=}. "
                    f"{ds=}."
                )
                raise AssertionError(msg)

        # Upper, lower
        bounds_dim_expected_size = 2
        if ds[bounds_dim].size != bounds_dim_expected_size:
            raise AssertionError(ds[bounds_dim].size)

        bounds_dim_upper_val = int(ds[bounds_dim].max().values.squeeze())
        bounds_dim_lower_val = int(ds[bounds_dim].min().values.squeeze())

        return cls(
            time_bounds=time_bounds,
            bounds_dim=bounds_dim,
            bounds_dim_lower_val=bounds_dim_lower_val,
            bounds_dim_upper_val=bounds_dim_upper_val,
        )


def infer_frequency(  # noqa: PLR0913
    ds: xr.Dataset,
    no_time_axis_frequency: str,
    time_dimension: str = "time",
    time_bounds: str = "time_bounds",
    bounds_dim: str = "bounds",
    bounds_dim_lower_val: int = 0,
    bounds_dim_upper_val: int = 1,
) -> str:
    """
    Infer frequency from data

    TODO: work out if/where these rules are captured anywhere else
    These resource are helpful, but I'm not sure if they spell out the rules exactly:

    - https://github.com/WCRP-CMIP/CMIP6_CVs/blob/main/CMIP6_frequency.json
    - https://wcrp-cmip.github.io/WGCM_Infrastructure_Panel/Papers/CMIP6_global_attributes_filenames_CVs_v6.2.7.pdf

    Parameters
    ----------
    ds
        Dataset

    no_time_axis_frequency
        Value to return if the data has no time axis i.e. is a fixed field.

    time_dimension
        Name of the expected time dimension in `ds`.

        If `time_dimension` is not in `ds`, we assume the data is a fixed field.

    time_bounds
        Variable assumed to contain time bounds information

    bounds_dim
        The name of the bounds dimension

    bounds_dim_lower_val
        Value of the lower bounds dimension, which allows us to select the lower bounds.

    bounds_dim_upper_val
        Value of the upper bounds dimension, which allows us to select the upper bounds.

    Returns
    -------
    :
        Inferred frequency
    """
    if time_dimension not in ds:
        logger.debug(f"{time_dimension=} not in {ds=}, assuming fixed field")
        # Fixed field
        return no_time_axis_frequency

    if "climatology" in ds[time_dimension].attrs:
        # This seems to be the only way to tell according to the convention
        logger.debug(
            f"{time_dimension} has a 'climatology' attribute, "
            "assuming we are looking at a climatology"
        )
        climatology = True

    else:
        climatology = False

    frequency_stem = get_frequency_label_stem(
        ds=ds,
        climatology=climatology,
        time_dimension=time_dimension,
        time_bounds=time_bounds,
        bounds_dim=bounds_dim,
        bounds_dim_lower_val=bounds_dim_lower_val,
        bounds_dim_upper_val=bounds_dim_upper_val,
    )

    if climatology:
        if frequency_stem == "mon":
            frequency_label = f"{frequency_stem}C"

        else:
            # Apparently 1hrCM is also a thing, not implemented (yet)
            msg = f"{climatology=} and {frequency_stem=}"
            raise NotImplementedError(msg)
    else:
        frequency_label = frequency_stem

    return frequency_label


def get_frequency_label_stem(  # noqa: PLR0913
    ds: xr.Dataset,
    climatology: bool,
    time_dimension: str,
    time_bounds: str,
    bounds_dim: str,
    bounds_dim_lower_val: int,
    bounds_dim_upper_val: int,
) -> str:
    """
    Get the frequency label's stem from data

    This is mainly intended for internal use,
    see [`infer_frequency`][input4mips_validation.inference.from_data.infer_frequency]
    instead.

    Parameters
    ----------
    ds
        Dataset

    climatology
        Does this dataset represent a climatology?

    time_dimension
        Name of the time dimension in `ds`.

    time_bounds
        Variable assumed to contain time bounds information

    bounds_dim
        The name of the bounds dimension

    bounds_dim_lower_val
        Value of the lower bounds dimension, which allows us to select the lower bounds.

    bounds_dim_upper_val
        Value of the upper bounds dimension, which allows us to select the upper bounds.

    Returns
    -------
    :
        Inferred frequency stem e.g. "mon", "yr".

        Climatology information is added in
        [`infer_frequency`][input4mips_validation.inference.from_data.infer_frequency].
    """
    if climatology:
        # Only have time to work with, no bounds
        helper_1 = ds[time_dimension].isel(time=slice(1, None))
        helper_2 = ds[time_dimension].isel(time=slice(None, -1))

        month_diff = helper_1.dt.month.values - helper_2.dt.month.values
        year_diff = helper_1.dt.year.values - helper_2.dt.year.values

        MONTH_DIFF_IF_END_OF_YEAR = -11
        if (
            (month_diff == 1)
            | ((month_diff == MONTH_DIFF_IF_END_OF_YEAR) & (year_diff == 1))
        ).all():
            return "mon"

    else:
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
        #     (timestep_size >= MIN_DAYS_IN_MONTH)
        #     & (timestep_size <= MAX_DAYS_IN_MONTH)
        # ).all():
        #     return "mon"
        # ```
        #
        # # Hence have to use the hack below instead.
        start_bounds = ds[time_bounds].sel({bounds_dim: bounds_dim_lower_val})
        end_bounds = ds[time_bounds].sel({bounds_dim: bounds_dim_upper_val})

        month_diff = end_bounds.dt.month - start_bounds.dt.month
        year_diff = end_bounds.dt.year - start_bounds.dt.year

        if ((month_diff == 0) & (year_diff == 1)).all():
            return "yr"

        MONTH_DIFF_IF_END_OF_YEAR = -11
        if (
            (month_diff == 1)
            | ((month_diff == MONTH_DIFF_IF_END_OF_YEAR) & (year_diff == 1))
        ).all():
            return "mon"

        time_deltas = end_bounds - start_bounds
        # This would not work across the Julian/Gregorian boundary
        # (Ideally, move fast paths earlier in the function...)
        if (time_deltas.dt.days == 1).all():
            return "day"

    raise NotImplementedError(ds)


def infer_time_start_time_end_for_filename(
    ds: xr.Dataset,
    frequency_metadata_key: str,
    no_time_axis_frequency: str,
    time_dimension: str,
) -> tuple[
    Union[cftime.datetime, dt.datetime, np.datetime64, None],
    Union[cftime.datetime, dt.datetime, np.datetime64, None],
]:
    """
    Infer start and end time of the data in a dataset for creating file names

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
    climatology_frequencies = {"monC"}
    frequency = ds.attrs[frequency_metadata_key]

    if frequency == no_time_axis_frequency:
        time_start: Union[cftime.datetime, dt.datetime, np.datetime64, None] = None
        time_end: Union[cftime.datetime, dt.datetime, np.datetime64, None] = None

    elif frequency in climatology_frequencies:
        climatology_bounds_var = ds[time_dimension].attrs["climatology"]
        climatology_bounds = ds[climatology_bounds_var]

        time_start = xr_time_min_max_to_single_value(climatology_bounds.min())
        time_end = xr_time_min_max_to_single_value(climatology_bounds.max())
        # If first day of month,
        # roll back one day to reflect the fact that the bound is exclusive
        if time_end.day == 1:
            time_end = time_end - dt.timedelta(days=1)

    else:
        time_start = xr_time_min_max_to_single_value(ds[time_dimension].min())
        time_end = xr_time_min_max_to_single_value(ds[time_dimension].max())

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
    :
        The time-range information,
        formatted correctly given the underlying dataset's frequency.
    """
    climatology_frequencies = {"monC"}
    fd = partial(format_date_for_time_range, ds_frequency=ds_frequency)
    time_start_formatted = fd(time_start)
    time_end_formatted = fd(time_end)

    res = start_end_separator.join([time_start_formatted, time_end_formatted])

    if ds_frequency in climatology_frequencies:
        res = f"{res}-clim"

    return res


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
