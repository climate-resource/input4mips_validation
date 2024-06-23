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
