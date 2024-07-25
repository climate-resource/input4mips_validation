"""
Validation module
"""

from __future__ import annotations

import subprocess
from collections.abc import Collection
from functools import wraps
from pathlib import Path
from typing import Callable, Protocol, TypeVar

import iris
import tqdm
import xarray as xr
from loguru import logger
from typing_extensions import ParamSpec

from input4mips_validation.cli.logging import (
    LOG_LEVEL_INFO_FILE,
    LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
)
from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.exceptions import NonUniqueError
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
            formatted_exc = f"{type(exc).__name__}: {exc}"
            error_msgs.append(f"{process} failed. Exception: {formatted_exc}")

        error_msgs_str = "\n\n".join(error_msgs)

        error_msg = (
            f"Failed to validate {filepath=}\n"
            f"File's `ncdump -h` output:\n\n{file_ncdump_h}\n\n"
            "Caught error messages (see log messages for full details):\n\n"
            f"{error_msgs_str}"
        )

        super().__init__(error_msg)


class InvalidTreeError(ValueError):
    """
    Raised when a tree does not pass all of the validation
    """

    def __init__(
        self,
        root: Path | str,
        error_container: list[tuple[str, Exception]],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        root
            The root of the tree we tried to validate

        error_container
            The thing which was being done
            and the error which was caught
            while validating the file.
        """
        error_msgs: list[str] = []
        for error in error_container:
            process, exc = error
            formatted_exc = f"{type(exc).__name__}: {exc}"
            error_msgs.append(f"{process} failed. Exception: {formatted_exc}")

        error_msgs_str = "\n\n".join(error_msgs)

        error_msg = (
            f"Failed to validate {root=}\n"
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
    checks_performed_container: list[str],
) -> CatchErrorDecoratorLike:
    """
    Get a decorator which can be used to collect errors without stopping the program

    Parameters
    ----------
    error_container
        The list in which to store the things being run and the caught errors

    checks_performed_container
        List which stores the checks that were performed

    Returns
    -------
    :
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
        :
            Decorated function
        """

        @wraps(func_to_call)
        def decorated(*args: P.args, **kwargs: P.kwargs) -> T | None:
            try:
                checks_performed_container.append(call_purpose)
                res = func_to_call(*args, **kwargs)

            except Exception as exc:
                logger.log(
                    LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
                    f"{call_purpose} raised an error ({type(exc).__name__})",
                )
                error_container.append((call_purpose, exc))
                return None

            logger.log(
                LOG_LEVEL_INFO_INDIVIDUAL_CHECK, f"{call_purpose} ran without error"
            )

            return res

        return decorated

    return catch_error_decorator


def load_cvs_in_validation(cv_source: str | None) -> Input4MIPsCVs:
    """
    Load the controlled vocabularies (CVs)

    For full details on options for loading CVs,
    see
    [`get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader].

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
    cv_source: str | None = None,
    cvs: Input4MIPsCVs | None = None,
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

    Raises
    ------
    InvalidFileError
        The file does not pass all of the validation.
    """
    logger.log(LOG_LEVEL_INFO_FILE, f"Validating {infile}")
    caught_errors: list[tuple[str, Exception]] = []
    checks_performed: list[str] = []
    catch_error = get_catch_error_decorator(caught_errors, checks_performed)

    if cvs is None:
        # Load CVs, we need them for the following steps
        cvs = catch_error(
            load_cvs_in_validation,
            call_purpose="Load controlled vocabularies to use during validation",
        )(cv_source)

    elif cv_source is not None:
        logger.debug(f"Using provided cvs instead of {cv_source=}")

    # Basic loading - xarray
    # # The below actually loads the data into memory.
    # # This can be very slow, hence turn off for now.
    # # TODO: discuss whether we want to have actual data loading checks or not.
    # ds_xr_load = catch_error(
    #     xr.load_dataset, call_purpose="Load data with `xr.load_dataset`"
    # )(infile)
    ds_xr_open = catch_error(
        xr.open_dataset, call_purpose="Open data with `xr.open_dataset`"
    )(infile)

    # Basic loading - iris
    # cubes = catch_error(iris.load, call_purpose="Load data with `iris.load`")(infile)
    cubes = catch_error(iris.load, call_purpose="Load data with `iris.load`")(infile)
    if cubes is not None and len(cubes) == 1:
        catch_error(iris.load_cube, call_purpose="Load data with `iris.load_cube`")(
            infile
        )

    if ds_xr_open is None:
        logger.error("Not running cf-checker, file wouldn't open with xarray")

    else:
        # CF-checker
        catch_error(check_with_cf_checker, call_purpose="Check data with cf-checker")(
            infile, ds=ds_xr_open
        )

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
        n_caught_errors = len(caught_errors)
        logger.log(LOG_LEVEL_INFO_FILE, f"Validation of {infile} failed. ")
        logger.log(
            LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
            f"{n_caught_errors} {'check' if n_caught_errors == 1 else 'checks'} "
            f"out of {len(checks_performed)} failed",
        )
        raise InvalidFileError(filepath=infile, error_container=caught_errors)

    logger.log(LOG_LEVEL_INFO_FILE, f"Validation passed for {infile}")


def validate_tracking_ids_are_unique(files: Collection[Path]) -> None:
    """
    Validate that tracking IDs in all files are unique

    Parameters
    ----------
    files
        Files to check

    Raises
    ------
    NonUniqueError
        Not all the tracking IDs are unique
    """
    tracking_ids = [xr.open_dataset(f).attrs["tracking_id"] for f in files]
    if len(set(tracking_ids)) != len(files):
        raise NonUniqueError(
            description="Tracking IDs for all files should be unique",
            values=tracking_ids,
        )


def validate_tree(  # noqa: PLR0913
    root: Path,
    cv_source: str | None,
    bnds_coord_indicator: str = "bnds",
    frequency_metadata_key: str = "frequency",
    no_time_axis_frequency: str = "fx",
    time_dimension: str = "time",
    rglob_input: str = "*.nc",
) -> None:
    """
    Validate a (directory) tree

    This checks that:

    1. all files in the tree can be loaded with standard libraries
    1. all files in the tree pass metadata and data checks
    1. all files in the tree are correctly written
       according to the data reference syntax
    1. all references to external variables (like cell areas) can be resolved
    1. all files have a unique tracking ID

    Parameters
    ----------
    root
        Root of the tree to validate

    cv_source
        Source from which to load the CVs

        For full details on options for loading CVs,
        see
        [`get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader].

    bnds_coord_indicator
        String that indicates that a variable is a bounds co-ordinate

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    frequency_metadata_key
        The key in the data's metadata
        which points to information about the data's frequency

    no_time_axis_frequency
        The value of `frequency_metadata_key` in the metadata which indicates
        that the file has no time axis i.e. is fixed in time.

    time_dimension
        The time dimension of the data

    rglob_input
        Input to rglob.

        This helps us only select relevant files to check.

    Raises
    ------
    InvalidTreeError
        The tree does not pass all of the validation.
    """
    logger.info(f"Validating the tree with root {root}")
    caught_errors: list[tuple[str, Exception]] = []
    checks_performed: list[str] = []
    catch_error = get_catch_error_decorator(caught_errors, checks_performed)

    # Check we can load CVs, we need them for the following steps
    cvs = catch_error(
        load_cvs_in_validation,
        call_purpose="Load controlled vocabularies to use during validation",
    )(cv_source)

    all_files = [v for v in root.rglob(rglob_input) if v.is_file()]
    failed_files_l = []

    def validate_file_h(file: Path) -> None:
        try:
            validate_file(
                file,
                cvs=cvs,
                bnds_coord_indicator=bnds_coord_indicator,
            )
        except InvalidFileError:
            if file not in failed_files_l:
                failed_files_l.append(file)

            raise

    validate_file_with_catch = catch_error(
        validate_file_h, call_purpose="Validate individual file"
    )

    if cvs is None:
        logger.error("Skipping check of consistency with DRS because CVs did not load")

    else:

        def validate_file_written_according_to_drs_h(file: Path) -> None:
            try:
                cvs.DRS.validate_file_written_according_to_drs(
                    file,
                    frequency_metadata_key=frequency_metadata_key,
                    no_time_axis_frequency=no_time_axis_frequency,
                    time_dimension=time_dimension,
                )

            except Exception:
                if file not in failed_files_l:
                    failed_files_l.append(file)

                raise

        validate_file_written_according_to_drs = catch_error(
            validate_file_written_according_to_drs_h,
            call_purpose="Validate file is correctly written in the DRS",
        )

    for file in tqdm.tqdm(all_files, desc="Files to validate"):
        validate_file_with_catch(file)

        if cvs is not None:
            validate_file_written_according_to_drs(file)

        # TODO: check cross references in files to external variables

    catch_error(
        validate_tracking_ids_are_unique,
        call_purpose="Validate that tracking IDs in all files are unique",
    )(all_files)

    if caught_errors:
        # # TODO: dump this out in html that can be interrogated
        # failed_files = line_start.join([str(v) for v in failed_files_l])
        # The following would be fine as a start
        """
Failures:
<ol>
    <li>
        <details>
          <summary>filename</summary>
          <ol>
              <li>
                  <details>
                      <summary>error headline</summary>
                      Error full info
                  </details>
              </li>
          </ol>
        </details>
    </li>
</ol>
Passed:
<ol>
    <li>filename</li>
</ol>
        """

        logger.info(f"Validation failed for the tree with root {root}")
        logger.info(
            f"{len(failed_files_l)} out of {len(all_files)} "
            f"{'files' if len(all_files) > 1 else 'file'} failed validation"
        )

        raise InvalidTreeError(root=root, error_container=caught_errors)

    logger.info(f"Validation passed for the tree with root {root}")
