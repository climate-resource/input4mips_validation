"""
Command-line interface
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Optional

import iris
import typer
from loguru import logger

import input4mips_validation
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.database.creation import create_db_file_entries
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.inference.from_data import infer_time_start_time_end
from input4mips_validation.logging import setup_logging
from input4mips_validation.serialisation import converter_json, json_dumps_cv_style
from input4mips_validation.upload_ftp import upload_ftp
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
        )
    ),
]

NO_TIME_AXIS_FREQUENCY_TYPE = Annotated[
    str,
    typer.Option(
        help=(
            "The value of `frequency_metadata_key` in the metadata which indicates "
            "that the file has no time axis i.e. is fixed in time."
        )
    ),
]

TIME_DIMENSION_TYPE = Annotated[
    str,
    typer.Option(help=("The time dimension of the data.")),
]

RGLOB_INPUT_TYPE = Annotated[
    str,
    typer.Option(help=("String to use when applying `rglob` to find input files.")),
]

ALLOW_CF_CHECKER_WARNINGS_TYPE = Annotated[
    bool,
    typer.Option(
        "--allow-cf-checker-warnings",
        help="Allow validation to pass, even if the CF-checker raises warnings",
    ),
]

# May be handy, although my current feeling is that logging via loguru
# can offer same thing with much better control.
# VERBOSE_TYPE = Annotated[
#     int,
#     typer.Option(
#         "--verbose",
#         "-v",
#         count=True,
#         help=(
#             "Increase the verbosity of the output "
#             "(the verbosity flag is equal to the number of times "
#             "the flag is supplied, "
#             "e.g. `-vvv` sets the verbosity to 3)."
#             "(Despite what the help says, this is a boolean flag input, "
#             "If you try and supply an integer, e.g. `-v 3`, you will get an error.)"
#         ),
#     ),
# ]


def version_callback(version: Optional[bool]) -> None:
    """
    If requested, print the version string and exit
    """
    if version:
        print(f"input4mips-validation {input4mips_validation.__version__}")
        raise typer.Exit(code=0)


@app.callback()
def cli(
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            help="Print the version number and exit",
            callback=version_callback,
            is_eager=True,
        ),
    ] = None,
    no_logging: Annotated[
        Optional[bool],
        typer.Option(
            "--no-logging",
            help="""Disable all logging.

If supplied, overrides '--logging-config'""",
        ),
    ] = None,
    logging_level: Annotated[
        Optional[str],
        typer.Option(
            help="""Logging level to use.

This is only applied if no other logging configuration flags are supplied."""
        ),
    ] = None,
    logging_config: Annotated[
        Optional[Path],
        typer.Option(
            help="""Path to the logging configuration file.

This will be loaded with [loguru-config](https://github.com/erezinman/loguru-config).
If supplied, this overrides any value provided with `--log-level`."""
        ),
    ] = None,
) -> None:
    """
    Entrypoint for the command-line interface
    """
    if no_logging:
        setup_logging(enable=False)

    else:
        setup_logging(
            enable=True, logging_config=logging_config, logging_level=logging_level
        )


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
    bnds_coord_indicator: BNDS_COORD_INDICATOR_TYPE = "bnds",
    frequency_metadata_key: FREQUENCY_METADATA_KEY_TYPE = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_TYPE = "fx",
    time_dimension: TIME_DIMENSION_TYPE = "time",
    allow_cf_checker_warnings: ALLOW_CF_CHECKER_WARNINGS_TYPE = False,
) -> None:
    """
    Validate a single file

    This validation is only partial
    because some validation can only be performed if we have the entire file tree.
    See the ``validate-tree`` command for this validation.
    """
    try:
        validate_file(
            file,
            cv_source=cv_source,
            allow_cf_checker_warnings=allow_cf_checker_warnings,
        )
    except InvalidFileError as exc:
        logger.debug(f"{type(exc).__name__}: {exc}")

        raise typer.Exit(code=1) from exc

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

        if full_file_path.exists():
            logger.error("We will not overwrite existing files")
            raise FileExistsError(full_file_path)

        full_file_path.parent.mkdir(parents=True, exist_ok=True)

        if full_file_path.name != file.name:
            logger.info(f"Re-writing {file} to {full_file_path}")
            Input4MIPsDataset.from_ds(ds, cvs=cvs).write(
                root_data_dir=write_in_drs,
                frequency_metadata_key=frequency_metadata_key,
                no_time_axis_frequency=no_time_axis_frequency,
                time_dimension=time_dimension,
            )

        else:
            logger.info(f"Copying {file} to {full_file_path}")
            shutil.copy(file, full_file_path)

        logger.success(f"File written according to the DRS in {full_file_path}")


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
    rglob_input: RGLOB_INPUT_TYPE = "*.nc",
    allow_cf_checker_warnings: ALLOW_CF_CHECKER_WARNINGS_TYPE = False,
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
            rglob_input=rglob_input,
            allow_cf_checker_warnings=allow_cf_checker_warnings,
        )
    except InvalidTreeError as exc:
        logger.debug(f"{type(exc).__name__}: {exc}")

        raise typer.Exit(code=1) from exc


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
    rglob_input: RGLOB_INPUT_TYPE = "*.nc",
) -> None:
    """
    Create a database from a tree of files
    """
    if db_file.exists():
        msg = "We haven't implemented functionality for merging databases yet"
        raise NotImplementedError(msg)

    if validate:
        try:
            validate_tree(
                root=tree_root,
                cv_source=cv_source,
                frequency_metadata_key=frequency_metadata_key,
                no_time_axis_frequency=no_time_axis_frequency,
                time_dimension=time_dimension,
                rglob_input=rglob_input,
            )
        except InvalidFileError as exc:
            logger.debug(f"{type(exc).__name__}: {exc}")

            raise typer.Exit(code=1) from exc

    db_entries = create_db_file_entries(
        root=tree_root,
        cv_source=cv_source,
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
        time_dimension=time_dimension,
        rglob_input=rglob_input,
    )
    with open(db_file, "w") as fh:
        fh.write(json_dumps_cv_style(converter_json.unstructure(db_entries)))


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


@app.command(name="upload-ftp")
def upload_ftp_command(  # noqa: PLR0913
    tree_root: Annotated[
        Path,
        typer.Argument(
            help="The root of the tree to upload",
            exists=True,
            dir_okay=True,
            file_okay=False,
        ),
    ],
    ftp_dir_rel_to_root: Annotated[
        str,
        typer.Option(
            help="""Directory, relative to `root_dir_ftp_incoming_files`, in which to upload the files on the FTP server.

For example, "my-institute-input4mips"
"""  # noqa: E501
        ),
    ],
    password: Annotated[
        str,
        typer.Option(
            help="""Password to use when logging in.

If you are uploading to LLNL's FTP server,
please use your email address here."""
        ),
    ],
    username: Annotated[
        str,
        typer.Option(help="Username to use when logging in to the server."),
    ] = "anonymous",
    ftp_server: Annotated[
        str,
        typer.Option(help="FTP server to upload to."),
    ] = "ftp.llnl.gov",
    ftp_dir_root: Annotated[
        str,
        typer.Option(help="Root directory on the FTP server for receiving files"),
    ] = "/incoming",
    n_threads: Annotated[
        int, typer.Option(help="Number of threads to use during upload")
    ] = 4,
    cv_source: CV_SOURCE_TYPE = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help="""Perform a dry run

In other words, don't actually upload the files, but show what would be uploaded.""",
        ),
    ] = False,
) -> None:
    """
    Upload files to an FTP server

    We recommend running this with a log level of INFO to start,
    then adjusting from there.
    """
    raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source)
    logger.debug(f"{raw_cvs_loader=}")
    cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

    upload_ftp(
        tree_root=tree_root,
        ftp_dir_rel_to_root=ftp_dir_rel_to_root,
        password=password,
        cvs=cvs,
        username=username,
        ftp_server=ftp_server,
        ftp_dir_root=ftp_dir_root,
        n_threads=n_threads,
        dry_run=dry_run,
    )
    logger.success(f"Uploaded all files to {ftp_server}")


if __name__ == "__main__":
    app()
