"""Tools for getting values from the CVs"""
from __future__ import annotations

from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    CVsRoot,
    load_raw_cv_definition,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    convert_raw_cv_to_source_id_entries,
)


def load_valid_cv_values(cvs_key: str, cvs_root: CVsRoot) -> tuple[str, ...]:
    """
    Load valid values according to the CVs

    Parameters
    ----------
    cvs_key
        CVs key for which to load the valid values

    cvs_root
        Root of the CVs definitions

    Returns
    -------
        Valid values for ``cvs_key`` according to the  CVs defined in ``cvs_root``
    """
    match cvs_key:
        case "source_id":
            return load_source_id_entries(cvs_root=cvs_root).source_ids
        case _:
            raise NotImplementedError(cvs_key)


def load_source_id_entries(cvs_root: CVsRoot) -> SourceIDEntries:
    """
    Load the source_id entries in the CVs

    Parameters
    ----------
    cvs_root
        Root of the CVs definitions

    Returns
    -------
        Valid values for ``cvs_key`` according to the  CVs defined in ``cvs_root``
    """
    return convert_raw_cv_to_source_id_entries(
        load_raw_cv_definition(filename=SOURCE_ID_FILENAME, root=cvs_root)
    )
