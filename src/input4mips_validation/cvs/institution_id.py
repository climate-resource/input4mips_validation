"""
Institution ID CV handling

For validation, see [`validation`][input4mips_validation.validation].
"""

from __future__ import annotations

import json

from typing_extensions import TypeAlias

from input4mips_validation.cvs.loading_raw import RawCVLoader
from input4mips_validation.serialisation import converter_json

INSTITUTION_ID_FILENAME: str = "input4MIPs_institution_id.json"
"""Default name of the file in which the institution ID CV is saved"""

InstitutionIDEntriesUnstructured: TypeAlias = list[str]
"""Form into which institution ID entries are serialised for the CVs"""


def convert_unstructured_cv_to_institution_ids(
    unstructured: InstitutionIDEntriesUnstructured,
) -> tuple[str, ...]:
    """
    Convert the raw CV data to its structured form

    Parameters
    ----------
    unstructured
        Unstructured CV data

    Returns
    -------
        Institution IDs
    """
    return converter_json.structure(unstructured, tuple[str, ...])


def convert_institution_ids_to_unstructured_cv(
    institution_ids: tuple[str, ...],
) -> InstitutionIDEntriesUnstructured:
    """
    Convert the structured institution_id entries to the raw CV form

    Parameters
    ----------
    institution_ids
        Institution IDs

    Returns
    -------
        Raw CV data
    """
    raw_cv_form = list(institution_ids)

    return raw_cv_form


def load_institution_ids(
    raw_cvs_loader: RawCVLoader,
    filename: str = INSTITUTION_ID_FILENAME,
) -> tuple[str, ...]:
    """
    Load the instution IDs in the CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of raw CVs data.

    filename
        Name of the file from which to load the CVs.

        Passed to
        [`raw_cvs_loader.load_raw`][input4mips_validation.cvs.loading_raw.RawCVLoader.load_raw].

    Returns
    -------
        Institution IDs
    """
    return convert_unstructured_cv_to_institution_ids(
        json.loads(raw_cvs_loader.load_raw(filename=filename))
    )
