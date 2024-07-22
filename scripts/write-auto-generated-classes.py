"""
Write a file we can use as our docs building environment on RtD
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import typer
from attrs import define

SRC = Path(__file__).parent.parent / "src" / "input4mips-validation"


def get_files_to_write() -> Iterable[FileToWrite]:
    file_raw_database = FileToWrite(
        SRC / "database" / "raw.py",
    )
    return [file_raw_database]


def main() -> None:
    """
    Write our auto-generated classes
    """
    files_to_write = get_files_to_write()

    for file in files_to_write:
        file.write()


if __name__ == "__main__":
    typer.run(main)
