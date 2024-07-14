"""
Validation of data
"""

from __future__ import annotations

import re
import subprocess
from functools import wraps
from pathlib import Path
from typing import Callable, ParamSpec, TypeVar

import iris
import ncdata.iris_xarray
import xarray as xr
from attrs import fields
from loguru import logger

from input4mips_validation.cvs_handling.input4MIPs.cv_loading import load_cvs
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.dataset_validation import (
    assert_consistency_between_source_id_and_other_values,
    assert_in_cvs,
)
from input4mips_validation.cvs_handling.input4MIPs.general_validation import (
    assert_is_url_like,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    get_raw_cvs_loader,
)
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadata,
    Input4MIPsDatasetMetadataEntry,
    Input4MIPsDatasetMetadataFromESGF,
    Input4MIPsDatasetMetadataFromFiles,
)
from input4mips_validation.exceptions import DatasetMetadataInconsistencyError

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


def create_metadata_entry(ds: xr.Dataset) -> Input4MIPsDatasetMetadataEntry:
    """
    Create a {py:obj}`Input4MIPsDatasetMetadataEntry` from a {py:obj}`xr.Dataset`

    Parameters
    ----------
    ds
        Dataset from which to make the metadata entry

    Returns
    -------
        Created metadata entry
    """
    dataset_entry_keys = [v.name for v in fields(Input4MIPsDatasetMetadataFromFiles)]
    dataset_entry_files = Input4MIPsDatasetMetadataFromFiles(
        **{k: v for k, v in ds.attrs.items() if k in dataset_entry_keys}
    )
    dataset_entry_esgf = Input4MIPsDatasetMetadataFromESGF()
    dataset_entry = Input4MIPsDatasetMetadataEntry(
        file=dataset_entry_files,
        esgf=dataset_entry_esgf,
    )

    return dataset_entry


def check_with_cf_checker(filepath: Path | str, ds: xr.Dataset) -> None:
    """
    Check a file with the cf-checker

    Parameters
    ----------
    filepath
        Filepath to check

    ds
        Dataset that corresponds to `filepath`.

        This is required to we can tell cf-checker
        which CF conventions to use while checking the file.
    """
    conventions_match = re.match(
        r"CF-(?P<conventions_id>[0-9\.]+).*", ds.attrs["Conventions"]
    )
    if not conventions_match:
        msg = (
            "Cannot extract CF conventions from Conventions metadata. "
            f"{ds.attrs['Conventions']=}"
        )
        raise ValueError(msg)

    cf_conventions = conventions_match.group("conventions_id").strip()

    cf_checks_loc = subprocess.check_output(["/usr/bin/which", "cfchecks"]).strip()  # noqa: S603
    try:
        subprocess.check_output(
            [cf_checks_loc, "-v", cf_conventions, str(filepath)]  # noqa: S603
        )
    except subprocess.CalledProcessError as exc:
        error_msg = (
            f"cf-checker validation failed. cfchecks output:\n\n{exc.output.decode()}"
        )
        raise ValueError(error_msg) from exc


def validate_input4mips_ds_metadata(
    metadata: Input4MIPsDatasetMetadata,
    cvs: CVsInput4MIPs,
) -> None:
    """
    Validate that {py:attr}`Input4MIPsDataset.metadata` confirms to the required form

    Parameters
    ----------
    metadata
        Metadata value to validate

    cvs
        Controlled vocabularies to use during the validation
    """
    # Activity ID
    assert_in_cvs(
        value=metadata.activity_id,
        cvs_key="activity_id",
        cv_values=cvs.activity_id_entries.activity_ids,
        cvs=cvs,
    )

    # Further info URL
    assert_is_url_like(
        value=metadata.further_info_url,
        description="further_info_url",
    )

    # Institution ID
    assert_in_cvs(
        value=metadata.institution_id,
        cvs_key="institution_id",
        cv_values=cvs.institution_ids,
        cvs=cvs,
    )

    # Source ID
    assert_in_cvs(
        value=metadata.source_id,
        cvs_key="source_id",
        cv_values=cvs.source_id_entries.source_ids,
        cvs=cvs,
    )

    # Consistency with source ID
    assert_consistency_between_source_id_and_other_values(
        source_id=metadata.source_id,
        further_info_url=metadata.further_info_url,
        institution_id=metadata.institution_id,
        cvs=cvs,
    )


def get_ds_var_assert_single(ds: xr.Dataset) -> str:
    """
    Get a {py:obj}`xr.Dataset`'s variable, asserting that there is only one

    Parameters
    ----------
    ds
        {py:obj}`xr.Dataset` from which to retrieve the variable

    Returns
    -------
        ``ds``'s variable
    """
    ds_var_l: list[str] = list(ds.data_vars)
    if len(ds_var_l) != 1:
        msg = f"``ds`` must only have one variable. Received: {ds_var_l!r}"
        raise AssertionError(msg)

    return ds_var_l[0]


def validate_input4mips_ds_ds(
    input4mips_ds_ds: xr.Dataset,
    cvs: CVsInput4MIPs,
) -> None:
    """
    Validate that {py:attr}`Input4MIPsDataset.ds` confirms to the required form

    Parameters
    ----------
    input4mips_ds_ds
        Dataset value to validate

    cvs
        Controlled vocabularies to use during the validation
    """
    # no-op currently
    pass


def validate_input4mips_ds_ds_metadata_consistency(
    ds: Input4MIPsDataset,
    cvs: CVsInput4MIPs,
) -> None:
    """
    Validate that {py:obj}`Input4MIPsDataset` is internally consistent.

    Specifically, that {py:attr}`Input4MIPsDataset.ds`
    and {py:attr}`Input4MIPsDataset.metadata` are consistent.

    Parameters
    ----------
    ds
        Object to validate

    cvs
        Controlled vocabularies to use during the validation
    """
    metadata = ds.metadata

    variable_id = metadata.variable_id

    if variable_id == "multiple":
        dataset_variables = list(ds.ds.data_vars)

        if len(dataset_variables) <= 1:
            msg = (
                "If variable_id is 'multiple', "
                "there should be more than one variable in the dataset. "
                f"Received: {dataset_variables=}"
            )
            raise ValueError(msg)

    else:
        dataset_variable = ds.ds_var

        if dataset_variable != metadata.variable_id:
            raise DatasetMetadataInconsistencyError(
                ds_key="The dataset's variable",
                ds_key_value=f"{dataset_variable=}",
                metadata_key="metadata.variable_id",
                metadata_key_value=f"{metadata.variable_id=!r}",
            )


def validate_ds(
    ds: xr.Dataset,
    cvs: CVsInput4MIPs,
) -> None:
    """
    Validate a dataset

    Parameters
    ----------
    ds
        Dataset to validate.

    cvs
        Controlled vocabularies to use during the validation
    """
    # Create Input4MIPsDataset
    ds_no_attrs = ds.copy()
    ds_no_attrs.attrs = {}

    metadata_keys = [v.name for v in fields(Input4MIPsDatasetMetadata)]
    metadata = Input4MIPsDatasetMetadata(
        **{k: v for k, v in ds.attrs.items() if k in metadata_keys}
    )
    input4mips_ds = Input4MIPsDataset(ds=ds_no_attrs, metadata=metadata, cvs=cvs)

    validate_input4mips_ds_metadata(metadata, cvs=cvs)
    validate_input4mips_ds_ds(input4mips_ds.ds, cvs=cvs)
    validate_input4mips_ds_ds_metadata_consistency(input4mips_ds, cvs=cvs)


def load_cvs_here(cv_source: str) -> CVsInput4MIPs:
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
) -> Input4MIPsDatasetMetadataEntry:
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

        This helps us with identifying `infile`'s variables correctly.

    Returns
    -------
        The dataset's corresponding metadata entry,
        which can be used in a database of datasets.

    Raises
    ------
    InvalidFileError
        The file does not pass all of the validation.
    """
    logger.info(f"Validating {infile}")
    error_container = []
    catch_error = get_catch_error_decorator(error_container)

    ds_xr_load = catch_error(
        xr.load_dataset, call_purpose="Load data with `xr.load_dataset`"
    )(infile)

    cubes = catch_error(iris.load, call_purpose="Load data with `iris.load`")(infile)
    if ds_xr_load.attrs["variable_id"] != "multiple":
        catch_error(iris.load_cube, call_purpose="Load data with `iris.load_cube`")(
            infile
        )

    catch_error(check_with_cf_checker, call_purpose="Check data with cf-checker")(
        infile, ds=ds_xr_load
    )

    dataset_entry = catch_error(
        create_metadata_entry, call_purpose="Create input4MIPs database metadata entry"
    )(ds_xr_load)

    cvs = catch_error(
        load_cvs_here,
        call_purpose="Load controlled vocabularies to use during validation",
    )(cv_source)

    # Convert with ncdata as it is generally better at this
    ds_careful_load = ncdata.iris_xarray.cubes_to_xarray(cubes)
    # Guess that everything which has "bnds" in it is a co-ordinate.
    # This is definitely a pain point when loading data from iris written.
    # TODO: issue in [ncdata](https://github.com/pp-mo/ncdata)
    # to see whether a true expert has any ideas.
    bnds_guess = [v for v in ds_careful_load.data_vars if bnds_coord_indicator in v]
    ds_careful_load = ds_careful_load.set_coords(bnds_guess)

    catch_error(
        validate_ds,
        call_purpose="Check the dataset's data and metadata",
    )(ds_careful_load, cvs=cvs)

    if error_container:
        logger.info("Validation failed")
        raise InvalidFileError(filepath=infile, error_container=error_container)

    else:
        logger.info("Validation passed")

    return dataset_entry
