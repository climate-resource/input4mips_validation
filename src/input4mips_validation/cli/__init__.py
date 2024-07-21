"""
Command-line interface
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations

import datetime as dt
import shutil
from pathlib import Path
from typing import Annotated, Union

import cftime
import iris
import numpy as np
import rich
import typer
from loguru import logger

import input4mips_validation.cli.logging
from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.serialisation import converter_json, json_dumps_cv_style
from input4mips_validation.validation import validate_file
from input4mips_validation.xarray_helpers.iris import ds_from_iris_cubes
from input4mips_validation.xarray_helpers.time import xr_time_min_max_to_single_value

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

WRITE_IN_DRS_UNSET_VALUE: str = "nowhere_idjunk"
"""
Default value for write-in-drs at the CLI

If write_in_drs equals this value, we assume that it wasn't passed by the user.
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
def validate_file_command(  # noqa: PLR0913
    file: Annotated[
        Path,
        typer.Argument(
            help="The file to validate", exists=True, dir_okay=False, file_okay=True
        ),
    ],
    cv_source: CV_SOURCE_TYPE = CV_SOURCE_UNSET_VALUE,
    write_in_drs: Annotated[
        str,
        typer.Option(
            help=(
                "If supplied, "
                "the file will be re-written into the DRS if it passes validation."
                "The supplied value is assumed to be the root directory "
                "into which to write the file (following the DRS)."
            ),
            show_default=False,
        ),
    ] = WRITE_IN_DRS_UNSET_VALUE,
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
    bnds_coord_indicator: Annotated[
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
    ] = "bnds",
    frequency_metadata_key: Annotated[
        str,
        typer.Option(
            help=(
                "The key in the data's metadata "
                "which points to information about the data's frequency. "
                "Only required if --write-in-drs or --create-db-entry are supplied."
            )
        ),
    ] = "frequency",
    no_time_axis_frequency: Annotated[
        str,
        typer.Option(
            help=(
                "The value of 'frequency' in the metadata which indicates "
                "that the file has no time axis i.e. is fixed in time."
                "Only required if --write-in-drs or --create-db-entry are supplied."
            )
        ),
    ] = "fx",
    time_dimension: Annotated[
        str,
        typer.Option(
            help=(
                "The time dimension of the data. "
                "Only required if --write-in-drs or --create-db-entry are supplied."
            )
        ),
    ] = "time",
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

    if write_in_drs == WRITE_IN_DRS_UNSET_VALUE:
        write_in_drs = None

    validate_file(file, cv_source=cv_source_use)

    if write_in_drs:
        raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source_use)
        cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

        ds = ds_from_iris_cubes(
            iris.load(file), bnds_coord_indicator=bnds_coord_indicator
        )

        if ds.attrs[frequency_metadata_key] != no_time_axis_frequency:
            time_start: cftime.datetime | dt.datetime | np.datetime64 | None = (
                xr_time_min_max_to_single_value(ds[time_dimension].min())
            )
            time_end: cftime.datetime | dt.datetime | np.datetime64 | None = (
                xr_time_min_max_to_single_value(ds[time_dimension].max())
            )
        else:
            time_start = time_end = None

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
            raw_cvs_loader = get_raw_cvs_loader(cv_source=cv_source_use)
            cvs = load_cvs(raw_cvs_loader=raw_cvs_loader)

            db_entry_creation_file = file

        database_entry = Input4MIPsDatabaseEntryFile.from_file(
            db_entry_creation_file, cvs=cvs
        )

        logger.info(f"{database_entry=}")
        rich.print("Database entry as JSON:")
        rich.print(json_dumps_cv_style(converter_json.unstructure(database_entry)))


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
