"""
Creation of database entries
"""

from __future__ import annotations

import concurrent.futures
from collections.abc import Iterable
from pathlib import Path

import tqdm
from loguru import logger

from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.database.database import Input4MIPsDatabaseEntryFile


def create_db_file_entries(  # noqa: PLR0913
    files: Iterable[Path],
    cv_source: str | None,
    frequency_metadata_key: str = "frequency",
    no_time_axis_frequency: str = "fx",
    time_dimension: str = "time",
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

    frequency_metadata_key
        The key in the data's metadata
        which points to information about the data's frequency

    no_time_axis_frequency
        The value of `frequency_metadata_key` in the metadata which indicates
        that the file has no time axis i.e. is fixed in time.

    time_dimension
        The time dimension of the data

    n_processes
        Number of parallel processes to use while creating the entries.

    Returns
    -------
    :
        Database file entries for the files in `files`
    """
    raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
    logger.debug(f"{raw_cvs_loader=}")
    cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

    logger.info(
        "Creating database entries in parallel using "
        f"{n_processes} {'processes' if n_processes > 1 else 'process'}"
    )
    with concurrent.futures.ProcessPoolExecutor(max_workers=n_processes) as executor:
        futures = [
            executor.submit(
                Input4MIPsDatabaseEntryFile.from_file,
                file,
                cvs=cvs,
                frequency_metadata_key=frequency_metadata_key,
                no_time_axis_frequency=no_time_axis_frequency,
                time_dimension=time_dimension,
            )
            for file in tqdm.tqdm(files, desc="Submitting files to queue")
        ]

        db_entries = [
            future.result()
            for future in tqdm.tqdm(
                concurrent.futures.as_completed(futures), desc="Database file entries"
            )
        ]

    return tuple(db_entries)
