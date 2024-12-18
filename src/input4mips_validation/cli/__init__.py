"""
Command-line interface
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations

import shutil
from pathlib import Path
from typing import Annotated, Optional, Union

import iris
import typer
import xarray as xr
from loguru import logger

import input4mips_validation
from input4mips_validation.cli.common_arguments_and_options import (
    ALLOW_CF_CHECKER_WARNINGS_TYPE,
    BNDS_COORD_INDICATORS_SEPARATOR,
    BNDS_COORD_INDICATORS_TYPE,
    CV_SOURCE_OPTION,
    FREQUENCY_METADATA_KEY_OPTION,
    NO_TIME_AXIS_FREQUENCY_OPTION,
    RGLOB_INPUT_OPTION,
    TIME_DIMENSION_OPTION,
)
from input4mips_validation.cli.db import app as app_db
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.inference.from_data import (
    BoundsInfo,
    FrequencyMetadataKeys,
    infer_time_start_time_end,
)
from input4mips_validation.logging import setup_logging
from input4mips_validation.upload_ftp import upload_ftp
from input4mips_validation.validation.file import get_validate_file_result
from input4mips_validation.validation.tree import get_validate_tree_result
from input4mips_validation.xarray_helpers.iris import ds_from_iris_cubes
from input4mips_validation.xarray_helpers.variables import (
    XRVariableHelper,
    XRVariableProcessorLike,
)

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


def validate_file(  # noqa: PLR0913
    file: Path,
    cv_source: Union[str, None],
    write_in_drs: Union[Path, None],
    xr_variable_processor: XRVariableProcessorLike,
    frequency_metadata_keys: FrequencyMetadataKeys,
    bounds_info: BoundsInfo,
    time_dimension: str,
    allow_cf_checker_warnings: bool,
) -> None:
    """
    Validate a file

    Optionally, re-write the file in the DRS.

    This is the direct Python API.
    We expose this for two reasons:

    1. to make it easier for those who want to use Python rather than the CLI
    1. to ensure that we're passing all the CLI arguments correctly
       (this function has no keyword arguments, so if we forget one, the CLI won't work)

    Parameters
    ----------
    file
        File to validate.

    cv_source
        The source from which to load the CVs.

        For full details, see [`load_cvs`][input4mips_validation.cvs.load_cvs].

    write_in_drs
        If the file passes validation,
        the root directory for writing the file in the DRS.

        If `None`, the file is not written in the DRS,
        irrespective of whether it passes validation or not.

    xr_variable_processor
        Helper to use for processing the variables in xarray objects.

    frequency_metadata_keys
        Metadata definitions for frequency information

    bounds_info
        Metadata definitions for bounds handling.

    time_dimension
        The time dimension of the data

    allow_cf_checker_warnings
        Allow validation to pass, even if the CF-checker raises warnings?
    """
    if bounds_info is None:
        bounds_info_use = BoundsInfo.from_ds(
            xr.open_dataset(file),
            time_dimension=time_dimension,
        )

    else:
        bounds_info_use = bounds_info

    get_validate_file_result(
        file,
        cv_source=cv_source,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        bounds_info=bounds_info_use,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
    ).raise_if_errors()

    logger.success(f"File passed validation: {file}")

    if write_in_drs is not None:
        cvs = load_cvs(cv_source=cv_source)

        ds = ds_from_iris_cubes(
            iris.load(file),
            xr_variable_processor=xr_variable_processor,
        )

        time_start, time_end = infer_time_start_time_end(
            ds=ds,
            frequency_metadata_key=frequency_metadata_keys.frequency_metadata_key,
            no_time_axis_frequency=frequency_metadata_keys.no_time_axis_frequency,
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
                frequency_metadata_keys=frequency_metadata_keys,
                time_dimension=time_dimension,
                xr_variable_processor=xr_variable_processor,
                bounds_info=bounds_info_use,
            )

        else:
            logger.info(f"Copying {file} to {full_file_path}")
            shutil.copy(file, full_file_path)

        logger.success(f"File written according to the DRS in {full_file_path}")


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
    bnds_coord_indicators: BNDS_COORD_INDICATORS_TYPE = "bnds;bounds",
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
    xr_variable_processor = XRVariableHelper(
        bounds_coord_indicators=tuple(
            bnds_coord_indicators.split(BNDS_COORD_INDICATORS_SEPARATOR)
        )
    )
    frequency_metadata_keys = FrequencyMetadataKeys(
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
    )
    # TODO: allow this to be passed from CLI
    bounds_info = BoundsInfo.from_ds(
        xr.open_dataset(file),
        time_dimension=time_dimension,
    )

    validate_file(
        file=file,
        cv_source=cv_source,
        write_in_drs=write_in_drs,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        bounds_info=bounds_info,
        time_dimension=time_dimension,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
    )


def validate_tree(  # noqa: PLR0913
    tree_root: Path,
    cv_source: Union[str, None],
    xr_variable_processor: XRVariableProcessorLike,
    frequency_metadata_keys: FrequencyMetadataKeys,
    bounds_info: BoundsInfo,
    time_dimension: str,
    rglob_input: str,
    allow_cf_checker_warnings: bool,
    output_html: Union[Path, None],
) -> None:
    """
    Validate a tree of files

    Optionally, write the validation output out as HTML.

    This is the direct Python API.
    We expose this for two reasons:

    1. to make it easier for those who want to use Python rather than the CLI
    1. to ensure that we're passing all the CLI arguments correctly
       (this function has no keyword arguments, so if we forget one, the CLI won't work)

    Parameters
    ----------
    tree_root
        The root of the tree of files to validate

    cv_source
        The source from which to load the CVs.

        For full details, see [`load_cvs`][input4mips_validation.cvs.load_cvs].

    xr_variable_processor
        Helper to use for processing the variables in xarray objects.

    frequency_metadata_keys
        Metadata definitions for frequency information

    bounds_info
        Metadata definitions for bounds handling

    time_dimension
        The time dimension of the data

    rglob_input
        String to use when applying `rglob` to find input files

    allow_cf_checker_warnings
        Allow validation to pass, even if the CF-checker raises warnings?

    output_html
        If not `None`,
        the file in which to dump the HTML version of the validation results.
    """
    vtrs = get_validate_tree_result(
        root=tree_root,
        cv_source=cv_source,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        bounds_info=bounds_info,
        time_dimension=time_dimension,
        rglob_input=rglob_input,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
    )

    if output_html is not None:
        with open(output_html, "w") as fh:
            fh.write(vtrs.to_html())

    vtrs.raise_if_errors()


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
    bnds_coord_indicators: BNDS_COORD_INDICATORS_TYPE = "bnds;bounds",
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
    frequency_metadata_keys = FrequencyMetadataKeys(
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
    )
    xr_variable_processor = XRVariableHelper(
        bounds_coord_indicators=tuple(
            bnds_coord_indicators.split(BNDS_COORD_INDICATORS_SEPARATOR)
        )
    )
    # TODO: allow this to be passed from CLI
    # # Could also retrieve the info from the file with something like
    # # (question would be, where in the stack to do this)
    # tmp = xr.open_dataset(file)
    # if time_dimension in tmp:
    #     # Has to be like this according to CF-convention
    #     bounds_info_key = "bounds"
    #     time_bounds = tmp[time_dimension].attrs[bounds_info_key]
    #     time_bounds_dims = tmp[time_bounds].dims
    #     bounds_dim_l = [v for v in time_bounds_dims if v != time_dimension]
    #     if len(bounds_dim_l) != 1:
    #         raise AssertionError
    #
    #     bounds_dim_l = bounds_dim[0]
    bounds_info = BoundsInfo(
        time_bounds="time_bnds",
        bounds_dim="bnds",
    )

    validate_tree(
        tree_root=tree_root,
        cv_source=cv_source,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        bounds_info=bounds_info,
        time_dimension=time_dimension,
        rglob_input=rglob_input,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
        output_html=output_html,
    )


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
