"""
Institution ID CV handling

To keep things in one place, all validation is handled in
{py:mod}`input4mips_validation.cvs_handling.input4MIPs.validation`.
This allows us to validate individual values as well as relationships
between values in one hit.
"""
from __future__ import annotations

from typing_extensions import TypeAlias

INSTITUTION_ID_FILENAME: str = "input4MIPs_institution_id.json"
"""Default name of the file in which the institution ID CV is saved"""

InstitutionIDEntriesUnstructured: TypeAlias = dict[str, list[str]]
"""Form into which institution ID entries are serialised for the CVs"""


def convert_unstructured_cv_to_institution_ids(
    unstructured: InstitutionIDEntriesUnstructured,
) -> list[str]:
    """
    Convert the raw CV data to a {py:obj}`list` of `str`

    Parameters
    ----------
    unstructured
        Unstructured CV data

    Returns
    -------
        Institution IDs
    """
    return unstructured["institution_id"]


def convert_institution_ids_to_unstructured_cv(
    institution_ids: list[str],
) -> InstitutionIDEntriesUnstructured:
    """
    Convert a {py:obj}`list` of `str` to the raw CV form

    Parameters
    ----------
    institution_ids
        Institution IDs

    Returns
    -------
        Raw CV data
    """
    raw_cv_form = {"institution_id": institution_ids}

    return raw_cv_form
