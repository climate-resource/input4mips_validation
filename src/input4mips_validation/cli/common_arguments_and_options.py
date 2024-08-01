"""
Common arguments and options used across our CI
"""

# # Do not use this here, it breaks typer's annotations
# from __future__ import annotations

from typing import Annotated, Optional

import typer

CV_SOURCE_OPTION = Annotated[
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

FREQUENCY_METADATA_KEY_OPTION = Annotated[
    str,
    typer.Option(
        help=(
            "The key in the data's metadata "
            "which points to information about the data's frequency. "
        )
    ),
]

N_PROCESSES_OPTION = Annotated[
    int, typer.Option(help="Number of parallel processes to use")
]

NO_TIME_AXIS_FREQUENCY_OPTION = Annotated[
    str,
    typer.Option(
        help=(
            "The value of `frequency_metadata_key` in the metadata which indicates "
            "that the file has no time axis i.e. is fixed in time."
        )
    ),
]


RGLOB_INPUT_OPTION = Annotated[
    str,
    typer.Option(help=("String to use when applying `rglob` to find input files.")),
]

TIME_DIMENSION_OPTION = Annotated[
    str,
    typer.Option(help=("The time dimension of the data.")),
]
