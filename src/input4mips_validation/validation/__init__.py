"""
Validation module
"""

from __future__ import annotations

import subprocess
from functools import partial, wraps
from pathlib import Path
from typing import Callable, TypeVar

from loguru import logger
from typing_extensions import ParamSpec

from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.database import Input4MIPsDatabaseEntryFile

P = ParamSpec("P")
T = TypeVar("T")


class InvalidFileError(ValueError):
    """
    Raised when a file does not pass all of the validation
    """

    def __init__(
        self,
        filepath: Path | str,
        error_container: list[tuple[str, Exception]],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        filepath
            The filepath we tried to validate

        error_container
            The thing which was being done
            and the error which was caught
            while validating the file.
        """
        # Not clear how input could be further validated hence noqa
        ncdump_loc = subprocess.check_output(["/usr/bin/which", "ncdump"]).strip()  # noqa: S603
        # Not clear how input could be further validated hence noqa
        file_ncdump_h = subprocess.check_output(
            [ncdump_loc, "-h", str(filepath)]  # noqa: S603
        ).decode()

        error_msgs: list[str] = []
        for error in error_container:
            process, exc = error
            # formatted_exc = "\n".join(traceback.format_exception(exc))
            formatted_exc = str(exc)
            error_msgs.append(f"{process} failed. Exception: {formatted_exc}")

        error_msgs_str = "\n\n".join(error_msgs)

        error_msg = (
            f"Failed to validate {filepath=}\n"
            f"File's `ncdump -h` output:\n\n{file_ncdump_h}\n\n"
            "Caught error messages (see log messages for full details):\n\n"
            f"{error_msgs_str}"
        )

        super().__init__(error_msg)


def get_catch_error_decorator(
    error_container: list[tuple[str, Exception]],
) -> Callable[[Callable[P, T]], Callable[P, T | None]]:
    """
    Get a decorator which can be used to collect errors without stopping the program

    Parameters
    ----------
    error_container
        The list in which to store the things being run and the caught errors

    Returns
    -------
        Decorator which can be used to collect errors
        that occur while calling callables.
    """

    def catch_error_decorator(
        func_to_call: Callable[P, T], call_purpose: str
    ) -> Callable[P, T | None]:
        """
        Decorate a callable such that any raised errors are caught

        This allows the program to keep running even if errors occur.

        If the function raises no error,
        a confirmation that it ran successfully is logged.

        Parameters
        ----------
        func_to_call
            Function to call

        call_purpose
            A description of the purpose of the call.
            This helps us create clearer error messages for the steps which failed.

        Returns
        -------
            Decorated function
        """

        @wraps(func_to_call)
        def decorated(*args: P.args, **kwargs: P.kwargs) -> T | None:
            try:
                res = func_to_call(*args, **kwargs)

            except Exception as exc:
                logger.exception(f"{call_purpose} raised an error")
                error_container.append((call_purpose, exc))
                return None

            logger.info(f"{call_purpose} ran without error")

            return res

        return decorated

    return catch_error_decorator


def load_cvs_here(cv_source: str) -> Input4MIPsCVs:
    """
    Load the controlled vocabularies (CVs)

    For full details on options for loading CVs,
    see {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading`.

    Parameters
    ----------
    cv_source
        Source from which to load the CVs

    Returns
    -------
        Loaded CVs
    """
    raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
    logger.debug(f"{raw_cvs_loader=}")
    cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

    return cvs


def validate_file(
    infile: Path | str, cv_source: str | None, bnds_coord_indicator: str = "bnds"
) -> Input4MIPsDatabaseEntryFile:
    """
    Validate a file

    This checks that the file can be loaded with standard libraries
    and passes metadata and data checks.

    Parameters
    ----------
    infile
        Path to the file to validate

    cv_source
        Source from which to load the CVs

        For full details on options for loading CVs,
        see {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading`.

    bnds_coord_indicator
        String that indicates that a variable is a bounds co-ordinate

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    Returns
    -------
        The file's corresponding database entry.

    Raises
    ------
    InvalidFileError
        The file does not pass all of the validation.
    """
    logger.info(f"Validating {infile}")
    caught_errors = []
    catch_error = get_catch_error_decorator(caught_errors)

    # Basic loading
    # ds_xr_load = catch_error(
    #     xr.load_dataset, call_purpose="Load data with `xr.load_dataset`"
    # )(infile)

    # cubes = catch_error(iris.load, call_purpose="Load data with `iris.load`")(infile)
    # if ds_xr_load.attrs["variable_id"] != "multiple":
    #     catch_error(iris.load_cube, call_purpose="Load data with `iris.load_cube`")(
    #         infile
    #     )

    # Check we can load CVs, we need them for the following steps
    cvs = catch_error(
        load_cvs_here,
        call_purpose="Load controlled vocabularies to use during validation",
    )(cv_source)

    # Check we can create a database entry
    database_entry = catch_error(
        partial(Input4MIPsDatabaseEntryFile.from_file, cvs=cvs),
        call_purpose="Create input4MIPs database entry for the file",
    )(infile)

    # Check that the data, metadata and CVs are all consistent
    # # Convert with ncdata as it is generally better at this
    # ds_careful_load = ncdata.iris_xarray.cubes_to_xarray(cubes)
    # # Guess that everything which has "bnds" in it is a co-ordinate.
    # # This is definitely a pain point when loading data from iris written.
    # # TODO: issue in [ncdata](https://github.com/pp-mo/ncdata)
    # # to see whether a true expert has any ideas.
    # bnds_guess = [v for v in ds_careful_load.data_vars if bnds_coord_indicator in v]
    # ds_careful_load = ds_careful_load.set_coords(bnds_guess)
    #
    # catch_error(
    #     validate_ds,
    #     call_purpose="Check the dataset's data and metadata",
    # )(ds_careful_load, cvs=cvs)

    # CF-checker
    # catch_error(check_with_cf_checker, call_purpose="Check data with cf-checker")(
    #     infile, ds=ds_xr_load
    # )

    if caught_errors:
        logger.info("Validation failed")
        raise InvalidFileError(filepath=infile, error_container=caught_errors)

    else:
        logger.info("Validation passed")

    return database_entry
