"""Tools for getting values from the CVs"""
from __future__ import annotations

from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    RawCVLoader,
    get_raw_cvs_loader,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    convert_raw_cv_to_source_id_entries,
)


def load_valid_cv_values(
    cvs_key: str,
    raw_cvs_loader: None | RawCVLoader = None,
) -> tuple[str, ...]:
    """
    Load valid values according to the CVs

    Parameters
    ----------
    cvs_key
        CVs key for which to load the valid values

    raw_cvs_loader
        Loader of raw CVs data.

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.get_raw_cvs_loader`.

    Returns
    -------
        Valid values for ``cvs_key`` according to the  CVs defined in ``cvs_root``
    """
    match cvs_key:
        case "source_id":
            return load_source_id_entries(raw_cvs_loader=raw_cvs_loader).source_ids
        case _:
            raise NotImplementedError(cvs_key)


def load_source_id_entries(
    raw_cvs_loader: None | RawCVLoader = None,
) -> SourceIDEntries:
    """
    Load the source_id entries in the CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of raw CVs data.

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.get_raw_cvs_loader`.

    Returns
    -------
        Valid values for ``cvs_key`` according to the  CVs defined in ``cvs_root``
    """
    if raw_cvs_loader is None:
        raw_cvs_loader = get_raw_cvs_loader()

    return convert_raw_cv_to_source_id_entries(
        raw_cvs_loader.load_raw(filename=SOURCE_ID_FILENAME)
    )
