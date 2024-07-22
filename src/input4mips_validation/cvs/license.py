"""
License CV handling

For validation, see [`validation`][input4mips_validation.validation].
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any

import attr
from attrs import define, field
from typing_extensions import TypeAlias

from input4mips_validation.cvs.loading_raw import RawCVLoader
from input4mips_validation.exceptions import NonUniqueError
from input4mips_validation.serialisation import converter_json

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

    # Note: we are ok with the duplicate validation logic here,
    # because it makes implementation of our helper dunder methods
    # simpler if we can assume that the activity IDs are unique.
    @entries.validator
    def _entry_licenses_are_unique(
        self, attribute: attr.Attribute[Any], value: tuple[LicenseEntry, ...]
    ) -> None:
        license_ids = self.license_ids
        if len(license_ids) != len(set(license_ids)):
            raise NonUniqueError(
                description=(
                    "The `license_id`'s of the entries in `entries` are not unique"
                ),
                values=license_ids,
            )

    def __getitem__(self, key: str) -> LicenseEntry:
        """
        Get [`LicenseEntry`][input4mips_validation.cvs.license.LicenseEntry] by its name

        We return the license entry whose license matches ``key``.
        """
        matching = [v for v in self.entries if v.license_id == key]
        if not matching:
            msg = f"{key!r}. {self.license_ids=!r}"
            raise KeyError(msg)

        if len(matching) > 1:  # pragma: no cover
            msg = "`license_id`'s should be validated as being unique at initialisation"
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
            The `license_id`'s found in the list of entries
        """
        return tuple(v.license_id for v in self.entries)


def convert_unstructured_cv_to_license_entries(
    unstructured: LicenseEntriesUnstructured,
) -> LicenseEntries:
    """
    Convert the raw CV data to a [`LicenseEntries`][input4mips_validation.cvs.license.LicenseEntries]

    Parameters
    ----------
    unstructured
        Unstructured CV data

    Returns
    -------
        License entries
    """  # noqa: E501
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
    Convert a [`LicenseEntries`][input4mips_validation.cvs.license.LicenseEntries] to the raw CV form

    Parameters
    ----------
    license_entries
        License entries

    Returns
    -------
        Raw CV data
    """  # noqa: E501
    unstructured = converter_json.unstructure(license_entries)

    raw_cv_form = {
        entry["license_id"]: entry["values"] for entry in unstructured["entries"]
    }

    return raw_cv_form


def load_license_entries(
    raw_cvs_loader: RawCVLoader,
    filename: str = LICENSE_FILENAME,
) -> LicenseEntries:
    """
    Load the license entries in the CVs

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
        Loaded license entries
    """
    return convert_unstructured_cv_to_license_entries(
        json.loads(raw_cvs_loader.load_raw(filename=filename))
    )
