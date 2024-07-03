"""
Activity ID CV handling

Where validation is possible on values in isolation, we include data validation in here.
Where the validation requires knowledge about other values in the CVs,
see {py:mod}`input4mips_validation.cvs_handling.input4MIPs.validation`.
"""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any

import attr
from attrs import define, field
from typing_extensions import TypeAlias

from input4mips_validation.cvs_handling.exceptions import NonUniqueError
from input4mips_validation.cvs_handling.input4MIPs.serialisation import converter_json

# TODO: consider whether we need to remove duplication with the ``source_id`` module

ACTIVITY_ID_FILENAME: str = "input4MIPs_activity_id.json"
"""Default name of the file in which the activity ID CV is saved"""

ActivityIDEntriesUnstructured: TypeAlias = dict[str, dict[str, dict[str, str]]]
"""Form into which activity ID entries are serialised for the CVs"""


@define
class ActivityIDValues:
    """
    Values defined by an activity ID
    """

    long_name: str
    """Long name/description of the activity"""

    URL: str
    """URL where information about this activity can be found"""


@define
class ActivityIDEntry:
    """
    A single activity ID entry
    """

    activity_id: str
    """The unique value which identifies this activity ID"""

    values: ActivityIDValues
    """The values defined by this activity ID"""


@define
class ActivityIDEntries:
    """
    Helper container for handling activity ID entries
    """

    entries: tuple[ActivityIDEntry, ...] = field()
    """Activity ID entries"""

    @entries.validator
    def _entry_activity_ids_are_unique(
        self, attribute: attr.Attribute[Any], value: tuple[ActivityIDEntry, ...]
    ) -> None:
        activity_ids = self.activity_ids
        if len(activity_ids) != len(set(activity_ids)):
            raise NonUniqueError(
                description=(
                    "The activity_id's of the entries in ``entries`` are not unique"
                ),
                values=activity_ids,
            )

    def __getitem__(self, key: str) -> ActivityIDEntry:
        """
        Get {py:obj}`ActivityIDEntry` by its name

        We return the {py:obj}`ActivityIDEntry` whose activity_id matches ``key``.
        """
        matching = [v for v in self.entries if v.activity_id == key]
        if not matching:
            msg = f"{key!r}. {self.activity_ids=!r}"
            raise KeyError(msg)

        if len(matching) > 1:  # pragma: no cover
            msg = "activity IDs should be validated as being unique at initialisation"
            raise AssertionError(msg)

        return matching[0]

    def __iter__(self) -> Iterable[ActivityIDEntry]:
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
    def activity_ids(self) -> tuple[str, ...]:
        """
        Activity IDs found in the list of entries

        Returns
        -------
            The activity IDs found in the list of entries
        """
        return tuple(v.activity_id for v in self.entries)


def convert_unstructured_cv_to_activity_id_entries(
    unstructured: ActivityIDEntriesUnstructured,
) -> ActivityIDEntries:
    """
    Convert the raw CV data to a {py:obj}`ActivityIDEntries`

    Parameters
    ----------
    unstructured
        Unstructured CV data

    Returns
    -------
        Activity ID entries
    """
    restructured = {
        "entries": [
            dict(activity_id=key, values=value)
            for key, value in unstructured["activity_id"].items()
        ]
    }

    return converter_json.structure(restructured, ActivityIDEntries)


def convert_activity_id_entries_to_unstructured_cv(
    activity_id_entries: ActivityIDEntries,
) -> ActivityIDEntriesUnstructured:
    """
    Convert a {py:obj}`ActivityIDEntries` to the raw CV form

    Parameters
    ----------
    activity_id_entries
        Activity ID entries

    Returns
    -------
        Raw CV data
    """
    unstructured = converter_json.unstructure(activity_id_entries)

    raw_cv_form = {
        "activity_id": {
            entry["activity_id"]: entry["values"] for entry in unstructured["entries"]
        }
    }

    return raw_cv_form
