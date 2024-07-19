"""
Validation module
"""

from __future__ import annotations

from pathlib import Path


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

        This helps us with identifying `infile`'s variables correctly
        in the absence of an agreed convention for doing this
        (xarray has a way, but it conflicts with the CF-conventions,
        so here we are).

    Returns
    -------
        The dataset's corresponding metadata entry,
        which can be used in a database of datasets.

    Raises
    ------
    InvalidFileError
        The file does not pass all of the validation.
    """
    raise NotImplementedError()
