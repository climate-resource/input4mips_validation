"""
Database handling from the CLI
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from loguru import logger

from input4mips_validation.cli.common_arguments_and_options import (
    CV_SOURCE_OPTION,
    FREQUENCY_METADATA_KEY_OPTION,
    N_PROCESSES_OPTION,
    NO_TIME_AXIS_FREQUENCY_OPTION,
    RGLOB_INPUT_OPTION,
    TIME_DIMENSION_OPTION,
)
from input4mips_validation.database import dump_database_file_entries
from input4mips_validation.database.creation import create_db_file_entries

app = typer.Typer()


# create_db_entry: Annotated[
#     bool,
#     typer.Option(
#         help=(
#             "Should a database entry be created? "
#             "If `True`, we will attempt to create a database entry. "
#             "This database entry will be logged to the screen. "
#             "For creation of a database based on a tree, "
#             "use the `validate-tree` command."
#         ),
#     ),
# ] = False,
# if create_db_entry:
#     if write_in_drs:
#         db_entry_creation_file = full_file_path
#     else:
#         db_entry_creation_file = file
#
#         # Also load the CVs, as they won't be loaded yet
#         raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
#         cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)
#
#     database_entry = Input4MIPsDatabaseEntryFile.from_file(
#         db_entry_creation_file,
#         cvs=cvs,
#         frequency_metadata_key=frequency_metadata_key,
#         no_time_axis_frequency=no_time_axis_frequency,
#         time_dimension=time_dimension,
#     )
#
#     logger.info(f"{database_entry=}")
#     rich.print("Database entry as JSON:")
#     rich.print(json_dumps_cv_style(converter_json.unstructure(database_entry)))
@app.command(name="create")
def db_create_command(  # noqa: PLR0913
    tree_root: Annotated[
        Path,
        typer.Argument(
            help="The root of the tree for which to create the database",
            exists=True,
            dir_okay=True,
            file_okay=False,
        ),
    ],
    db_dir: Annotated[
        Path,
        typer.Option(
            help="The directory in which to write the database entries. ",
            dir_okay=True,
            file_okay=False,
        ),
    ],
    cv_source: CV_SOURCE_OPTION = None,
    frequency_metadata_key: FREQUENCY_METADATA_KEY_OPTION = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_OPTION = "fx",
    time_dimension: TIME_DIMENSION_OPTION = "time",
    rglob_input: RGLOB_INPUT_OPTION = "*.nc",
    n_processes: N_PROCESSES_OPTION = 4,
) -> None:
    """
    Create a database from a tree of files
    """
    if db_dir.exists():
        msg = "If using `create`, the database directory must not already exist"
        raise FileExistsError(msg)

    db_entries = create_db_file_entries(
        root=tree_root,
        cv_source=cv_source,
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
        time_dimension=time_dimension,
        rglob_input=rglob_input,
        n_processes=n_processes,
    )

    logger.debug(f"Creating {db_dir}")
    db_dir.mkdir(parents=True, exist_ok=False)
    dump_database_file_entries(entries=db_entries, db_dir=db_dir)


# if validate:
#     try:
#         validate_tree(
#             root=tree_root,
#             cv_source=cv_source,
#             frequency_metadata_key=frequency_metadata_key,
#             no_time_axis_frequency=no_time_axis_frequency,
#             time_dimension=time_dimension,
#             rglob_input=rglob_input,
#         )
#     except InvalidFileError as exc:
#         logger.debug(f"{type(exc).__name__}: {exc}")
#
#         raise typer.Exit(code=1) from exc


if __name__ == "__main__":
    app()
