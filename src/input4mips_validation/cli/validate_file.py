"""
Validate file command

Validate a single file
(to the extent possible given that some information is only verifiable with a tree).
"""
from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from input4mips_validation.cli.root import app
from input4mips_validation.validation import assert_file_is_valid


@app.command(name="validate-file")
def validate_file_command(
    filepath: Annotated[
        Path, typer.Option(exists=True, dir_okay=False, file_okay=True)
    ],
) -> None:
    """
    Validate a single file

    This validation is only partial
    because some validation can only be performed if we have the entire file tree.
    See the ``validate-tree`` command for this validation.
    (Note: ``validate-tree`` is currently still under development).

    FILEPATH is the path to the file to validate.
    """
    assert_file_is_valid(filepath)
