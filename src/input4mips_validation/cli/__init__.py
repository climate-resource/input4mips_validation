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
from input4mips_validation.cli.common_arguments_and_options import (
    ALLOW_CF_CHECKER_WARNINGS_TYPE,
    BNDS_COORD_INDICATOR_TYPE,
    CV_SOURCE_OPTION,
    FREQUENCY_METADATA_KEY_OPTION,
    NO_TIME_AXIS_FREQUENCY_OPTION,
    RGLOB_INPUT_OPTION,
    TIME_DIMENSION_OPTION,
)
from input4mips_validation.cli.db import app as app_db
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.inference.from_data import infer_time_start_time_end
from input4mips_validation.logging import setup_logging
from input4mips_validation.upload_ftp import upload_ftp
from input4mips_validation.validation.file import get_validate_file_result
from input4mips_validation.validation.tree import get_validate_tree_result
from input4mips_validation.xarray_helpers.iris import ds_from_iris_cubes

app = typer.Typer()


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
            help=("Disable all logging. If supplied, overrides '--logging-config'."),
        ),
    ] = None,
    logging_level: Annotated[
        Optional[str],
        typer.Option(
            help=(
                "Logging level to use. "
                "This is only applied "
                "if no other logging configuration flags are supplied."
            ),
        ),
    ] = None,
    logging_config: Annotated[
        Optional[Path],
        typer.Option(
            help=(
                "Path to the logging configuration file. "
                "This will be loaded with "
                "[loguru-config](https://github.com/erezinman/loguru-config). "
                "If supplied, this overrides any value provided with `--log-level`."
                "For a sample configuration file, see "
                "[How to configure logging with input4MIPs-validation?][how-to-configure-logging-with-input4mips-validation]"  # noqa: E501
            )
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
    cv_source: CV_SOURCE_OPTION = None,
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
    frequency_metadata_key: FREQUENCY_METADATA_KEY_OPTION = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_OPTION = "fx",
    time_dimension: TIME_DIMENSION_OPTION = "time",
    allow_cf_checker_warnings: ALLOW_CF_CHECKER_WARNINGS_TYPE = False,
) -> None:
    """
    Validate a single file

    This validation is only partial
    because some validation can only be performed if we have the entire file tree.
    See the ``validate-tree`` command for this validation.
    """
    get_validate_file_result(
        file,
        cv_source=cv_source,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
    ).raise_if_errors()

    if write_in_drs:
        cvs = load_cvs(cv_source=cv_source)

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
    cv_source: CV_SOURCE_OPTION = None,
    bnds_coord_indicator: BNDS_COORD_INDICATOR_TYPE = "bnds",
    frequency_metadata_key: FREQUENCY_METADATA_KEY_OPTION = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_OPTION = "fx",
    time_dimension: TIME_DIMENSION_OPTION = "time",
    rglob_input: RGLOB_INPUT_OPTION = "*.nc",
    allow_cf_checker_warnings: ALLOW_CF_CHECKER_WARNINGS_TYPE = False,
    output_html: Annotated[
        Optional[Path],
        typer.Option(
            "--output-html", help="Output the result as HTML to this file too."
        ),
    ] = None,
) -> None:
    """
    Validate a tree of files

    This checks things like whether all external variables are also provided
    and all tracking IDs are unique.
    """
    vtrs = get_validate_tree_result(
        root=tree_root,
        cv_source=cv_source,
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
        time_dimension=time_dimension,
        rglob_input=rglob_input,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
    )

    if output_html is not None:
        with open(output_html, "w") as fh:
            fh.write(vtrs.to_html())

    vtrs.raise_if_errors()


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
            help=(
                "Directory, relative to `root_dir_ftp_incoming_files`, "
                "in which to upload the files on the FTP server. "
                'For example, "my-institute-input4mips".'
            )
        ),
    ],
    password: Annotated[
        str,
        typer.Option(
            help=(
                "Password to use when logging in. "
                "If you are uploading to LLNL's FTP server, "
                "please use your email address here."
            )
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
    cv_source: CV_SOURCE_OPTION = None,
    dry_run: Annotated[
        bool,
        typer.Option(
            "--dry-run",
            help=(
                "Perform a dry run. "
                "In other words, don't actually upload the files, "
                "but show what would be uploaded."
            ),
        ),
    ] = False,
    continue_on_error: Annotated[
        bool,
        typer.Option(
            "--continue-on-error",
            help=(
                "Continue trying to upload the rest of the files, "
                "even if an error is raised while trying to upload a file."
            ),
        ),
    ] = False,
) -> None:
    """
    Upload files to an FTP server

    We recommend running this with a log level of INFO to start,
    then adjusting from there.
    """
    cvs = load_cvs(cv_source=cv_source)

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
        continue_on_error=continue_on_error,
    )


app.add_typer(app_db, name="db")

if __name__ == "__main__":
    app()
