"""
Creation of database entries
"""

from __future__ import annotations

import multiprocessing
from collections.abc import Iterable
from pathlib import Path
from typing import Any

import loguru

from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.database.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.inference.from_data import FrequencyMetadataKeys
from input4mips_validation.parallelisation import run_parallel
from input4mips_validation.xarray_helpers.variables import (
    XRVariableHelper,
    XRVariableProcessorLike,
)


def create_db_file_entry_with_logging(
    file: Path,
    /,
    logger_to_use: loguru.Logger,
    **kwargs: Any,
) -> Input4MIPsDatabaseEntryFile:
    """
    Create database file entries with logging passed through too

    Parameters
    ----------
    file
        File for which to create the entry

    logger_to_use
        Logger to use when creating the entries

    **kwargs
        Passed to
        [`Input4MIPsDatabaseEntryFile.from_file`][input4mips_validation.database.database.Input4MIPsDatabaseEntryFile.from_file]

    Returns
    -------
    :
        Created database entry for `file`
    """
    logger_to_use.info("hi")

    return Input4MIPsDatabaseEntryFile.from_file(file, **kwargs)


def create_db_file_entries(  # noqa: PLR0913
    files: Iterable[Path],
    cv_source: str | None,
    frequency_metadata_keys: FrequencyMetadataKeys = FrequencyMetadataKeys(),
    time_dimension: str = "time",
    xr_variable_processor: XRVariableProcessorLike = XRVariableHelper(),
    n_processes: int = 1,
    mp_context: multiprocessing.context.BaseContext | None = None,
) -> tuple[Input4MIPsDatabaseEntryFile, ...]:
    """
    Create database file entries for all the files in a given path

    For full details on options for loading CVs,
    see
    [`get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader].

    Parameters
    ----------
    files
        Files for which to create the database entries

    cv_source
        Source from which to load the CVs

    frequency_metadata_keys
        Metadata definitions for frequency information

    time_dimension
        The time dimension of the data

    xr_variable_processor
        Helper to use for processing the variables in xarray objects.

    n_processes
        Number of parallel processes to use while creating the entries.

    mp_context
        Multiprocessing context to use.

        If `n_processes` is equal to 1, simply pass `None`.
        If `n_processes` is greater than 1 and you pass `None`,
        a default context will be created and used.

    Returns
    -------
    :
        Database file entries for the files in `files`
    """
    cvs = load_cvs(cv_source=cv_source)

    db_entries = run_parallel(
        func_to_call=Input4MIPsDatabaseEntryFile.from_file,
        iterable_input=files,
        input_desc="files",
        n_processes=n_processes,
        mp_context=mp_context,
        cvs=cvs,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        time_dimension=time_dimension,
    )
    return db_entries
