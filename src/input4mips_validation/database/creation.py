"""
Creation of database entries
"""

from __future__ import annotations

from pathlib import Path

from loguru import logger

from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.database.database import Input4MIPsDatabaseEntryFile


def create_db_file_entries(  # noqa: PLR0913
    root: Path,
    cv_source: str | None,
    frequency_metadata_key: str = "frequency",
    no_time_axis_frequency: str = "fx",
    time_dimension: str = "time",
    rglob_input: str = "*.nc",
) -> tuple[Input4MIPsDatabaseEntryFile, ...]:
    """
    Create database file entries for all the files in a given path

    For full details on options for loading CVs,
    see
    [`get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader].

    Parameters
    ----------
    root
        Root of the path to search for files

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

    rglob_input
        Input to rglob.

        This helps us only select relevant files to check.

    Returns
    -------
    :
        Database file entries for the files in `root`
    """
    raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
    logger.debug(f"{raw_cvs_loader=}")
    cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

    all_files = [v for v in root.rglob(rglob_input) if v.is_file()]

    db_entries = []
    for file in all_files:
        logger.info(f"Creating database entry for {file}")
        database_entry = Input4MIPsDatabaseEntryFile.from_file(
            file,
            cvs=cvs,
            frequency_metadata_key=frequency_metadata_key,
            no_time_axis_frequency=no_time_axis_frequency,
            time_dimension=time_dimension,
        )

        db_entries.append(database_entry)

    return tuple(db_entries)
