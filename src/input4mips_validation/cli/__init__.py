"""
Command-line interface
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Optional

import iris
import rich
import typer
from loguru import logger

import input4mips_validation.cli.logging
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.database.creation import create_db_file_entries
from input4mips_validation.inference.from_data import infer_time_start_time_end
from input4mips_validation.serialisation import converter_json, json_dumps_cv_style
from input4mips_validation.validation import (
    InvalidFileError,
    InvalidTreeError,
    validate_file,
    validate_tree,
)
from input4mips_validation.xarray_helpers.iris import ds_from_iris_cubes

app = typer.Typer()

CV_SOURCE_TYPE = Annotated[
    Optional[str],
    typer.Option(
        help=(
            "String identifying the source of the CVs. "
            "If not supplied, this is retrieved from the environment variable "
            "``INPUT4MIPS_VALIDATION_CV_SOURCE``. "
            ""
            "If this environment variable is also not set, "
            "we raise a ``NotImplementedError``. "
            ""
            "If this starts with 'gh:', we retrieve the data from PCMD's GitHub, "
            "using everything after the colon as the ID for the Git object to use "
            "(where the ID can be a branch name, a tag or a commit ID). "
            ""
            "Otherwise we simply return the path as provided and use the "
            "[validators][https://validators.readthedocs.io/en/stable] "
            "package to decide if the source points to a URL or not "
            "(i.e. whether we should look for the CVs locally "
            "or retrieve them from a URL)."
        ),
    ),
]

BNDS_COORD_INDICATOR_TYPE = Annotated[
    str,
    typer.Option(
        help=(
            "String that indicates that a variable is a bounds co-ordinate. "
            "This helps us with identifying `infile`'s variables correctly "
            "in the absence of an agreed convention for doing this "
            "(xarray has a way, "
            "but it conflicts with the CF-conventions hence iris, "
            "so here we are)."
        )
    ),
]

FREQUENCY_METADATA_KEY_TYPE = Annotated[
    str,
    typer.Option(
        help=(
            "The key in the data's metadata "
            "which points to information about the data's frequency. "
            "Only required if --write-in-drs or --create-db-entry are supplied."
        )
    ),
]

NO_TIME_AXIS_FREQUENCY_TYPE = Annotated[
    str,
    typer.Option(
        help=(
            "The value of `frequency_metadata_key` in the metadata which indicates "
            "that the file has no time axis i.e. is fixed in time."
            "Only required if --write-in-drs or --create-db-entry are supplied."
        )
    ),
]

TIME_DIMENSION_TYPE = Annotated[
    str,
    typer.Option(
        help=(
            "The time dimension of the data. "
            "Only required if --write-in-drs or --create-db-entry are supplied."
        )
    ),
]

VERBOSE_TYPE = Annotated[
    int,
    typer.Option(
        "--verbose",
        "-v",
        count=True,
        help=(
            "Increase the verbosity of the output "
            "(the verbosity flag is equal to the number of times the flag is supplied, "
            "e.g. `-vvv` sets the verbosity to 3)."
            "(Despite what the help says, this is a boolean flag input, "
            "If you try and supply an integer, e.g. `-v 3`, you will get an error.)"
        ),
    ),
]


@app.callback()
def cli(setup_logging: bool = True) -> None:
    """
    Entrypoint for the command-line interface
    """
    if not setup_logging:
        # If you want fully configurable logging from the CLI,
        # please make an issue or PRs welcome :)
        input4mips_validation.cli.logging.setup_logging()


@app.command(name="validate-file")
def validate_file_command(  # noqa: PLR0913
    file: Annotated[
        Path,
        typer.Argument(
            help="The file to validate", exists=True, dir_okay=False, file_okay=True
        ),
    ],
    cv_source: CV_SOURCE_TYPE = None,
    write_in_drs: Annotated[
        Optional[Path],
        typer.Option(
            help=(
                "If supplied, "
                "the file will be re-written into the DRS if it passes validation."
                "The supplied value is assumed to be the root directory "
                "into which to write the file (following the DRS)."
            ),
            show_default=False,
        ),
    ] = None,
    create_db_entry: Annotated[
        bool,
        typer.Option(
            help=(
                "Should a database entry be created? "
                "If `True`, we will attempt to create a database entry. "
                "This database entry will be logged to the screen. "
                "For creation of a database based on a tree, "
                "use the `validate-tree` command."
            ),
        ),
    ] = False,
    bnds_coord_indicator: BNDS_COORD_INDICATOR_TYPE = "bnds",
    frequency_metadata_key: FREQUENCY_METADATA_KEY_TYPE = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_TYPE = "fx",
    time_dimension: TIME_DIMENSION_TYPE = "time",
    verbose: VERBOSE_TYPE = 0,
) -> None:
    """
    Validate a single file

    This validation is only partial
    because some validation can only be performed if we have the entire file tree.
    See the ``validate-tree`` command for this validation.
    """
    try:
        validate_file(file, cv_source=cv_source)
    except InvalidFileError:
        if verbose >= 1:
            logger.exception("Validation failed")

        typer.Exit(code=1)

    if write_in_drs:
        raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
        cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

        ds = ds_from_iris_cubes(
            iris.load(file), bnds_coord_indicator=bnds_coord_indicator
        )

        time_start, time_end = infer_time_start_time_end(
            ds=ds,
            frequency_metadata_key=frequency_metadata_key,
            no_time_axis_frequency=no_time_axis_frequency,
            time_dimension=time_dimension,
        )

        full_file_path = cvs.DRS.get_file_path(
            root_data_dir=write_in_drs,
            available_attributes=ds.attrs,
            time_start=time_start,
            time_end=time_end,
        )
        write_path = full_file_path.parent / file.name

        if write_path.exists():
            raise NotImplementedError()

        write_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"Copying {file} to {write_path}")
        shutil.copy(file, write_path)

    if create_db_entry:
        if write_in_drs:
            db_entry_creation_file = write_path
        else:
            db_entry_creation_file = file

            # Also load the CVs, as they won't be loaded yet
            raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
            cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

        database_entry = Input4MIPsDatabaseEntryFile.from_file(
            db_entry_creation_file,
            cvs=cvs,
            frequency_metadata_key=frequency_metadata_key,
            no_time_axis_frequency=no_time_axis_frequency,
            time_dimension=time_dimension,
        )

        logger.info(f"{database_entry=}")
        rich.print("Database entry as JSON:")
        rich.print(json_dumps_cv_style(converter_json.unstructure(database_entry)))


@app.command(name="validate-tree")
def validate_tree_command(  # noqa: PLR0913
    tree_root: Annotated[
        Path,
        typer.Argument(
            help="The root of the tree to validate",
            exists=True,
            dir_okay=True,
            file_okay=False,
        ),
    ],
    cv_source: CV_SOURCE_TYPE = None,
    bnds_coord_indicator: BNDS_COORD_INDICATOR_TYPE = "bnds",
    frequency_metadata_key: FREQUENCY_METADATA_KEY_TYPE = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_TYPE = "fx",
    time_dimension: TIME_DIMENSION_TYPE = "time",
    verbose: VERBOSE_TYPE = 0,
) -> None:
    """
    Validate a tree of files

    This checks things like whether all external variables are also provided
    and all tracking IDs are unique.
    """
    try:
        validate_tree(
            root=tree_root,
            cv_source=cv_source,
            frequency_metadata_key=frequency_metadata_key,
            no_time_axis_frequency=no_time_axis_frequency,
            time_dimension=time_dimension,
        )
    except InvalidTreeError:
        if verbose >= 1:
            logger.exception("Validation failed")

        typer.Exit(code=1)


@app.command(name="create-db")
def create_db_command(  # noqa: PLR0913
    tree_root: Annotated[
        Path,
        typer.Argument(
            help="The root of the tree for which to create the database",
            exists=True,
            dir_okay=True,
            file_okay=False,
        ),
    ],
    db_file: Annotated[
        Path,
        typer.Option(
            help=(
                "The file in which to write the database entries. "
                "At the moment, the file must not already exist. "
                "In future, we will add functionality "
                "to merge entries into an existing database."
            ),
            dir_okay=False,
            file_okay=True,
        ),
    ],
    validate: Annotated[
        bool,
        typer.Option(
            help="Should the tree be validated before the database is created?"
        ),
    ] = True,
    cv_source: CV_SOURCE_TYPE = None,
    frequency_metadata_key: FREQUENCY_METADATA_KEY_TYPE = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_TYPE = "fx",
    time_dimension: TIME_DIMENSION_TYPE = "time",
    verbose: VERBOSE_TYPE = 0,
) -> None:
    """
    Create a database from a tree of files
    """
    if db_file.exists():
        msg = "We haven't implemented functionality for merging databases yet"
        raise NotImplementedError(msg)

    if validate:
        logger.info(f"Validating {tree_root} before creating the database")
        try:
            validate_tree(
                root=tree_root,
                cv_source=cv_source,
                frequency_metadata_key=frequency_metadata_key,
                no_time_axis_frequency=no_time_axis_frequency,
                time_dimension=time_dimension,
            )
        except InvalidTreeError:
            if verbose >= 1:
                logger.exception("Validation failed")

            typer.Exit(code=1)

    else:
        logger.debug("Skipping validation")

    logger.debug("Creating database entries")
    db_entries = create_db_file_entries(
        root=tree_root,
        cv_source=cv_source,
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
        time_dimension=time_dimension,
    )
    with open(db_file, "w") as fh:
        logger.info(f"Writing database to {db_file}")
        fh.write(json_dumps_cv_style(converter_json.unstructure(db_entries)))


if __name__ == "__main__":
    app()
