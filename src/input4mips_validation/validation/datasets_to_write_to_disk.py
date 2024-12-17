"""
Validation of datasets that we are writing to disk
"""

from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import Callable, Union

import xarray as xr

from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.validation.comment import validate_comment
from input4mips_validation.validation.creation_date import validate_creation_date
from input4mips_validation.validation.error_catching import (
    ValidationResultsStore,
)
from input4mips_validation.validation.exceptions import (
    MissingAttributeError,
)
from input4mips_validation.validation.external_variables import (
    validate_external_variables,
)
from input4mips_validation.validation.tracking_id import validate_tracking_id
from input4mips_validation.validation.variable_id import validate_variable_id
from input4mips_validation.xarray_helpers.variables import (
    XRVariableHelper,
    XRVariableProcessorLike,
)


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
        Function to use to validate the value of `attribute`

    Raises
    ------
    MissingAttributeError
        `attribute` is not in `ds`'s attributes
    """
    if attribute not in ds.attrs:
        raise MissingAttributeError(attribute)

    attribute_value = ds.attrs[attribute]
    validation_function(attribute_value)


def validate_attribute_that_depends_on_other_attribute(
    ds: xr.Dataset,
    attribute: str,
    attribute_dependent_on: str,
    validation_function: Callable[[str, str], None],
) -> None:
    """
    Validate an attribute of the dataset that depends on another attribute's value

    A convenience function so we get sensible error messages,
    even if one of the attributes isn't provided by the dataset.

    Parameters
    ----------
    ds
        Dataset to validate

    attribute
        Attribute of `ds` to validate

    attribute_dependent_on
        Attribute of `ds` that the value of `attribute` depends on

    validation_function
        Function to use to validate the value of `attribute`,
        given the value of `attribute_dependent_on`

    Raises
    ------
    MissingAttributeError
        `attribute` or `attribute_dependent_on` is not in `ds`'s attributes
    """
    if attribute not in ds.attrs:
        raise MissingAttributeError(attribute)

    if attribute_dependent_on not in ds.attrs:
        raise MissingAttributeError(attribute_dependent_on)

    attribute_value = ds.attrs[attribute]
    attribute_dependent_on_value = ds.attrs[attribute_dependent_on]
    validation_function(attribute_value, attribute_dependent_on_value)


def get_ds_to_write_to_disk_validation_result(
    ds: xr.Dataset,
    out_path: Path,
    cvs: Input4MIPsCVs,
    vrs: Union[ValidationResultsStore, None] = None,
    xr_variable_processor: XRVariableProcessorLike = XRVariableHelper(),
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

    xr_variable_processor
        Helper to use for processing the variables in xarray objects.

    Returns
    -------
    :
        The validation results store.
    """
    if vrs is None:
        vrs = ValidationResultsStore()

    # Metadata that can be validated standalone
    verification_standalone = (
        ("creation_date", validate_creation_date),
        ("tracking_id", validate_tracking_id),
    )
    verification_standalone_optional = (
        ("comment", validate_comment),
        # TODO: add verification of this to validate-tree.
        # That's where the real power would come in.
        ("external_variables", validate_external_variables),
    )

    # Metadata that depends on the data
    ds_variables = xr_variable_processor.get_ds_variables(
        ds=ds,
    )
    verification_based_on_data = (
        (
            "variable_id",
            partial(
                validate_variable_id,
                ds_variables=ds_variables,
            ),
        ),
    )

    # Metadata that has to be consistent with the CVs,
    # but is not defined by the CVs
    verification_must_be_in_cvs = (
        (
            "activity_id",
            cvs.validate_activity_id,
        ),
    )

    for attribute, validation_function in (
        *verification_standalone,
        *verification_based_on_data,
        *verification_must_be_in_cvs,
    ):
        vrs.wrap(
            validate_attribute,
            func_description=f"Validate the {attribute!r} attribute",
        )(ds, attribute, validation_function)

    # Optional attributes
    for attribute_optional, validation_function_optional in (
        *verification_standalone_optional,
    ):
        if attribute_optional in ds.attrs:
            vrs.wrap(
                validate_attribute,
                func_description=f"Validate the {attribute_optional!r} attribute",
            )(ds, attribute_optional, validation_function_optional)

    # Metadata that is defined by the combination of other metadata and the CVs
    verification_defined_by_cvs_and_other_metadata = (
        (
            "contact",
            "source_id",
            cvs.validate_contact,
        ),
        (
            "source_version",
            "source_id",
            cvs.validate_source_version,
        ),
    )
    for attribute, attribute_dependent_on, validation_function_dependents in (
        *verification_defined_by_cvs_and_other_metadata,
    ):
        vrs.wrap(
            validate_attribute_that_depends_on_other_attribute,
            func_description=f"Validate the {attribute!r} attribute",
        )(ds, attribute, attribute_dependent_on, validation_function_dependents)

    return vrs
