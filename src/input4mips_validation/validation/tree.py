"""
Validation of a tree of files
"""

from __future__ import annotations

from collections.abc import Collection
from pathlib import Path

import tqdm
import xarray as xr
from attrs import define, field
from loguru import logger

from input4mips_validation.cvs import Input4MIPsCVs, load_cvs
from input4mips_validation.deprecation import raise_deprecation_warning
from input4mips_validation.exceptions import NonUniqueError
from input4mips_validation.validation.error_catching import (
    ValidationResult,
    ValidationResultsStore,
    get_catch_error_decorator,
)
from input4mips_validation.validation.exceptions import (
    InvalidFileError,
    InvalidTreeError,
)
from input4mips_validation.validation.file import (
    get_validate_file_result,
    validate_file,
)


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

    /// danger | Deprecated
    `validate_tree` was deprecated in v0.12.0.
    It will be removed in v0.14.0.
    Please use [`get_validate_tree_result`][input4mips_validation.validation.tree.get_validate_tree_result]
    instead because it provides greater control.
    ///

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
    """  # noqa: E501
    raise_deprecation_warning(
        "validate_tree",
        removed_in="0.14.0",
        use_instead=(
            "`get_validate_tree_result`, then process the result to suit your use case"
        ),
    )

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
        logger.error(
            f"{len(failed_files_l)} out of {len(all_files)} "
            f"{'files' if len(all_files) > 1 else 'file'} failed validation "
            f"for the tree with root {root}",
        )

        raise InvalidTreeError(root=root, error_container=caught_errors)

    logger.success(f"Validation passed for the tree with root {root}")


class TreeValidationResultsStoreError(ValueError):
    """
    Raised to signal that an error occured during validation

    Specifically, that a
    [`TreeValidationResultsStore`][input4mips_validation.validation.tree.TreeValidationResultsStore]
    object contains failed validation results.
    """

    def __init__(self, tvrs: TreeValidationResultsStore) -> None:
        """
        Initialise the error

        Parameters
        ----------
        tvrs
            The validation results store that contains failures.
        """
        error_msg_l: list[str] = [
            f"Tree root: {tvrs.tree_root!r}",
            (
                "General checks passing: "
                f"{tvrs.checks_summary_str(general=True, passing=True)}"
            ),
            (
                "General checks failing: "
                f"{tvrs.checks_summary_str(general=True, passing=False)}"
            ),
            (
                "Individual files passing: "
                f"{tvrs.checks_summary_str(general=False, passing=True)}"
            ),
            (
                "Individual files failing: "
                f"{tvrs.checks_summary_str(general=False, passing=False)}"
            ),
        ]

        general_checks_failing = tvrs.general_checks_failing
        if general_checks_failing:
            error_msg_l.append("")
            error_msg_l.append("Failing general checks details")
            for gcf in general_checks_failing:
                error_msg_l.append("")
                error_msg_l.append(
                    f"{gcf.description} ({type(gcf.exception).__name__})"
                )
                if gcf.exception_info is None:
                    msg = "Should have an exception here"
                    raise AssertionError(msg)

                error_msg_l.extend(gcf.exception_info.splitlines())

        files_failing = tvrs.files_failing
        if files_failing:
            error_msg_l.append("")
            error_msg_l.append("Failing individual checks details")
            for file_path in sorted(files_failing.keys()):
                error_msg_l.append("")
                error_msg_l.append(f"{file_path=!r}")

                for ifcf in files_failing[file_path].checks_failing:
                    error_msg_l.append(
                        f"{ifcf.description} ({type(ifcf.exception).__name__})"
                    )
                    if ifcf.exception_info is None:
                        msg = "Should have an exception here"
                        raise AssertionError(msg)

                    error_msg_l.extend(ifcf.exception_info.splitlines())

        error_msg = "\n".join(error_msg_l)

        super().__init__(error_msg)


@define
class TreeValidationResultsStore:
    """Store of the results from validating a (directory) tree"""

    tree_root: Path
    """Root of the tree being validated"""

    general_validation_results_store: ValidationResultsStore
    """Results of general validation steps"""

    file_validation_results_stores: dict[Path, ValidationResultsStore] = field(
        factory=dict
    )
    """Results of validation for each file"""

    @property
    def general_checks_passing(self) -> tuple[ValidationResult, ...]:
        """General checks in our store which passed"""
        return tuple(
            v
            for v in self.general_validation_results_store.validation_results
            if v.passed
        )

    @property
    def general_checks_failing(self) -> tuple[ValidationResult, ...]:
        """General checks in our store which failed"""
        return tuple(
            v
            for v in self.general_validation_results_store.validation_results
            if v.failed
        )

    @property
    def files_passing(self) -> dict[Path, ValidationResultsStore]:
        """Files in our store which passed validation"""
        return {
            k: v for k, v in self.file_validation_results_stores.items() if v.all_passed
        }

    @property
    def files_failing(self) -> dict[Path, ValidationResultsStore]:
        """Files in our store which failed validation"""
        return {
            k: v
            for k, v in self.file_validation_results_stores.items()
            if not v.all_passed
        }

    def to_html(self) -> str:
        """Generate an HTML representation of self"""
        res_l = [
            f"<h1>Tree validation results for {self.tree_root}</h1>",
            "<h2>General validation results</h2>",
            "",
            "<ul>",
            f"  <li>Passed: {self.checks_summary_str(general=True, passing=True)}</li>",
            (
                "  <li>Failed: "
                f"{self.checks_summary_str(general=True, passing=False)}</li>"
            ),
            "</ul>",
            "",
            "<h2>Individual file validation results</h2>",
            "<ul>",
            (
                "  <li>Passing files: "
                f"{self.checks_summary_str(general=False, passing=True)}</li>"
            ),
            (
                "  <li>Failing files: "
                f"{self.checks_summary_str(general=False, passing=False)}</li>"
            ),
            "</ul>",
        ]

        passing_file_foldouts_l = []
        individual_file_checks_passed = self.files_passing
        for i, passing_path in enumerate(sorted(individual_file_checks_passed.keys())):
            tmp = [
                "<details>",
                f"<summary>{i + 1}: {passing_path.name}</summary>",
                f"<p>Full path: {passing_path}</p>",
                "</details>",
            ]
            passing_file_foldouts_l.extend(tmp)

        res_l.extend(
            [
                "",
                "<h3>Passing files</h3>",
                "<details>",
                "<summary>All passing files</summary>",
                "<ul>",
                *passing_file_foldouts_l,
                "</ul>",
                "</details>",
            ]
        )

        failing_file_foldouts_l: list[str] = []
        individual_file_checks_failed = self.files_failing
        for i, failing_path in enumerate(sorted(individual_file_checks_failed.keys())):
            vrs = individual_file_checks_failed[failing_path]

            if failing_file_foldouts_l:
                failing_file_foldouts_l.append("")

            passing_summary = [
                "<details>",
                f"<summary>Passed: {vrs.checks_summary_str(passing=True)}</summary>",
                "  <ol>",
                *[f"    <li>{vr.description}</li>" for vr in vrs.checks_passing],
                "  </ol>",
                "</details>",
            ]

            failing_checks_foldouts = []
            for fc in vrs.checks_failing:
                if fc.exception_info is None:
                    msg = "Should have an exception here"
                    raise AssertionError(msg)

                tmp = [
                    "<li>",
                    "<details>",
                    "<summary>"
                    f"{fc.description} ({type(fc.exception).__name__})"
                    "</summary>",
                    "<pre>",
                    *fc.exception_info.splitlines(),
                    "</pre>",
                    "</details>",
                    "</li>",
                ]
                failing_checks_foldouts.extend(tmp)

            failing_summary = [
                "<details>",
                f"<summary>Failed: {vrs.checks_summary_str(passing=False)}</summary>",
                "  <ol>",
                *failing_checks_foldouts,
                "  </ol>",
                "</details>",
            ]

            tmp = [
                "<details>",
                f"<summary>{i + 1}: {failing_path.name}</summary>",
                f"<p>Full path: {failing_path}</p>",
                *passing_summary,
                *failing_summary,
                "</details>",
                "<br>",
            ]
            failing_file_foldouts_l.extend(tmp)

        res_l.extend(
            [
                "",
                "<h3>Failing files</h3>",
                *failing_file_foldouts_l,
                # End with newline following unix conventions
                "",
            ]
        )

        return "\n".join(res_l)

    def checks_summary_str(self, general: bool, passing: bool) -> str:
        """
        Get a summary of the checks we have performed

        Parameters
        ----------
        general
            Should we get a summary of general checks, or individual file checks?

        passing
            Should we return the summary
            as the number of checks
            which are passing (`True`) or failing (`False`)?

        Returns
        -------
        :
            Summary of the checks
        """
        if general:
            denominator = len(self.general_validation_results_store.validation_results)
            if passing:
                numerator = len(self.general_checks_passing)

            else:
                numerator = len(self.general_checks_failing)

        else:
            denominator = len(self.file_validation_results_stores)
            if passing:
                numerator = len(self.files_passing)

            else:
                numerator = len(self.files_failing)

        pct = numerator / denominator * 100
        return f"{pct:.2f}% ({numerator} / {denominator})"

    def raise_if_errors(self) -> None:
        """
        Raise a `ValidationError` if any of the validation steps failed

        Raises
        ------
        ValidationError
            One of the validation steps in `self.validation_results` failed.
        """
        if any(
            not v.passed
            for v in self.general_validation_results_store.validation_results
        ) or any(
            not v.passed
            for vs in self.file_validation_results_stores.values()
            for v in vs.validation_results
        ):
            raise TreeValidationResultsStoreError(self)


def get_validate_tree_result(  # noqa: PLR0913
    root: Path,
    cv_source: str | None,
    cvs: Input4MIPsCVs | None = None,
    bnds_coord_indicator: str = "bnds",
    frequency_metadata_key: str = "frequency",
    no_time_axis_frequency: str = "fx",
    time_dimension: str = "time",
    rglob_input: str = "*.nc",
    allow_cf_checker_warnings: bool = False,
) -> TreeValidationResultsStore:
    """
    Get the result of validating a (directory) tree

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

    Returns
    -------
    :
        The validation results store.
    """
    logger.info(f"Creating validation results for the tree with root {root}")

    logger.debug("Instantiating a `ValidationResultsStore` for the general steps")
    vrs_general = ValidationResultsStore()

    if cvs is None:
        # Load CVs, we need them for the following steps
        cvs = vrs_general.wrap(
            load_cvs,
            func_description="Load controlled vocabularies to use during validation",
        )(cv_source=cv_source).result

    elif cv_source is not None:
        logger.warning(
            "Ignoring provided value for `cv_source` (using provided cvs instead)."
        )

    all_files = [v for v in root.rglob(rglob_input) if v.is_file()]

    vrs_general.wrap(
        validate_tracking_ids_are_unique,
        func_description="Validate that tracking IDs in all files are unique",
    )(all_files)

    logger.debug("Instantiating a new `TreeValidationResultsStore`")
    tvrs = TreeValidationResultsStore(
        tree_root=root, general_validation_results_store=vrs_general
    )

    for file in tqdm.tqdm(all_files, desc="Files to validate"):
        validate_file_result = get_validate_file_result(
            file,
            cvs=cvs,
            bnds_coord_indicator=bnds_coord_indicator,
            allow_cf_checker_warnings=allow_cf_checker_warnings,
        )

        if cvs is None:
            logger.error(
                "Skipping check of consistency with DRS because CVs did not load"
            )

        else:
            validate_file_result.wrap(
                cvs.DRS.validate_file_written_according_to_drs,
                func_description="Check file is written according to the DRS",
            )(
                file,
                frequency_metadata_key=frequency_metadata_key,
                no_time_axis_frequency=no_time_axis_frequency,
                time_dimension=time_dimension,
            )

        # TODO: check cross references in files to external variables
        # e.g. areacella

        tvrs.file_validation_results_stores[file] = validate_file_result

    logger.info(f"Created tree validation results for the tree with root: {root}")

    return tvrs
