"""
Loading of CVs from a given source
"""

from __future__ import annotations

from input4mips_validation.cvs.activity_id import load_activity_id_entries
from input4mips_validation.cvs.cvs import Input4MIPsCVs
from input4mips_validation.cvs.drs import load_drs
from input4mips_validation.cvs.institution_id import load_institution_ids
from input4mips_validation.cvs.license import load_license_entries
from input4mips_validation.cvs.loading_raw import RawCVLoader, get_raw_cvs_loader
from input4mips_validation.cvs.source_id import load_source_id_entries


def load_cvs(
    raw_cvs_loader: RawCVLoader | None = None,
) -> Input4MIPsCVs:
    """
    Load CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of the raw CVs data

        If not supplied, this will be retrieved with
        [`get_raw_cvs_loader`][input4mips_validation.cvs.loading_raw.get_raw_cvs_loader].

    Returns
    -------
        Loaded CVs
    """
    if raw_cvs_loader is None:
        raw_cvs_loader = get_raw_cvs_loader()

    return load_cvs_known_loader(raw_cvs_loader=raw_cvs_loader)


# @functools.cach
# There may be subtle bugs if we use caching,
# particularly related to forcing downloads,
# and this may be the wrong pattern anyway,
# so we haven't turned caching on yet.
def load_cvs_known_loader(raw_cvs_loader: RawCVLoader) -> Input4MIPsCVs:
    """
    Load CVs from a known loader

    Parameters
    ----------
    raw_cvs_loader
        Loader of the raw CVs data

    Returns
    -------
        Loaded CVs
    """
    activity_id_entries = load_activity_id_entries(raw_cvs_loader=raw_cvs_loader)
    drs = load_drs(raw_cvs_loader=raw_cvs_loader)
    institution_ids = load_institution_ids(raw_cvs_loader=raw_cvs_loader)
    license_entries = load_license_entries(raw_cvs_loader=raw_cvs_loader)
    source_id_entries = load_source_id_entries(raw_cvs_loader=raw_cvs_loader)

    return Input4MIPsCVs(
        raw_loader=raw_cvs_loader,
        DRS=drs,
        activity_id_entries=activity_id_entries,
        institution_ids=institution_ids,
        license_entries=license_entries,
        source_id_entries=source_id_entries,
    )
