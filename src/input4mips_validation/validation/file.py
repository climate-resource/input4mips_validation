"""
Validation of an individual file in isolation
"""

from __future__ import annotations

from pathlib import Path
from typing import Union

import iris
import xarray as xr
from loguru import logger

from input4mips_validation.cvs import Input4MIPsCVs, load_cvs
from input4mips_validation.deprecation import raise_deprecation_warning
from input4mips_validation.logging import (
    LOG_LEVEL_INFO_FILE,
    LOG_LEVEL_INFO_FILE_ERROR,
    LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
)
from input4mips_validation.validation.cf_checker import check_with_cf_checker
from input4mips_validation.validation.datasets_to_write_to_disk import (
    get_ds_to_write_to_disk_validation_result,
    validate_ds_to_write_to_disk,
)
from input4mips_validation.validation.error_catching import (
    ValidationResultsStore,
    get_catch_error_decorator,
)
from input4mips_validation.validation.exceptions import (
    InvalidFileError,
)
from input4mips_validation.xarray_helpers.iris import ds_from_iris_cubes


def validate_file(
    infile: Path | str,
    cv_source: str | None = None,
    cvs: Input4MIPsCVs | None = None,
    bnds_coord_indicator: str = "bnds",
    allow_cf_checker_warnings: bool = False,
) -> None:
    """
    Validate a file

    This checks that the file can be loaded with standard libraries
    and passes metadata and data checks.

    /// danger | Deprecated
    `validate_file` was deprecated in v0.12.0.
    It will be removed in v0.14.0.
    Please use [`get_validate_file_result`][input4mips_validation.validation.file.get_validate_file_result]
    instead because it provides greater control.
    ///

    Parameters
    ----------
    infile
        Path to the file to validate

    cv_source
        Source from which to load the CVs

        Only required if `cvs` is `None`.

        For full details on options for loading CVs,
        see
        [`get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader].

    cvs
        CVs to use when validating the file.

        If these are passed, then `cv_source` is ignored.

    bnds_coord_indicator
        String that indicates that a variable is a bounds co-ordinate

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    allow_cf_checker_warnings
        Should warnings from the CF-checker be allowed?

        In otherwise, is a file allowed to pass validation,
        even if there are warnings from the CF-checker?

    Raises
    ------
    InvalidFileError
        The file does not pass all of the validation.
    """  # noqa: E501
    raise_deprecation_warning(
        "validate_file",
        removed_in="0.14.0",
        use_instead=(
            "`get_validate_file_result`, "
            "then process the result to suit your use case"
        ),
    )

    logger.log(LOG_LEVEL_INFO_FILE.name, f"Validating {infile}")
    caught_errors: list[tuple[str, Exception]] = []
    checks_performed: list[str] = []
    catch_error = get_catch_error_decorator(caught_errors, checks_performed)

    if cvs is None:
        # Load CVs, we need them for the following steps
        cvs = catch_error(
            load_cvs,
            call_purpose="Load controlled vocabularies to use during validation",
        )(cv_source=cv_source)

    elif cv_source is not None:
        logger.warning(f"Using provided cvs instead of {cv_source=}")

    # Basic loading - xarray
    # # The below actually loads the data into memory.
    # # This can be very slow, hence turn off for now.
    # # TODO: discuss whether we want to have actual data loading checks or not.
    # ds_xr_load = catch_error(
    #     xr.load_dataset, call_purpose="Load data with `xr.load_dataset`"
    # )(infile)
    ds_xr_open = catch_error(
        xr.open_dataset, call_purpose="Open data with `xr.open_dataset`"
    )(infile, use_cftime=True)

    # Basic loading - iris
    cubes = catch_error(iris.load, call_purpose="Load data with `iris.load`")(infile)
    if cubes is not None and len(cubes) == 1:
        catch_error(iris.load_cube, call_purpose="Load data with `iris.load_cube`")(
            infile
        )

    if ds_xr_open is None:
        logger.error("Not running cf-checker, file wouldn't load with xarray")

    else:
        # CF-checker
        logger.log(
            LOG_LEVEL_INFO_INDIVIDUAL_CHECK.name,
            f"Using the cf-checker to check {infile}",
        )
        logger.debug(f"{allow_cf_checker_warnings=}")
        catch_error(check_with_cf_checker, call_purpose="Check data with cf-checker")(
            infile, ds=ds_xr_open, no_raise_if_only_warnings=allow_cf_checker_warnings
        )

    if cvs is None:
        logger.error("Skipping checks of CV consistency because cvs loading failed")

    elif cubes is None:
        logger.error("Skipping checks of CV consistency because cubes loading failed")

    else:
        # TODO: check consistency with CVs
        # TODO: Check that the data, metadata and CVs are all consistent
        # Check that the filename and metadata are consistent
        # Checking of the directory and metadata is only done in validate_tree
        ds_careful_load = ds_from_iris_cubes(
            cubes, bnds_coord_indicator=bnds_coord_indicator
        )
        catch_error(
            validate_ds_to_write_to_disk,
            call_purpose=(
                "Check that the dataset is formatted correctly "
                "for being written to disk"
            ),
        )(ds_careful_load, out_path=Path(infile), cvs=cvs)

    if caught_errors:
        n_caught_errors = len(caught_errors)
        logger.log(
            LOG_LEVEL_INFO_FILE_ERROR.name,
            f"{n_caught_errors} {'check' if n_caught_errors == 1 else 'checks'} "
            f"out of {len(checks_performed)} failed for file {infile}",
        )
        raise InvalidFileError(filepath=infile, error_container=caught_errors)

    logger.log(LOG_LEVEL_INFO_FILE.name, f"Validation passed for {infile}")


def get_validate_file_result(  # noqa: PLR0913
    infile: Path | str,
    cv_source: str | None = None,
    cvs: Input4MIPsCVs | None = None,
    bnds_coord_indicator: str = "bnds",
    allow_cf_checker_warnings: bool = False,
    vrs: Union[ValidationResultsStore, None] = None,
) -> ValidationResultsStore:
    """
    Get the result of validating a file

    This includes checks that the file can be loaded with standard libraries
    and passes metadata and data checks.

    Parameters
    ----------
    infile
        Path to the file to validate

    cv_source
        Source from which to load the CVs

        Only required if `cvs` is `None`.

        For full details on options for loading CVs,
        see
        [`get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader].

    cvs
        CVs to use when validating the file.

        If these are passed, then `cv_source` is ignored.

    bnds_coord_indicator
        String that indicates that a variable is a bounds co-ordinate

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    allow_cf_checker_warnings
        Should warnings from the CF-checker be allowed?

        In otherwise, is a file allowed to pass validation,
        even if there are warnings from the CF-checker?

    vrs
        The validation results store to use for the validation.

        If not supplied, we instantiate a new
        [`ValidationResultsStore`][input4mips_validation.validation.error_catching.ValidationResultsStore]
        instance.

    Returns
    -------
    :
        The validation results store.
    """
    logger.log(
        LOG_LEVEL_INFO_FILE.name, f"Creating validation results for file: {infile}"
    )

    if vrs is None:
        logger.debug("Instantiating a new `ValidationResultsStore`")
        vrs = ValidationResultsStore()

    if cvs is None:
        # Load CVs, we need them for the following steps
        cvs = vrs.wrap(
            load_cvs,
            func_description="Load controlled vocabularies to use during validation",
        )(cv_source=cv_source).result

    elif cv_source is not None:
        logger.warning(
            "Ignoring provided value for `cv_source` (using provided cvs instead)."
        )

    # Basic loading - xarray
    ds_xr_open = vrs.wrap(
        xr.open_dataset, func_description="Open data with `xr.open_dataset`"
    )(infile, use_cftime=True).result
    # # The below actually loads the data into memory.
    # # This can be very slow, hence turn off for now.
    # # TODO: discuss whether we want to have actual data loading checks or not.
    # ds_xr_load = vrs.wrap(
    #     xr.load_dataset, func_description="Load data with `xr.load_dataset`"
    # )(infile)

    # Basic loading - iris
    cubes = vrs.wrap(iris.load, func_description="Load data with `iris.load`")(
        infile
    ).result
    if cubes is not None and len(cubes) == 1:
        vrs.wrap(iris.load_cube, func_description="Load data with `iris.load_cube`")(
            infile
        )

    if ds_xr_open is None:
        logger.error("Not running cf-checker, file wouldn't load with xarray")

    else:
        # CF-checker
        logger.log(
            LOG_LEVEL_INFO_INDIVIDUAL_CHECK.name,
            f"Using the cf-checker to check {infile}",
        )
        logger.debug(f"{allow_cf_checker_warnings=}")
        vrs.wrap(check_with_cf_checker, func_description="Check data with cf-checker")(
            infile, ds=ds_xr_open, no_raise_if_only_warnings=allow_cf_checker_warnings
        )

    if cvs is None:
        logger.error("Skipping checks of CV consistency because cvs loading failed")

    elif cubes is None:
        logger.error("Skipping checks of CV consistency because cubes loading failed")

    else:
        # TODO: check consistency with CVs

        # TODO: Check that the data, metadata and CVs are all consistent
        # Check that the filename and metadata are consistent
        # Checking of the directory and metadata conssitency
        # can only be done in validate_tree.

        ds_careful_load = ds_from_iris_cubes(
            cubes, bnds_coord_indicator=bnds_coord_indicator
        )
        vrs = get_ds_to_write_to_disk_validation_result(
            ds=ds_careful_load,
            out_path=Path(infile),
            cvs=cvs,
            vrs=vrs,
        )

    logger.log(
        LOG_LEVEL_INFO_FILE.name, f"Created validation results for file: {infile}"
    )
    return vrs
