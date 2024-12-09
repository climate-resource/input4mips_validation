"""
Validation of datasets that we are writing to disk
"""

from __future__ import annotations

from collections.abc import Collection
from functools import partial
from pathlib import Path
from typing import Callable, Union

import xarray as xr

from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.validation.creation_date import validate_creation_date
from input4mips_validation.validation.error_catching import (
    MissingAttributeError,
    ValidationResultsStore,
)
from input4mips_validation.validation.tracking_id import validate_tracking_id
from input4mips_validation.validation.variable_id import validate_variable_id
from input4mips_validation.xarray_helpers.variables import get_ds_variables


class InvalidDatasetToWriteToDiskError(ValueError):
    """
    Raised when a dataset to write to disk does not pass all of the validation
    """

    def __init__(
        self,
        ds: xr.Dataset,
        error_container: list[tuple[str, Exception]],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        ds
            The dataset we tried to validate

        error_container
            The thing which was being done
            and the error which was caught
            while validating `ds`.
        """
        error_msgs: list[str] = []
        for error in error_container:
            process, exc = error
            formatted_exc = f"{type(exc).__name__}: {exc}"
            error_msgs.append(f"{process} failed. Exception: {formatted_exc}")

        error_msgs_str = "\n\n".join(error_msgs)

        error_msg = (
            f"Failed to validate {ds=}\n"
            "Caught error messages:\n\n"
            f"{error_msgs_str}"
        )

        super().__init__(error_msg)


def validate_attribute(
    ds: xr.Dataset, attribute: str, validation_function: Callable[[str], None]
) -> None:
    """
    Validate an attribute of the dataset

    A convenience function so we get sensible error messages,
    even if the attribute isn't provided by the dataset.

    Parameters
    ----------
    ds
        Dataset to validate

    attribute
        Attribute of `ds` to validate

    validation_function
        Functino to use to validate the value of `attribute`
    """
    if attribute not in ds.attrs:
        raise MissingAttributeError(attribute)

    attribute_value = str(ds.attrs[attribute])
    validation_function(attribute_value)


def get_ds_to_write_to_disk_validation_result(
    ds: xr.Dataset,
    out_path: Path,
    cvs: Input4MIPsCVs,
    vrs: Union[ValidationResultsStore, None] = None,
    bnds_coord_indicators: Collection[str] = {"bnds", "bounds"},
) -> ValidationResultsStore:
    """
    Get the result of validating a dataset that is going to be written to disk

    Parameters
    ----------
    ds
        Dataset to write to disk.
        May contain one or more variables.

    out_path
        Path in which to the dataset will be written

    cvs
        CVs to use to validate the dataset before writing

    vrs
        The validation results store to use for the validation.

        If not supplied, we instantiate a new
        [`ValidationResultsStore`][input4mips_validation.validation.error_catching.ValidationResultsStore]
        instance.

    bnds_coord_indicators
        Strings that indicate that a variable is a bounds variable

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).


    Returns
    -------
    :
        The validation results store.
    """
    if vrs is None:
        vrs = ValidationResultsStore()

    ds_variables = get_ds_variables(
        ds=ds,
        bnds_coord_indicators=bnds_coord_indicators,
    )
    for attribute, validation_function in (
        ("creation_date", validate_creation_date),
        ("tracking_id", validate_tracking_id),
        (
            "variable_id",
            partial(
                validate_variable_id,
                ds_variables=ds_variables,
            ),
        ),
    ):
        vrs.wrap(
            validate_attribute,
            func_description=f"Validate the {attribute!r} attribute",
        )(ds, attribute, validation_function)

    return vrs
