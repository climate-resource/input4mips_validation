"""
CLI for database handling
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations

from pathlib import Path
from typing import Annotated, Union

import typer
from loguru import logger

from input4mips_validation.cli.common_arguments_and_options import (
    ALLOW_CF_CHECKER_WARNINGS_TYPE,
    BNDS_COORD_INDICATORS_SEPARATOR,
    BNDS_COORD_INDICATORS_TYPE,
    CV_SOURCE_OPTION,
    FREQUENCY_METADATA_KEY_OPTION,
    N_PROCESSES_OPTION,
    NO_TIME_AXIS_FREQUENCY_OPTION,
    RGLOB_INPUT_OPTION,
    TIME_DIMENSION_OPTION,
)
from input4mips_validation.database import (
    dump_database_file_entries,
    load_database_file_entries,
    update_database_file_entries,
)
from input4mips_validation.database.creation import create_db_file_entries
from input4mips_validation.inference.from_data import BoundsInfo, FrequencyMetadataKeys
from input4mips_validation.validation.database import (
    validate_database_entries,
    validate_tracking_ids_are_unique,
)
from input4mips_validation.xarray_helpers.variables import (
    XRVariableHelper,
    XRVariableProcessorLike,
)

app = typer.Typer()


def db_create(  # noqa: PLR0913
    tree_root: Path,
    db_dir: Path,
    cv_source: Union[str, None],
    frequency_metadata_keys: FrequencyMetadataKeys,
    time_dimension: str,
    rglob_input: str,
    n_processes: int,
) -> None:
    """
    Create a database from a tree of files

    This is the direct Python API.
    We expose this for two reasons:

    1. to make it easier for those who want to use Python rather than the CLI
    1. to ensure that we're passing all the CLI arguments correctly
       (this function has no keyword arguments, so if we forget one, the CLI won't work)

    Parameters
    ----------
    tree_root
        The root of the tree for which to create the database

    db_dir
        The directory in which to write the database entries

    cv_source
        The source from which to load the CVs.

        For full details, see [`load_cvs`][input4mips_validation.cvs.load_cvs].

    frequency_metadata_keys
        Metadata definitions for frequency information

    time_dimension
        The time dimension of the data

    rglob_input
        String to use when applying `rglob` to find input files

    n_processes
        Number of parallel processes to use while creating the entries
    """
    if db_dir.exists():
        msg = "The database directory must not already exist"
        raise FileExistsError(msg)

    logger.debug(f"Creating {db_dir}")
    db_dir.mkdir(parents=True, exist_ok=False)

    all_files = tuple(v for v in tree_root.rglob(rglob_input) if v.is_file())

    db_entries = create_db_file_entries(
        files=all_files,
        cv_source=cv_source,
        frequency_metadata_keys=frequency_metadata_keys,
        time_dimension=time_dimension,
        n_processes=n_processes,
    )

    logger.info(
        f"Dumping the {len(db_entries)} created "
        f"{'entry' if len(db_entries) == 1 else 'entries'} "
        f"to the new database in {db_dir}"
    )
    dump_database_file_entries(entries=db_entries, db_dir=db_dir)
    logger.success(f"Created new database in {db_dir}")


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
            help="The directory in which to write the database entries.",
            dir_okay=True,
            file_okay=False,
        ),
    ],
    cv_source: CV_SOURCE_OPTION = None,
    frequency_metadata_key: FREQUENCY_METADATA_KEY_OPTION = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_OPTION = "fx",
    time_dimension: TIME_DIMENSION_OPTION = "time",
    rglob_input: RGLOB_INPUT_OPTION = "*.nc",
    n_processes: N_PROCESSES_OPTION = 1,
) -> None:
    """
    Create a database from a tree of files
    """
    if db_dir.exists():
        msg = "If using `create`, the database directory must not already exist"
        raise FileExistsError(msg)

    frequency_metadata_keys = FrequencyMetadataKeys(
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
    )

    db_create(
        tree_root=tree_root,
        db_dir=db_dir,
        cv_source=cv_source,
        frequency_metadata_keys=frequency_metadata_keys,
        time_dimension=time_dimension,
        rglob_input=rglob_input,
        n_processes=n_processes,
    )


def db_add_tree(  # noqa: PLR0913
    tree_root: Path,
    db_dir: Path,
    cv_source: Union[str, None],
    frequency_metadata_keys: FrequencyMetadataKeys,
    time_dimension: str,
    rglob_input: str,
    n_processes: int,
) -> None:
    """
    Add files from a tree to a database

    This is the direct Python API.
    We expose this for two reasons:

    1. to make it easier for those who want to use Python rather than the CLI
    1. to ensure that we're passing all the CLI arguments correctly
       (this function has no keyword arguments, so if we forget one, the CLI won't work)

    Parameters
    ----------
    tree_root
        The root of the tree for which to create the database

    db_dir
        The directory in which to write the database entries

    cv_source
        The source from which to load the CVs.

        For full details, see [`load_cvs`][input4mips_validation.cvs.load_cvs].

    frequency_metadata_keys
        Metadata definitions for frequency information

    time_dimension
        The time dimension of the data

    rglob_input
        String to use when applying `rglob` to find input files

    n_processes
        Number of parallel processes to use while creating the entries
    """
    all_tree_files = set(tree_root.rglob(rglob_input))

    db_existing_entries = load_database_file_entries(db_dir)
    known_files = set([Path(v.filepath) for v in db_existing_entries])

    files_to_add = all_tree_files.difference(known_files)

    if not files_to_add:
        logger.info(f"All files in {tree_root} are already in the database")
        return

    logger.info(
        f"Found {len(files_to_add)} "
        f"new {'files' if len(files_to_add) > 1 else 'file'} "
        "to add to the database"
    )
    db_entries_to_add = create_db_file_entries(
        files=files_to_add,
        cv_source=cv_source,
        frequency_metadata_keys=frequency_metadata_keys,
        time_dimension=time_dimension,
        n_processes=n_processes,
    )

    logger.info(
        f"Dumping {len(db_entries_to_add)} new entries to the database in {db_dir}"
    )
    dump_database_file_entries(entries=db_entries_to_add, db_dir=db_dir)
    logger.success(
        f"Added missing entries from {tree_root} to the database in {db_dir}"
    )


@app.command(name="add-tree")
def db_add_tree_command(  # noqa: PLR0913
    tree_root: Annotated[
        Path,
        typer.Argument(
            help="The root of the tree from which to add entries to the database",
            exists=True,
            dir_okay=True,
            file_okay=False,
        ),
    ],
    db_dir: Annotated[
        Path,
        typer.Option(
            help="The database's directory.",
            dir_okay=True,
            file_okay=False,
            exists=True,
        ),
    ],
    cv_source: CV_SOURCE_OPTION = None,
    frequency_metadata_key: FREQUENCY_METADATA_KEY_OPTION = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_OPTION = "fx",
    time_dimension: TIME_DIMENSION_OPTION = "time",
    rglob_input: RGLOB_INPUT_OPTION = "*.nc",
    n_processes: N_PROCESSES_OPTION = 1,
) -> None:
    """
    Add files from a tree to a database
    """
    frequency_metadata_keys = FrequencyMetadataKeys(
        frequency_metadata_key=frequency_metadata_key,
        no_time_axis_frequency=no_time_axis_frequency,
    )

    db_add_tree(
        tree_root=tree_root,
        db_dir=db_dir,
        cv_source=cv_source,
        frequency_metadata_keys=frequency_metadata_keys,
        time_dimension=time_dimension,
        rglob_input=rglob_input,
        n_processes=n_processes,
    )


def db_validate(  # noqa: PLR0913
    db_dir: Path,
    cv_source: Union[str, None],
    xr_variable_processor: XRVariableProcessorLike,
    frequency_metadata_keys: FrequencyMetadataKeys,
    bounds_info: BoundsInfo,
    time_dimension: str,
    allow_cf_checker_warnings: bool,
    n_processes: int,
    force: bool,
) -> None:
    """
    Validate the entries in a database

    This is the direct Python API.
    We expose this for two reasons:

    1. to make it easier for those who want to use Python rather than the CLI
    1. to ensure that we're passing all the CLI arguments correctly
       (this function has no keyword arguments, so if we forget one, the CLI won't work)

    Parameters
    ----------
    db_dir
        The database's directory

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

    allow_cf_checker_warnings
        Allow validation to pass, even if the CF-checker raises warnings?

    n_processes
        Number of parallel processes to use while creating the entries

    force
        Force validation to run on all files,
        even those that have already been validated
        (i.e. validation may be re-run on some files).
    """
    db_existing_entries = load_database_file_entries(db_dir)

    # If tracking IDs aren't unique, we can fail immediately,
    # no need to catch the errors or anything.
    validate_tracking_ids_are_unique(db_existing_entries)

    if force:
        logger.info("`--force` used, hence all entries will be re-validated")
        entries_to_validate = db_existing_entries

    else:
        logger.info("Determining entries to validate")
        entries_to_validate = tuple(
            [e for e in db_existing_entries if e.validated_input4mips is None]
        )
        if not entries_to_validate:
            logger.info(f"All files in {db_dir} have already been validated")
            return

    validated_entries = validate_database_entries(
        entries_to_validate,
        cv_source=cv_source,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        bounds_info=bounds_info,
        time_dimension=time_dimension,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
        n_processes=n_processes,
    )

    logger.info(
        f"Updating {len(validated_entries)} validated entries "
        f"in the database in {db_dir}"
    )
    update_database_file_entries(entries=validated_entries, db_dir=db_dir)

    if force:
        msg = f"Re-validated all the entries in the database in {db_dir}"

    else:
        msg = (
            "Validated the entries "
            f"which hadn't been validated in the database in {db_dir}"
        )

    logger.success(msg)


@app.command(name="validate")
def db_validate_command(  # noqa: PLR0913
    db_dir: Annotated[
        Path,
        typer.Option(
            help="The database's directory.",
            dir_okay=True,
            file_okay=False,
            exists=True,
        ),
    ],
    cv_source: CV_SOURCE_OPTION = None,
    bnds_coord_indicators: BNDS_COORD_INDICATORS_TYPE = "bnds;bounds",
    frequency_metadata_key: FREQUENCY_METADATA_KEY_OPTION = "frequency",
    no_time_axis_frequency: NO_TIME_AXIS_FREQUENCY_OPTION = "fx",
    time_dimension: TIME_DIMENSION_OPTION = "time",
    allow_cf_checker_warnings: ALLOW_CF_CHECKER_WARNINGS_TYPE = False,
    n_processes: N_PROCESSES_OPTION = 1,
    force: Annotated[
        bool,
        typer.Option(
            "--force",
            help=(
                "Force re-validation of all entries. "
                "This means that any previous validation of the entries is ignored."
            ),
        ),
    ] = False,
) -> None:
    """
    Validate the entries in a database
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

    db_validate(
        db_dir=db_dir,
        cv_source=cv_source,
        xr_variable_processor=xr_variable_processor,
        frequency_metadata_keys=frequency_metadata_keys,
        bounds_info=bounds_info,
        time_dimension=time_dimension,
        allow_cf_checker_warnings=allow_cf_checker_warnings,
        n_processes=n_processes,
        force=force,
    )


if __name__ == "__main__":
    app()
