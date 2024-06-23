"""
Test handling of the source ID CV
"""
from __future__ import annotations

import collections
import re

import pytest

from input4mips_validation.cvs_handling.exceptions import NonUniqueError
from input4mips_validation.cvs_handling.input4MIPs.source_id import (
    SourceIDEntries,
    SourceIDEntry,
    SourceIDValues,
)


def test_conflicting_source_ids():
    source_id = "source-id-1"
    source_id_different = "source-id-1837"
    values = SourceIDValues(
        activity_id="placeholder",
        contact="placeholder",
        further_info_url="placeholder",
        institution="placeholder",
        institution_id="placeholder",
        license="placeholder",
        mip_era="placeholder",
        version="placeholder",
    )

    occurence_counts = collections.Counter(
        [source_id, source_id, source_id_different]
    ).most_common()
    error_msg = (
        "The source_id's of the entries in ``entries`` are not unique. "
        f"{occurence_counts=}"
    )
    with pytest.raises(NonUniqueError, match=re.escape(error_msg)):
        SourceIDEntries(
            (
                SourceIDEntry(source_id=source_id, values=values),
                SourceIDEntry(source_id=source_id, values=values),
                SourceIDEntry(source_id=source_id_different, values=values),
            )
        )


def test_source_id_entries_convenience_methods():
    entries = [
        SourceIDEntry(
            source_id=f"source_id_{i}",
            values=SourceIDValues(
                activity_id=f"placeholder_{i}",
                contact=f"placeholder_{i}",
                further_info_url=f"placeholder_{i}",
                institution=f"placeholder_{i}",
                institution_id=f"placeholder_{i}",
                license=f"placeholder_{i}",
                mip_era=f"placeholder_{i}",
                version=f"placeholder_{i}",
            ),
        )
        for i in range(3)
    ]

    source_id_entries = SourceIDEntries(entries)

    assert len(source_id_entries) == 3

    # Check that we can iterate
    assert [v for v in source_id_entries] == source_id_entries.entries

    # Check access via indexes
    assert source_id_entries[0].source_id == "source_id_0"
    assert source_id_entries[2].source_id == "source_id_2"

    # Check access via source_id
    assert source_id_entries["source_id_1"].source_id == "source_id_1"
    assert source_id_entries["source_id_2"].source_id == "source_id_2"

    # Check key error raises if we try and access something that isn't there
    with pytest.raises(
        KeyError,
        match=re.escape(
            f"'source_id_3'. self.source_ids={source_id_entries.source_ids!r}"
        ),
    ):
        source_id_entries["source_id_3"]
