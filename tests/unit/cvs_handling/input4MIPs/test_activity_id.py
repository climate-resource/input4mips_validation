"""
Test handling of the activity ID CV
"""
from __future__ import annotations

import collections
import re

import pytest

from input4mips_validation.cvs_handling.exceptions import NonUniqueError
from input4mips_validation.cvs_handling.input4MIPs.activity_id import (
    ActivityIDEntries,
    ActivityIDEntry,
    ActivityIDValues,
)


def test_conflicting_activity_ids():
    activity_id = "activity-id-1"
    activity_id_different = "activity-id-1837"
    values = ActivityIDValues(
        URL="www.placeholder.invalid",
        long_name="Long name here",
    )

    occurence_counts = collections.Counter(
        [activity_id, activity_id, activity_id_different]
    ).most_common()
    error_msg = (
        "The activity_id's of the entries in ``entries`` are not unique. "
        f"{occurence_counts=}"
    )
    with pytest.raises(NonUniqueError, match=re.escape(error_msg)):
        ActivityIDEntries(
            (
                ActivityIDEntry(activity_id=activity_id, values=values),
                ActivityIDEntry(activity_id=activity_id, values=values),
                ActivityIDEntry(activity_id=activity_id_different, values=values),
            )
        )


def test_activity_id_entries_convenience_methods():
    entries = [
        ActivityIDEntry(
            activity_id=f"activity_id_{i}",
            values=ActivityIDValues(
                URL=f"www.tbd-{i}.invalid",
                long_name=f"Test value {i}",
            ),
        )
        for i in range(3)
    ]

    activity_id_entries = ActivityIDEntries(entries)

    assert len(activity_id_entries) == 3

    # Check that we can iterate
    assert [v for v in activity_id_entries] == activity_id_entries.entries

    # Check access via activity_id
    assert activity_id_entries["activity_id_1"].activity_id == "activity_id_1"
    assert activity_id_entries["activity_id_2"].activity_id == "activity_id_2"

    # Check key error raises if we try and access something that isn't there
    with pytest.raises(
        KeyError,
        match=re.escape(
            f"'activity_id_3'. self.activity_ids={activity_id_entries.activity_ids!r}"
        ),
    ):
        activity_id_entries["activity_id_3"]
