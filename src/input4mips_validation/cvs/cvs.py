"""
Data model of the controlled vocabularies (CVs)
"""

from __future__ import annotations

from attrs import define

from input4mips_validation.cvs.activity_id import ActivityIDEntries
from input4mips_validation.cvs.drs import DataReferenceSyntax
from input4mips_validation.cvs.exceptions import (
    ValueInconsistentWithCVsError,
    ValueNotAllowedByCVsError,
)
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
    def validate_activity_id(self, value: str) -> None:
        """
        Validate that a value of activity ID is valid

        Parameters
        ----------
        value
            Value to validate

        Raises
        ------
        ValueNotAllowedByCVsError
            The provided value is not allowed by the CVs
        """
        if value not in self.activity_id_entries.activity_ids:
            raise ValueNotAllowedByCVsError(
                value=value,
                cv_component="activity_id",
                cv_allowed_values=self.activity_id_entries.activity_ids,
                cv_entries=self.activity_id_entries.entries,
            )

    def validate_contact(self, value: str, source_id: str) -> None:
        """
        Validate that a value of contact is valid

        Parameters
        ----------
        value
            Value to validate

        source_id
            Source ID value

            This is required because the source ID defines
            what the expected value of contact is.

        Raises
        ------
        ValueInconsistentWithCVsError
            The provided value is not the correct value according to the CVs
            and the value of `source_id`.
        """
        cv_source_id_entry = self.source_id_entries[source_id]
        expected_value = cv_source_id_entry.values.contact

        if value != expected_value:
            raise ValueInconsistentWithCVsError(
                value=value,
                expected_value=expected_value,
                cv_component="contact",
                cv_component_dependent_on="source_id",
                cv_entry_dependenty_component=cv_source_id_entry,
            )

    def validate_source_version(self, value: str, source_id: str) -> None:
        """
        Validate that a value of source version is valid

        Parameters
        ----------
        value
            Value to validate

        source_id
            Source ID value

            This is required because the source ID defines
            what the expected value of source_version is.

        Raises
        ------
        ValueInconsistentWithCVsError
            The provided value is not the correct value according to the CVs
            and the value of `source_id`.
        """
        cv_source_id_entry = self.source_id_entries[source_id]
        expected_value = cv_source_id_entry.values.source_version

        if value != expected_value:
            raise ValueInconsistentWithCVsError(
                value=value,
                expected_value=expected_value,
                cv_component="source_version",
                cv_component_dependent_on="source_id",
                cv_entry_dependenty_component=cv_source_id_entry,
            )
