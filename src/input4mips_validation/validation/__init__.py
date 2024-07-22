"""
Validation module
"""

from __future__ import annotations

import subprocess
from functools import wraps
from pathlib import Path
from typing import Callable, Protocol, TypeVar

import iris
import xarray as xr
from loguru import logger
from typing_extensions import ParamSpec

from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.validation.cf_checker import check_with_cf_checker

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


class CatchErrorDecoratorLike(Protocol):
    """
    A callable like what we return from [`get_catch_error_decorator`][input4mips_validation.validation.get_catch_error_decorator]
    """  # noqa: E501

    def __call__(
        self, func_to_call: Callable[P, T], call_purpose: str
    ) -> Callable[P, T | None]:
        """
        Get wrapped version of a function
        """


def get_catch_error_decorator(
    error_container: list[tuple[str, Exception]],
) -> CatchErrorDecoratorLike:
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


def load_cvs_in_validation(cv_source: str | None) -> Input4MIPsCVs:
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
    infile: Path | str,
    cv_source: str | None,
    bnds_coord_indicator: str = "bnds",
) -> None:
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
    caught_errors: list[tuple[str, Exception]] = []
    catch_error = get_catch_error_decorator(caught_errors)

    # Basic loading - xarray
    ds_xr_load = catch_error(
        xr.load_dataset, call_purpose="Load data with `xr.load_dataset`"
    )(infile)

    # Basic loading - iris
    # cubes = catch_error(iris.load, call_purpose="Load data with `iris.load`")(infile)
    cubes = catch_error(iris.load, call_purpose="Load data with `iris.load`")(infile)
    if cubes is not None and len(cubes) == 1:
        catch_error(iris.load_cube, call_purpose="Load data with `iris.load_cube`")(
            infile
        )

    if ds_xr_load is None:
        logger.error("Not running cf-checker, file wouldn't load with xarray")

    else:
        # CF-checker
        catch_error(check_with_cf_checker, call_purpose="Check data with cf-checker")(
            infile, ds=ds_xr_load
        )

    # Check we can load CVs, we need them for the following steps
    cvs = catch_error(
        load_cvs_in_validation,
        call_purpose="Load controlled vocabularies to use during validation",
    )(cv_source)

    # TODO: Check that the data, metadata and CVs are all consistent
    # ds_careful_load = from_iris_cubes(
    #   cubes, bnds_coord_indicator=bnds_coord_indicator
    # )
    # catch_error(
    #     validate_ds,
    #     call_purpose="Check the dataset's data and metadata",
    # )(ds_careful_load, cvs=cvs)

    # Check that the filename and metadata are consistent
    # Checking of the directory and metadata is only done in validate_tree

    if cvs is None:
        logger.error("Skipping checks of CV consistency because cvs loading failed")

    else:
        # TODO: check consistency with CVs
        pass

    if caught_errors:
        logger.info("Validation failed")
        raise InvalidFileError(filepath=infile, error_container=caught_errors)

    logger.info("Validation passed")
