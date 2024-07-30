"""
Validation with the [cf-checker](https://github.com/cedadev/cf-checker)
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Union

import xarray as xr
from loguru import logger


def only_cf_checker_warnings_raised(cf_checker_output: str) -> bool:
    """
    Determine if the CF-checker only raised warnings

    This is extremely sensitive to the implementation of the
    [cf-checker](https://github.com/cedadev/cf-checker),
    particularly its error reporting
    ([status of error reporting at last check](https://github.com/cedadev/cf-checker/blob/c0486c606f7cf4d38d3b484b427726ce1bde73ee/src/cfchecker/cfchecks.py#L675)).

    Parameters
    ----------
    cf_checker_output
        CF-checker output to parse

    Returns
    -------
    :
        `True` if only warnings and below were raised by the CF-checker,
        `False` otherwise.
    """
    cf_checker_output_no_new_lines = " ".join(cf_checker_output.splitlines())

    counts: dict[str, Union[int, None]] = {}
    for key, id_string in {
        "fatal": "FATAL ERRORS",
        "errors": "ERRORS detected",
        "warnings": "WARNINGS given",
    }.items():
        check_regexp = rf".*(?P<checker_output_string>{id_string}:\s\d+).*"
        match = re.match(check_regexp, cf_checker_output_no_new_lines)
        if match:
            matching_text = match.group("checker_output_string")
            count = int(matching_text.split(":")[-1].strip())

            counts[key] = count

        else:
            counts[key] = None

    return all(counts[k] is None or counts[k] == 0 for k in ("fatal", "errors"))


def check_with_cf_checker(
    filepath: Path | str, ds: xr.Dataset, no_raise_if_only_warnings: bool = False
) -> None:
    """
    Check a file with the cf-checker

    Parameters
    ----------
    filepath
        Filepath to check

    ds
        Dataset that corresponds to `filepath`.

        This is required to we can tell cf-checker
        which CF conventions to use while checking the file.

    no_raise_if_only_warnings
        If `True`, no error is raised if the CF-checker only raises warnings.

    Raises
    ------
    ValueError
        If `no_raise_if_only_warnings` is `False`, an error is raised
        if the CF-checker found any issues, including warnings.

        If `no_raise_if_only_warnings` is `True`, an error is raised
        if the CF-checker found any errors, excluding warnings.
    """
    conventions_match = re.match(
        r"CF-(?P<conventions_id>[0-9\.]+).*", ds.attrs["Conventions"]
    )
    if not conventions_match:
        msg = (
            "Cannot extract CF conventions from Conventions metadata. "
            f"{ds.attrs['Conventions']=}"
        )
        raise ValueError(msg)

    cf_conventions = conventions_match.group("conventions_id").strip()
    if cf_conventions is None:  # pragma: no cover
        msg = f"Somehow failed to get the conventions from {ds.attrs['Conventions']=}"
        raise AssertionError(msg)

    cf_checks_loc = shutil.which("cfchecks")
    if cf_checks_loc is None:
        msg = "Could not find cfchecks executable"
        raise AssertionError(msg)

    try:
        subprocess.check_output(
            [cf_checks_loc, "-v", cf_conventions, str(filepath)],  # noqa: S603
        )
    except subprocess.CalledProcessError as exc:
        output = exc.output.decode()

        # If only warnings should not raise an error,
        # parse the output to work out what happened.
        # This is a terrible way to do this, but the cf-checker's
        # return codes don't play nice with subprocess so here we are
        if no_raise_if_only_warnings and only_cf_checker_warnings_raised(output):
            logger.debug(f"Ignoring cf-checker warnings:\n\n{output}")

            return

        error_msg = f"cf-checker validation failed. cfchecks output:\n\n{output}"
        raise ValueError(error_msg) from exc
