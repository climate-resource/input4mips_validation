"""
Hashing tools
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def get_file_hash_sha256(file: Path, buffer_size: int = 2**30) -> str:
    """
    Get a file's sha256 hash

    This reads the file in chunks to avoid blowing memory to pieces.

    Parameters
    ----------
    file
        File to hash

    buffer_size
        Size of buffer to read.

        The default is around 1GB.

    Returns
    -------
    :
        SHA256 of the file
    """
    sha256 = hashlib.sha256()

    # Shouldn't need more iterations than this
    # (there is a factor of 10 buffer).
    # If we do, something has gone wrong.
    max_iter = 10 * (1 + int(file.stat().st_size / buffer_size))
    with open(file, "rb") as fh:
        for _ in range(max_iter):
            data = fh.read(buffer_size)
            if not data:
                break

            sha256.update(data)

        else:
            msg = "Should have finished calculating the sha256 by now"
            raise AssertionError(msg)

    return sha256.hexdigest()
