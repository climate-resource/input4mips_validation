"""Data model for input4MIPs' controlled vocabularies (CVs)"""
from __future__ import annotations

from attrs import define

from input4mips_validation.cvs_handling.input4MIPs.activity_id import ActivityIDEntries
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import RawCVLoader
from input4mips_validation.cvs_handling.input4MIPs.source_id import SourceIDEntries


@define
class CVsInput4MIPs:
    """
    Data model of input4MIPs' CVs
    """

    raw_loader: RawCVLoader
    """Object used to load the raw CVs"""

    activity_id_entries: ActivityIDEntries
    """Activity ID entries"""

    # dataset_categories: tuple[str, ...]
    # """Recognised dataset categories"""
    # Would make sense for this to actually be entries,
    # and to specify the variables in each category here

    # data_file_required_global_attributes: tuple[str, ...]
    # """Global attributes that must be in data files"""
    # Not sure if these can be linked back to global CVs/should somehow be split.
    # Having this seems like duplication to me...

    # data_reference_syntax: DataReferenceSyntax
    # """Data reference syntax (drs) specification"""

    # instutition_ids: tuple[str, ...]
    # """Recognised institution IDs"""
    # These should be linked back to the global CVs somehow
    # (probably as part of validation)

    # license: LicenseSpecification
    # """License specification that can be used with the data"""

    # mip_era: tuple[str, ...]
    # """Recognised MIP eras"""
    # These should be linked back to the global CVs somehow
    # (probably as part of validation)

    # product: tuple[str, ...]
    # """Recognised product types"""
    # These should be linked back to the global CVs somehow I assume (?)
    # (probably as part of validation)

    source_id_entries: SourceIDEntries
    """Source ID entries"""

    # target_mip_entries: TargetMIPEntries
    # """Target MIP entries"""
    # These should be linked back to the global CVs somehow I assume (?)
    # (probably as part of validation)

    # tracking_id_regexp: str | regexp
    # """Regular expression which files' tracking IDs must match"""

    # Then have a method, `validate_metadata`,
    # and a method, `validate_data` (no-op for now)
    # and a method, `validate_metadata_data_consistency`


# In validation, add `validate_cvs(cvs: CVsInput4MIPs) -> None:`
