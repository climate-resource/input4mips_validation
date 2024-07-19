"""
Command-line interface
"""

from pathlib import Path
from typing import Annotated, Union

import typer

import input4mips_validation.cli.logging
from input4mips_validation.validation import validate_file

app = typer.Typer()

CV_SOURCE_TYPE = Annotated[
    str,
    typer.Option(
        help=(
            """String identifying the source of the CVs.

If not supplied, this is retrieved from the environment variable
``INPUT4MIPS_VALIDATION_CV_SOURCE``.

If this environment variable is also not set,
we raise a ``NotImplementedError``.

If this starts with "gh:", we retrieve the data from PCMD's GitHub,
using everything after the colon as the ID for the Git object to use
(where the ID can be a branch name, a tag or a commit ID).

Otherwise we simply return the path as provided
and use the {py:mod}`validators` package
to decide if the source points to a URL or not
(i.e. whether we should look for the CVs locally or retrieve them from a URL).
"""
        ),
        show_default=False,
    ),
]

CV_SOURCE_UNSET_VALUE: str = "not_set_idjunk"
"""
Default value for CV source at the CLI

If cv_source equals this value, we assume that it wasn't passed by the user.
"""


@app.callback()
def cli(setup_logging: bool = True) -> None:
    """
    Entrypoint for the command-line interface
    """
    if not setup_logging:
        # If you want fully configurable logging from the CLI,
        # please make an issue or PRs welcome :)
        input4mips_validation.cli.logging.setup_logging()


def get_cv_source(cv_source: str, cv_source_unset_value: str) -> Union[str, None]:
    """
    Get CV source as the type we actually want.

    This is a workaround
    for the fact that typer does not support an input with type `str | None` yet.

    Parameters
    ----------
    cv_source
        CV source as received from the CLI (always a string)

    cv_source_unset_value
        Value which indicates that CV source was not set at the command-line.

    Returns
    -------
        CV source, translated into the type we actually want.
    """
    # Work around the fact typer does not support an input with type str | None yet
    if cv_source == cv_source_unset_value:
        cv_source_use = None
    else:
        cv_source_use = cv_source

    return cv_source_use


@app.command(name="validate-file")
def validate_file_command(
    file: Annotated[
        Path,
        typer.Argument(
            help="The file to validate", exists=True, dir_okay=False, file_okay=True
        ),
    ],
    cv_source: CV_SOURCE_TYPE = CV_SOURCE_UNSET_VALUE,
) -> None:
    """
    Validate a single file

    This validation is only partial
    because some validation can only be performed if we have the entire file tree.
    See the ``validate-tree`` command for this validation.
    """
    cv_source_use = get_cv_source(
        cv_source, cv_source_unset_value=CV_SOURCE_UNSET_VALUE
    )

    validate_file(file, cv_source=cv_source_use)


@app.command(name="validate-tree")
def validate_tree_command(
    tree_root: Annotated[
        Path,
        typer.Argument(
            help="The root of the tree to validate",
            exists=True,
            dir_okay=True,
            file_okay=False,
        ),
    ],
    cv_source: CV_SOURCE_TYPE = CV_SOURCE_UNSET_VALUE,
) -> None:
    """
    Validate a tree of files

    This checks things like whether all external variables are also provided
    and all tracking IDs are unique.
    """
    raise NotImplementedError()
    # cv_source_use = get_cv_source(
    #     cv_source, cv_source_unset_value=CV_SOURCE_UNSET_VALUE
    # )
    #
    # validate_tree(root=tree_root, cv_source=cv_source_use)


_typer_click_object = typer.main.get_command(app)
"""
Click object, only created so we can use sphinx-click for documentation.

May be removed if there is a better answer to this,
see https://github.com/tiangolo/typer/issues/200.
"""

if __name__ == "__main__":
    app()
