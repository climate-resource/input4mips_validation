"""
Source ID CV handling
"""
from __future__ import annotations

import json
from typing import Any, TypeAlias

import attr
from attrs import define, field

from input4mips_validation.cvs_handling.exceptions import NonUniqueError
from input4mips_validation.cvs_handling.input4MIPs.serialisation import converter_json

SOURCE_ID_FILENAME: str = "input4MIPs_source_id.json"
"""Default name of the file in which the source ID CV is saved"""

SourceIDEntriesSerialised: TypeAlias = dict[str, dict[str, dict[str, str]]]
"""Form into which source ID entries are serialised for the CVs"""


@define
class SourceIDValues:
    """
    Values defined by a source ID
    """

    activity_id: str
    """ID of the activity to which this source is contributing"""
    # TODO: add validation from activity ID JSON

    contact: str
    """Email addresses to contact in case of questions"""
    # TODO: add email validation

    further_info_url: str
    """URL where further information about this source can be found"""
    # TODO: add validation

    institution: str
    """Institution which provides this source"""
    # No validation, can be any string

    institution_id: str
    """ID of the institution which provides this source"""
    # TODO: add validation

    license: str
    """License information for data coming from this source"""
    # TODO: add validation

    mip_era: str
    """MIP era to which this source is contributing"""
    # TODO: add validation

    version: str
    """Version identifier for data associated with this source"""


@define
class SourceIDEntry:
    """
    A single source ID entry
    """

    source_id: str
    """The unique value which identifies this source ID"""

    values: SourceIDValues
    """The values defined by this source ID"""


@define
class SourceIDEntries:
    """
    Helper container for handling source ID entries
    """

    entries: tuple[SourceIDEntry, ...] = field()
    """Source ID entries"""

    @entries.validator
    def _entry_source_ids_are_unique(
        self, attribute: attr.Attribute[Any], value: tuple[SourceIDEntry, ...]
    ) -> None:
        source_ids = self.source_ids
        if len(source_ids) != len(set(source_ids)):
            raise NonUniqueError(
                description=(
                    "The source_id's of the entries in ``entries`` are not unique"
                ),
                values=source_ids,
            )

    def __getitem__(self, key: str) -> SourceIDEntry:
        """
        Get {py:obj}`SourceIDEntry` by its name

        We return the {py:obj}`SourceIDEntry` whose source_id
        matches ``key``.
        """
        matching = [v for v in self.entries if v.source_id == key]
        if not matching:
            raise KeyError(key)

        if len(matching) > 1:
            msg = "source IDs should be validated as being unique at initialisation"
            raise AssertionError(msg)

        return matching[0]

    def __len__(self) -> int:
        """
        Get length of ``self.entries``
        """
        return len(self.entries)

    @property
    def source_ids(self) -> tuple[str, ...]:
        """
        Source IDs found in the list of entries

        Returns
        -------
            The source IDs found in the list of entries
        """
        return tuple(v.source_id for v in self.entries)


def convert_raw_cv_to_source_id_entries(
    raw: SourceIDEntriesSerialised,
) -> SourceIDEntries:
    """
    Convert the raw CV data to a {py:obj}`SourceIDEntries`

    Parameters
    ----------
    raw
        Raw CV data

    Returns
    -------
        Source ID entries
    """
    raw_json = json.loads(raw)
    restructured = {
        "entries": [
            dict(source_id=key, values=value)
            for key, value in raw_json["source_id"].items()
        ]
    }

    return converter_json.structure(restructured, SourceIDEntries)


def convert_source_id_entries_to_raw_cv(
    source_id_entries: SourceIDEntries,
) -> SourceIDEntriesSerialised:
    """
    Convert a {py:obj}`SourceIDEntries` to the raw CV form

    Parameters
    ----------
    source_id_entries
        Source ID entries

    Returns
    -------
        Raw CV data
    """
    unstructured = converter_json.unstructure(source_id_entries)

    raw_cv_form = {
        "source_id": {
            entry["source_id"]: entry["values"] for entry in unstructured["entries"]
        }
    }

    return raw_cv_form
