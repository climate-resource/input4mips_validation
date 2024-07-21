"""
Source ID CV handling

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
from input4mips_validation.database import make_class_from_database_entry_file_fields
from input4mips_validation.exceptions import NonUniqueError
from input4mips_validation.serialisation import converter_json

SOURCE_ID_FILENAME: str = "input4MIPs_source_id.json"
"""Default name of the file in which the source ID CV is saved"""

SourceIDEntriesUnstructured: TypeAlias = dict[str, dict[str, str]]
"""Form into which source ID entries are serialised for the CVs"""


SourceIDValues = make_class_from_database_entry_file_fields(
    "SourceIDValues",
    (
        "contact",
        "further_info_url",
        "institution_id",
        "license_id",
        "mip_era",
        "source_version",
    ),
)
"""
Values defined by an source ID

For an explanation of the required fields,
see [`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile]
"""  # noqa: E501
# Adding docstrings like this is a hack while this issue is ongoing:
# https://github.com/python-attrs/attrs/issues/1309


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

    # Note: we are ok with the duplicate validation logic here,
    # because it makes implementation of our helper dunder methods
    # simpler if we can assume that the source IDs are unique.
    @entries.validator
    def _entry_source_ids_are_unique(
        self, attribute: attr.Attribute[Any], value: tuple[SourceIDEntry, ...]
    ) -> None:
        source_ids = self.source_ids
        if len(source_ids) != len(set(source_ids)):
            raise NonUniqueError(
                description=(
                    "The source_id's of the entries in `entries` are not unique"
                ),
                values=source_ids,
            )

    def __getitem__(self, key: str) -> SourceIDEntry:
        """
        Get [`SourceIDEntry`][SourceIDEntry] by its name

        We return the [`SourceIDEntry`][SourceIDEntry]
        whose source_id matches `key`.
        """
        matching = [v for v in self.entries if v.source_id == key]
        if not matching:
            msg = f"{key!r}. {self.source_ids=!r}"
            raise KeyError(msg)

        if len(matching) > 1:  # pragma: no cover
            msg = "`source_id`'s should be validated as being unique at initialisation"
            raise AssertionError(msg)

        return matching[0]

    def __iter__(self) -> Iterable[SourceIDEntry]:
        """
        Iterate over `self.entries`
        """
        yield from self.entries

    def __len__(self) -> int:
        """
        Get length of `self.entries`
        """
        return len(self.entries)

    @property
    def source_ids(self) -> tuple[str, ...]:
        """
        Source IDs found in the list of entries

        Returns
        -------
            The `source_id`'s found in the list of entries
        """
        return tuple(v.source_id for v in self.entries)


def convert_unstructured_cv_to_source_id_entries(
    unstructured: SourceIDEntriesUnstructured,
) -> SourceIDEntries:
    """
    Convert the raw CV data to a [`SourceIDEntries`][SourceIDEntries]

    Parameters
    ----------
    unstructured
        Unstructured CV data

    Returns
    -------
        Source ID entries
    """
    restructured = {
        "entries": [
            dict(source_id=key, values=value) for key, value in unstructured.items()
        ]
    }

    return converter_json.structure(restructured, SourceIDEntries)


def convert_source_id_entries_to_unstructured_cv(
    source_id_entries: SourceIDEntries,
) -> SourceIDEntriesUnstructured:
    """
    Convert a [`SourceIDEntries`][SourceIDEntries] to the raw CV form

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
        entry["source_id"]: entry["values"] for entry in unstructured["entries"]
    }

    return raw_cv_form


def load_source_id_entries(
    raw_cvs_loader: RawCVLoader,
    filename: str = SOURCE_ID_FILENAME,
) -> SourceIDEntries:
    """
    Load the source_id entries in the CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of raw CVs data.

    filename
        Name of the file from which to load the CVs.

        Passed to
        [`raw_cvs_loader.load_raw`][input4mips_validation.loading_raw.RawCVLoader.load_raw].

    Returns
    -------
        Loaded source ID entries
    """
    return convert_unstructured_cv_to_source_id_entries(
        json.loads(raw_cvs_loader.load_raw(filename=filename))
    )
