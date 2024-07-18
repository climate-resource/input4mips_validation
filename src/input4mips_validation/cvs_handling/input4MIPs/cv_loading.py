"""Tools for getting values from the CVs"""

from __future__ import annotations

import json

from input4mips_validation.cvs_handling.input4MIPs.activity_id import (
    ACTIVITY_ID_FILENAME,
    ActivityIDEntries,
    convert_unstructured_cv_to_activity_id_entries,
)
from input4mips_validation.cvs_handling.input4MIPs.cvs import CVsInput4MIPs
from input4mips_validation.cvs_handling.input4MIPs.institution_id import (
    INSTITUTION_ID_FILENAME,
    convert_unstructured_cv_to_institution_ids,
)
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    RawCVLoader,
    get_raw_cvs_loader,
)
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    SOURCE_ID_FILENAME,
    SourceIDEntries,
    convert_unstructured_cv_to_source_id_entries,
)


def load_activity_id_entries(
    raw_cvs_loader: RawCVLoader,
) -> ActivityIDEntries:
    """
    Load the activity_id entries in the CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of raw CVs data.

    Returns
    -------
        Valid values for ``cvs_key`` according to the  CVs defined in ``cvs_root``
    """
    return convert_unstructured_cv_to_activity_id_entries(
        json.loads(raw_cvs_loader.load_raw(filename=ACTIVITY_ID_FILENAME))
    )


def load_source_id_entries(
    raw_cvs_loader: RawCVLoader,
) -> SourceIDEntries:
    """
    Load the source_id entries in the CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of raw CVs data.

    Returns
    -------
        Valid values for ``cvs_key`` according to the  CVs defined in ``cvs_root``
    """
    return convert_unstructured_cv_to_source_id_entries(
        json.loads(raw_cvs_loader.load_raw(filename=SOURCE_ID_FILENAME))
    )


def load_institution_ids(
    raw_cvs_loader: RawCVLoader,
) -> tuple[str, ...]:
    """
    Load the instution IDs in the CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of raw CVs data.

    Returns
    -------
        Valid values for ``cvs_key`` according to the  CVs defined in ``cvs_root``
    """
    return convert_unstructured_cv_to_institution_ids(
        json.loads(raw_cvs_loader.load_raw(filename=INSTITUTION_ID_FILENAME))
    )


def load_cvs(
    raw_cvs_loader: RawCVLoader | None = None,
) -> CVsInput4MIPs:
    """
    Load CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of the raw CVs data

        If not supplied, this will be retrieved with
        {py:func}`input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.get_raw_cvs_loader`.

    Returns
    -------
        Loaded CVs
    """
    if raw_cvs_loader is None:
        raw_cvs_loader = get_raw_cvs_loader()

    return load_cvs_known_loader(raw_cvs_loader=raw_cvs_loader)


# @functools.cache
def load_cvs_known_loader(raw_cvs_loader: RawCVLoader) -> CVsInput4MIPs:
    """
    Load CVs

    This requires the raw CVs loader to be known,
    so the results can be cached
    (although there may be subtle bugs in this related to forcing downloads
    and this may be the wrong pattern anyway, so we haven't turned it on yet).

    Parameters
    ----------
    raw_cvs_loader
        Loader of the raw CVs data

    Returns
    -------
        Loaded CVs
    """
    activity_id_entries = load_activity_id_entries(raw_cvs_loader=raw_cvs_loader)
    institution_ids = load_institution_ids(raw_cvs_loader=raw_cvs_loader)
    source_id_entries = load_source_id_entries(raw_cvs_loader=raw_cvs_loader)

    return CVsInput4MIPs(
        raw_loader=raw_cvs_loader,
        activity_id_entries=activity_id_entries,
        institution_ids=institution_ids,
        source_id_entries=source_id_entries,
    )
