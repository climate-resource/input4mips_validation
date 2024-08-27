"""
Validation of a tree of files
"""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path

import tqdm
import xarray as xr
from loguru import logger

from input4mips_validation.cvs import Input4MIPsCVs, load_cvs
from input4mips_validation.deprecation import raise_deprecation_warning
from input4mips_validation.exceptions import NonUniqueError
from input4mips_validation.validation.error_catching import get_catch_error_decorator
from input4mips_validation.validation.exceptions import (
    InvalidFileError,
    InvalidTreeError,
)
from input4mips_validation.validation.file import validate_file


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
    tracking_ids = [
        xr.open_dataset(f, use_cftime=True).attrs["tracking_id"] for f in files
    ]
    if len(set(tracking_ids)) != len(files):
        raise NonUniqueError(
            description="Tracking IDs for all files should be unique",
            values=tracking_ids,
        )


def validate_tree(  # noqa: PLR0913
    root: Path,
    cv_source: str | None,
    cvs: Input4MIPsCVs | None = None,
    bnds_coord_indicator: str = "bnds",
    frequency_metadata_key: str = "frequency",
    no_time_axis_frequency: str = "fx",
    time_dimension: str = "time",
    rglob_input: str = "*.nc",
    allow_cf_checker_warnings: bool = False,
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

    frequency_metadata_key
        The key in the data's metadata
        which points to information about the data's frequency

    no_time_axis_frequency
        The value of `frequency_metadata_key` in the metadata which indicates
        that the file has no time axis i.e. is fixed in time.

    time_dimension
        The time dimension of the data

    rglob_input
        String to use when applying [Path.rglob](https://docs.python.org/3/library/pathlib.html#pathlib.Path.rglob)
        to find input files.

        This helps us only select relevant files to check.

    allow_cf_checker_warnings
        Should warnings from the CF-checker be allowed?

        In otherwise, is a file allowed to pass validation,
        even if there are warnings from the CF-checker?

    Raises
    ------
    InvalidTreeError
        The tree does not pass all of the validation.
    """
    raise_deprecation_warning("validate_tree", removed_in="0.14.0")

    logger.info(f"Validating the tree with root {root}")
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

    all_files = [v for v in root.rglob(rglob_input) if v.is_file()]
    failed_files_l = []

    def validate_file_h(file: Path) -> None:
        try:
            validate_file(
                file,
                cvs=cvs,
                bnds_coord_indicator=bnds_coord_indicator,
                allow_cf_checker_warnings=allow_cf_checker_warnings,
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

        logger.error(
            f"{len(failed_files_l)} out of {len(all_files)} "
            f"{'files' if len(all_files) > 1 else 'file'} failed validation "
            f"for the tree with root {root}",
        )

        raise InvalidTreeError(root=root, error_container=caught_errors)

    logger.success(f"Validation passed for the tree with root {root}")
