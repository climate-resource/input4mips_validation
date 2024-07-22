"""
Validation with the [cf-checker](https://github.com/cedadev/cf-checker)
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import xarray as xr


def check_with_cf_checker(filepath: Path | str, ds: xr.Dataset) -> None:
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

    cf_checks_loc = subprocess.check_output(["/usr/bin/which", "cfchecks"]).strip()  # noqa: S603
    try:
        subprocess.check_output(
            [cf_checks_loc, "-v", cf_conventions, str(filepath)],  # noqa: S603
        )
    except subprocess.CalledProcessError as exc:
        error_msg = (
            f"cf-checker validation failed. cfchecks output:\n\n{exc.output.decode()}"
        )
        raise ValueError(error_msg) from exc
