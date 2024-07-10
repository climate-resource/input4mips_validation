"""
License CV handling

To keep things in one place, all validation is handled in
{py:mod}`input4mips_validation.cvs_handling.input4MIPs.validation`.
This allows us to validate individual values as well as relationships
between values in one hit.
"""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import attr
from attrs import define, field
from typing_extensions import TypeAlias

from input4mips_validation.cvs_handling.exceptions import NonUniqueError
from input4mips_validation.cvs_handling.input4MIPs.serialisation import converter_json

LICENSE_FILENAME: str = "input4MIPs_license.json"
"""Default name of the file in which the license CV is saved"""

LicenseEntriesUnstructured: TypeAlias = dict[str, dict[str, str]]
"""Form into which license entries are serialised for the CVs"""


@define
class LicenseValues:
    """
    Values defined by a license
    """

    conditions: str
    """Conditions attached to this license"""

    license_url: str
    """URL that has full information about the license"""

    long_name: str
    """Long name of the license"""


@define
class LicenseEntry:
    """
    A single license entry
    """

    license_id: str
    """The unique ID which identifies this license"""

    values: LicenseValues
    """The values defined by this license"""


@define
class LicenseEntries:
    """
    Helper container for handling license entries
    """

    entries: tuple[LicenseEntry, ...] = field()
    """License entries"""

    @entries.validator
    def _entry_licenses_are_unique(
        self, attribute: attr.Attribute[Any], value: tuple[LicenseEntry, ...]
    ) -> None:
        license_ids = self.license_ids
        if len(license_ids) != len(set(license_ids)):
            raise NonUniqueError(
                description=(
                    "The license's of the entries in ``entries`` are not unique"
                ),
                values=license_ids,
            )

    def __getitem__(self, key: str) -> LicenseEntry:
        """
        Get {py:obj}`LicenseEntry` by its name

        We return the {py:obj}`LicenseEntry` whose license matches ``key``.
        """
        matching = [v for v in self.entries if v.license_id == key]
        if not matching:
            msg = f"{key!r}. {self.licenses=!r}"
            raise KeyError(msg)

        if len(matching) > 1:  # pragma: no cover
            msg = "licenses should be validated as being unique at initialisation"
            raise AssertionError(msg)

        return matching[0]

    def __iter__(self) -> Iterable[LicenseEntry]:
        """
        Iterate over ``self.entries``
        """
        yield from self.entries

    def __len__(self) -> int:
        """
        Get length of ``self.entries``
        """
        return len(self.entries)

    @property
    def license_ids(self) -> tuple[str, ...]:
        """
        License IDs found in the list of entries

        Returns
        -------
            The licenses found in the list of entries
        """
        return tuple(v.license_id for v in self.entries)


def convert_unstructured_cv_to_license_entries(
    unstructured: LicenseEntriesUnstructured,
) -> LicenseEntries:
    """
    Convert the raw CV data to a {py:obj}`LicenseEntries`

    Parameters
    ----------
    unstructured
        Unstructured CV data

    Returns
    -------
        License entries
    """
    restructured = {
        "entries": [
            dict(license_id=key, values=value) for key, value in unstructured.items()
        ]
    }

    return converter_json.structure(restructured, LicenseEntries)


def convert_license_entries_to_unstructured_cv(
    license_entries: LicenseEntries,
) -> LicenseEntriesUnstructured:
    """
    Convert a {py:obj}`LicenseEntries` to the raw CV form

    Parameters
    ----------
    license_entries
        License entries

    Returns
    -------
        Raw CV data
    """
    unstructured = converter_json.unstructure(license_entries)

    raw_cv_form = {
        entry["license_id"]: entry["values"] for entry in unstructured["entries"]
    }

    return raw_cv_form
