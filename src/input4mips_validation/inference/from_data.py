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


def ds_is_climatology(ds: xr.Dataset, time_dimension: str) -> bool:
    """
    Determine whether a dataset represents a climatology or not

    Parameters
    ----------
    ds
        Dataset to check

    time_dimension
        The name of the time dimension in `ds`, if `ds` contains a time dimension

    Returns
    -------
    :
        Whether the dataset is a climatology or not
    """
    if time_dimension in ds:
        # As far as I can tell from the cf-conventions,
        # this is what defines whether something is a climatology or not.
        # See https://cfconventions.org/Data/cf-conventions/cf-conventions-1.12/cf-conventions.html#climatological-statistics
        #
        # > Intervals of climatological time
        # > are conceptually different from ordinary time intervals...
        # > To indicate this difference,
        # > a climatological time coordinate variable does not have a bounds attribute.
        # > Instead, it has a climatology attribute
        ds_is_climatology = "climatology" in ds[time_dimension].attrs
    else:
        ds_is_climatology = False

    return ds_is_climatology


def get_climatology_bounds(
    ds: xr.Dataset, time_dimension: str = "time"
) -> xr.DataArray:
    """
    Get the climatology bounds variable

    This should only be used after having first checked that `ds`
    is a climatology (
    using e.g.
    [`ds_is_climatology`][input4mips_validation.inference.from_data.ds_is_climatology]
    ).

    Parameters
    ----------
    ds
        Dataset

    time_dimension
        Time dimension in `ds`

    Returns
    -------
    :
        Climatology bounds variable
    """
    # Can do this with confidence as this is what the spec defines.
    # For further details, see comments in `ds_is_climatology`.
    climatology_bounds_var = ds[time_dimension].attrs["climatology"]
    climatology_bounds: xr.DataArray = ds[climatology_bounds_var]

    return climatology_bounds


def frequency_is_climatology(frequency: str) -> bool:
    """
    Check whether the frequency information indicates that the data is a climatology

    Parameters
    ----------
    frequency
        Frequency attribute value

    Returns
    -------
    :
        Whether the data represents a climatology or not
    """
    return frequency in {"monC"}


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
        climatology = ds_is_climatology(ds, time_dimension)

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
                    f"Inferred: {bounds_dim_l=}. "
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

            guesses = ("bounds", "bnds", "nv")
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
                    f"Guessed {guesses=}. "
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

    climatology = ds_is_climatology(ds, time_dimension)

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


def is_yearly_steps(
    step_start: xr.DataArray,
    step_end: xr.DataArray,
) -> bool:
    """
    Determine whether the steps are yearly

    Parameters
    ----------
    step_start
        Start of each step (e.g. start of each bound)

    step_end
        End of each step (e.g. end of each bound)

    Returns
    -------
    :
        `True` if the steps are yearly, otherwise `False`
    """
    month_diff = step_end.dt.month.values - step_start.dt.month.values
    year_diff = step_end.dt.year.values - step_start.dt.year.values

    is_yearly_steps = ((month_diff == 0) & (year_diff == 1)).all()

    return bool(is_yearly_steps)


def is_monthly_steps(
    step_start: xr.DataArray,
    step_end: xr.DataArray,
) -> bool:
    """
    Determine whether the steps are monthly

    Parameters
    ----------
    step_start
        Start of each step (e.g. start of each bound)

    step_end
        End of each step (e.g. end of each bound)

    Returns
    -------
    :
        `True` if the steps are monthly, otherwise `False`
    """
    # # Urgh this doesn't work because October 5 to October 14 1582 (inclusive)
    # # don't exist in the mixed Julian/Gregorian calendar,
    # # so you don't get the right number of days for October 1582
    # # if you do it like this.
    # ```
    # timestep_size = (step_end - step_start).dt.days
    #
    # MIN_DAYS_IN_MONTH = 28
    # MAX_DAYS_IN_MONTH = 31
    # is_monthly_steps = (
    #     (timestep_size >= MIN_DAYS_IN_MONTH)
    #     & (timestep_size <= MAX_DAYS_IN_MONTH)
    # ).all()
    # ```
    #
    # # Hence have to use the hack below instead.
    month_diff = step_end.dt.month.values - step_start.dt.month.values
    year_diff = step_end.dt.year.values - step_start.dt.year.values

    MONTH_DIFF_IF_END_OF_YEAR = -11
    is_monthly_steps = (
        (month_diff == 1)
        | ((month_diff == MONTH_DIFF_IF_END_OF_YEAR) & (year_diff == 1))
    ).all()

    return bool(is_monthly_steps)


def is_daily_steps(
    step_start: xr.DataArray,
    step_end: xr.DataArray,
) -> bool:
    """
    Determine whether the steps are daily

    Parameters
    ----------
    step_start
        Start of each step (e.g. start of each bound)

    step_end
        End of each step (e.g. end of each bound)

    Returns
    -------
    :
        `True` if the steps are daily, otherwise `False`
    """
    # Use compute to avoid any dask stupidity
    step_start = step_start.compute()
    step_end = step_end.compute()
    time_deltas = step_end - step_start

    return (time_deltas.dt.days == 1).all()


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
        step_start = ds[time_dimension].isel(time=slice(None, -1))
        step_end = ds[time_dimension].isel(time=slice(1, None))

    else:
        # Use compute to avoid any dask stupidity
        step_start = ds[time_bounds].sel({bounds_dim: bounds_dim_lower_val}).compute()
        step_end = ds[time_bounds].sel({bounds_dim: bounds_dim_upper_val}).compute()

    if is_yearly_steps(
        step_start=step_start,
        step_end=step_end,
    ):
        return "yr"

    if is_monthly_steps(
        step_start=step_start,
        step_end=step_end,
    ):
        return "mon"

    time_deltas = step_end - step_start
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
    frequency = ds.attrs[frequency_metadata_key]
    is_climatology = frequency_is_climatology(frequency)

    if frequency == no_time_axis_frequency:
        time_start: Union[cftime.datetime, dt.datetime, np.datetime64, None] = None
        time_end: Union[cftime.datetime, dt.datetime, np.datetime64, None] = None

    elif is_climatology:
        # Can do this with confidence as this is what the spec defines.
        # See comments in `ds_is_climatology`.
        climatology_bounds = get_climatology_bounds(ds, time_dimension=time_dimension)

        time_start = xr_time_min_max_to_single_value(climatology_bounds.min())
        time_end = xr_time_min_max_to_single_value(climatology_bounds.max())
        if isinstance(time_end, np.datetime64):
            raise TypeError(time_end)

        if frequency == "monC":
            # If first day of month,
            # roll back one day to reflect the fact that the bound is exclusive.
            if time_end.day == 1:
                time_end = time_end - dt.timedelta(days=1)

    else:
        time_start = xr_time_min_max_to_single_value(ds[time_dimension].min())
        time_end = xr_time_min_max_to_single_value(ds[time_dimension].max())

    return time_start, time_end


def create_time_range_for_filename(
    time_start: cftime.datetime | dt.datetime | np.datetime64,
    time_end: cftime.datetime | dt.datetime | np.datetime64,
    ds_frequency: str,
    start_end_separator: str = "-",
) -> str:
    """
    Create the time range information for the filename

    It is safest to use this function with the output from
    [`infer_time_start_time_end_for_filename`][input4mips_validation.inference.from_data.infer_time_start_time_end_for_filename]
    because that function correctly infers the start and end time from the data,
    even when the data represents a climatology.

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
    fd = partial(format_date_for_time_range, ds_frequency=ds_frequency)
    time_start_formatted = fd(time_start)
    time_end_formatted = fd(time_end)

    res = start_end_separator.join([time_start_formatted, time_end_formatted])

    if frequency_is_climatology(ds_frequency):
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
