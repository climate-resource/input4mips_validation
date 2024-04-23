"""
Command-line interface
"""
from pathlib import Path
from typing import Annotated

import typer

from input4mips_validation.cli.cli_logging import setup_logging
from input4mips_validation.validation import assert_file_is_valid

app = typer.Typer()


@app.callback()
def main() -> None:
    """
    Entrypoint for the command-line interface
    """
    setup_logging()


@app.command(name="validate-file")
def validate_file_command(
    filepath: Annotated[
        Path, typer.Argument(exists=True, dir_okay=False, file_okay=True)
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


_typer_click_object = typer.main.get_command(app)
"""
Click object, only created so we can use sphinx-click for documentation.

May be removed if there is a better answer to this,
see https://github.com/tiangolo/typer/issues/200.
"""
