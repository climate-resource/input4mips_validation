"""
Helpers for determining what is and isn't a variable
"""

from __future__ import annotations

from typing import Protocol

import xarray as xr
from attrs import define


class XRVariableProcessorLike(Protocol):
    """
    Interface for helpers for processing the variables in an xarray object

    This is required because the rules for handling bounds variables
    compared to data variables are not uniformly applied in xarray.
    There are CF-rules, but these are not applied consistently in xarray
    hence we use this instead.
    We would use https://github.com/xarray-contrib/cf-xarray,
    but that just hard-codes the name "bounds",
    which doesn't work when the variable is saved as "bnds",
    which seems to be the case when we save with e.g. iris.
    """

    def get_ds_bounds_variables(
        self,
        ds: xr.Dataset,
    ) -> tuple[str, ...]:
        """
        Get the bounds variables in a dataset

        Parameters
        ----------
        ds
            Dataset to check

        Returns
        -------
        :
            Bounds variables in the dataset.
        """

    def get_ds_climatology_bounds_variables(
        self,
        ds: xr.Dataset,
    ) -> tuple[str, ...]:
        """
        Get the climatology bounds variables in a dataset

        Parameters
        ----------
        ds
            Dataset to check

        Returns
        -------
        :
            Climatology bounds variables in the dataset.
        """

    def get_ds_variables(
        self,
        ds: xr.Dataset,
    ) -> tuple[str, ...]:
        """
        Get the variables in a dataset

        Parameters
        ----------
        ds
            Dataset to check

        Returns
        -------
        :
            Variables in the dataset, excluding bounds variables.
        """


@define
class XRVariableHelper:
    """
    Helper for processing the variables in an xarray object

    This is required because the rules for handling bounds variables
    compared to data variables are not uniformly applied in xarray.
    """

    bounds_coord_indicators: tuple[str, ...] = ("bounds", "bnds")
    """
    Strings that show that the variable represents bounds

    If any of these strings is found in the variable's name,
    it is assumed that the variable is a bounds variable.
    """

    climatology_bounds_coord_indicators: tuple[str, ...] = ("climatology",)
    """
    Strings that show that the variable represents climatology bounds

    If any of these strings is found in the variable's name,
    it is assumed that the variable is a climatology bounds variable.
    """

    def get_ds_bounds_variables(
        self,
        ds: xr.Dataset,
    ) -> tuple[str, ...]:
        """
        Get the bounds variables in a dataset

        Parameters
        ----------
        ds
            Dataset to check

        Returns
        -------
        :
            Bounds variables in the dataset.
        """
        return tuple(
            str(v)
            for v in ds.data_vars
            if any(bci in str(v) for bci in self.bounds_coord_indicators)
        )

    def get_ds_climatology_bounds_variables(
        self,
        ds: xr.Dataset,
    ) -> tuple[str, ...]:
        """
        Get the climatology bounds variables in a dataset

        Parameters
        ----------
        ds
            Dataset to check

        Returns
        -------
        :
            Climatology bounds variables in the dataset.
        """
        return tuple(
            str(v)
            for v in ds.data_vars
            if any(
                clim_i in str(v) for clim_i in self.climatology_bounds_coord_indicators
            )
        )

    def get_ds_variables(
        self,
        ds: xr.Dataset,
    ) -> tuple[str, ...]:
        """
        Get the variables in a dataset

        Parameters
        ----------
        ds
            Dataset to check

        Returns
        -------
        :
            Variables in the dataset, excluding bounds, climatology
            and obviously non-data (e.g. string) variables.
        """
        bounds_vars = self.get_ds_bounds_variables(ds)
        climatology_vars = self.get_ds_climatology_bounds_variables(ds)
        # Must be a better way to do this
        str_vars = tuple(k for k, v in ds.data_vars.items() if str(v.dtype) == "object")

        return tuple(
            str(v)
            for v in ds.data_vars
            if v not in bounds_vars and v not in climatology_vars and v not in str_vars
        )
