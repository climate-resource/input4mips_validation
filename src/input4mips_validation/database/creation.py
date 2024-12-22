"""
Creation of database entries
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any

import input4mips_validation.logging_config
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.database.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.inference.from_data import FrequencyMetadataKeys
from input4mips_validation.logging import setup_logging
from input4mips_validation.logging_config import (
    LoggingConfigSerialisedType,
    deserialise_logging_config,
    serialise_logging_config,
)
from input4mips_validation.parallelisation import run_parallel
from input4mips_validation.xarray_helpers.variables import (
    XRVariableHelper,
    XRVariableProcessorLike,
)


def create_db_file_entry_with_logging(
    file: Path,
    /,
    logging_config_serialised: LoggingConfigSerialisedType,
    **kwargs: Any,
) -> Input4MIPsDatabaseEntryFile:
    """
    Create database file entries, with the logging setup matching main

    Parameters
    ----------
    logging_config_serialised
        Logging configuration to use (serialised version thereof)

    file
        File for which to create the entry

    kwargs
        Passed to
        [`Input4MIPsDatabaseEntryFile.from_file`][input4mips_validation.database.database.Input4MIPsDatabaseEntryFile.from_file]

    Returns
    -------
    :
        Created database entry for `file`
    """
    logging_config = deserialise_logging_config(logging_config_serialised)
    setup_logging(
        enable=logging_config is not None,
        logging_config=logging_config,
    )

    return Input4MIPsDatabaseEntryFile.from_file(file, **kwargs)


def create_db_file_entries(  # noqa: PLR0913
    files: Iterable[Path],
    cv_source: str | None,
    frequency_metadata_keys: FrequencyMetadataKeys = FrequencyMetadataKeys(),
    time_dimension: str = "time",
    xr_variable_processor: XRVariableProcessorLike = XRVariableHelper(),
    n_processes: int = 1,
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

    Returns
    -------
    :
        Database file entries for the files in `files`
    """
    cvs = load_cvs(cv_source=cv_source)

    # Might be fixable if we use multiprocessing more directly,
    # see e.g. https://github.com/znichollscr/loguru/blob/61963240dece1979961ec43840e06a1f396479c4/tests/test_multiprocessing.py#L243
    logging_config_serialised = serialise_logging_config(
        input4mips_validation.logging_config.LOGGING_CONFIG
    )

    db_entries = run_parallel(
        func_to_call=create_db_file_entry_with_logging,
        iterable_input=files,
        input_desc="files",
        n_processes=n_processes,
        logging_config_serialised=logging_config_serialised,
        cvs=cvs,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        time_dimension=time_dimension,
    )
    return db_entries
