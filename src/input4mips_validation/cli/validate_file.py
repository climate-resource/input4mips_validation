"""
Validate file command

Validate a single file
(to the extent possible given that some information is only verifiable with a tree).
"""
from __future__ import annotations

from pathlib import Path

import click

from input4mips_validation.cli.root import root_cli
from input4mips_validation.validation import assert_file_is_valid


@root_cli.command(name="validate-file")
@click.argument(
    "filepath",
    type=click.Path(exists=True, dir_okay=False, file_okay=True),
)
def validate_file_command(filepath: str) -> None:
    """
    Validate a single file

    This validation is only partial
    because some validation can only be performed if we have the entire file tree.
    See the ``validate-tree`` command for this validation.
    (Note: ``validate-tree`` is currently still under development).

    FILEPATH is the path to the file to validate.
    """
    assert_file_is_valid(Path(filepath))
