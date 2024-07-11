"""
Command-line interface
"""

from pathlib import Path
from typing import Annotated

import typer

from input4mips_validation.cli.cli_logging import setup_logging
from input4mips_validation.validation import validate_file

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
    cv_source: Annotated[
        str,
        typer.Option(
            help=(
                """String identifying the source of the CVs.

If not supplied, this is retrieved from the environment variable
``INPUT4MIPS_VALIDATION_CV_SOURCE``.

If this environment variable is also not set,
we raise a ``NotImplementedError``.

If this starts with "gh:", we retrieve the data from PCMD's GitHub,
using everything after the colon as the ID for the Git commit to use
(where the ID can be a branch name, a tag or a commit ID).

Otherwise we simply return the path as provided
and use the {py:mod}`validators` package
to decide if the source points to a URL or not.
"""
            ),
            show_default=False,
        ),
    ] = "not_set",
) -> None:
    """
    Validate a single file

    This validation is only partial
    because some validation can only be performed if we have the entire file tree.
    See the ``validate-tree`` command for this validation.
    (Note: ``validate-tree`` is currently still under development).

    FILEPATH is the path to the file to validate.
    """
    # Work around the fact typer does not support an input with type str | None yet
    if cv_source == "not_set":
        cv_source_use = None
    else:
        cv_source_use = cv_source

    validate_file(filepath, cv_source=cv_source_use)


_typer_click_object = typer.main.get_command(app)
"""
Click object, only created so we can use sphinx-click for documentation.

May be removed if there is a better answer to this,
see https://github.com/tiangolo/typer/issues/200.
"""

if __name__ == "__main__":
    app()
