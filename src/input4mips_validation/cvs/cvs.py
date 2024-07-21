"""
Data model of the controlled vocabularies (CVs)
"""

from __future__ import annotations

from attrs import define

from input4mips_validation.cvs.activity_id import ActivityIDEntries
from input4mips_validation.cvs.drs import DataReferenceSyntax
from input4mips_validation.cvs.license import LicenseEntries
from input4mips_validation.cvs.loading_raw import RawCVLoader
from input4mips_validation.cvs.source_id import SourceIDEntries


@define
class Input4MIPsCVs:
    """
    Data model of input4MIPs' CVs
    """

    raw_loader: RawCVLoader
    """Object used to load the raw CVs"""

    DRS: DataReferenceSyntax
    """Data reference syntax used with these CVs"""
    # TODO: validation - check that all bits of the DRS
    #       are known in the metadata universe
    #        e.g. are required fields of files or something
    #        (may have to maintain list of 'known stuff' by hand).

    activity_id_entries: ActivityIDEntries
    """Activity ID entries"""

    # dataset_categories: tuple[str, ...]
    # """Recognised dataset categories"""
    # Would make sense for this to actually be entries,
    # and to specify the variables in each category here
    # No other validation applied

    institution_ids: tuple[str, ...]
    """Recognised institution IDs"""
    # TODO: check these against the global CVs when validating

    license_entries: LicenseEntries
    """License entries"""

    # mip_eras: tuple[str, ...]
    # """Recognised MIP eras"""
    # These should be linked back to the global CVs somehow
    # (probably as part of validation)

    # products: ProductEntries
    # """Recognised product types"""
    # These should be linked back to the global CVs somehow I assume (?)
    # (probably as part of validation)

    # publication_statuses: PublicationStatusEntries
    # """Recognised publication statuses"""
    # These should be linked back to the global CVs somehow I assume (?)
    # (probably as part of validation)

    # required_global_attribute: tuple[str, ...]
    # """Global attributes required in input4MIPs files"""
    # Would be nice if these were entries and hence we could get descriptions
    # of the meanins of the fields/link back to global CVs.
    # Might be easy with JSON-LD.

    source_id_entries: SourceIDEntries
    """Source ID entries"""

    # target_mip_entries: TargetMIPEntries
    # """Target MIP entries"""
    # These should be linked back to the global CVs somehow I assume (?)
    # (probably as part of validation)

    # tracking_id_regexp: str | regexp
    # """Regular expression which files' tracking IDs must match"""
