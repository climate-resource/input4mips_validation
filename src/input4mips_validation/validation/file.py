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
from input4mips_validation.logging import (
    LOG_LEVEL_INFO_FILE,
    LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
)
from input4mips_validation.validation.cf_checker import check_with_cf_checker
from input4mips_validation.validation.datasets_to_write_to_disk import (
    get_ds_to_write_to_disk_validation_result,
)
from input4mips_validation.validation.error_catching import (
    ValidationResultsStore,
)
from input4mips_validation.xarray_helpers.iris import ds_from_iris_cubes
from input4mips_validation.xarray_helpers.variables import (
    XRVariableHelper,
    XRVariableProcessorLike,
)


def get_validate_file_result(  # noqa: PLR0913
    infile: Path | str,
    cv_source: str | None = None,
    cvs: Input4MIPsCVs | None = None,
    xr_variable_processor: XRVariableProcessorLike = XRVariableHelper(),
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

    xr_variable_processor
        Helper to use for processing the variables in xarray objects.

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
            cubes,
            xr_variable_processor=xr_variable_processor,
        )
        vrs = get_ds_to_write_to_disk_validation_result(
            ds=ds_careful_load,
            out_path=Path(infile),
            cvs=cvs,
            vrs=vrs,
            xr_variable_processor=xr_variable_processor,
        )

    logger.log(
        LOG_LEVEL_INFO_FILE.name, f"Created validation results for file: {infile}"
    )
    return vrs
