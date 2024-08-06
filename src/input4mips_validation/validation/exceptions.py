"""
Exceptions related to validation that don't obviously fit elsewhere
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from input4mips_validation.database.database import Input4MIPsDatabaseEntryFile


class InvalidFileError(ValueError):
    """
    Raised when a file does not pass all of the validation
    """

    def __init__(
        self,
        filepath: Path | str,
        error_container: list[tuple[str, Exception]],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        filepath
            The filepath we tried to validate

        error_container
            The thing which was being done
            and the error which was caught
            while validating the file.
        """
        # Not clear how input could be further validated hence noqa
        ncdump_loc = shutil.which("ncdump")
        if ncdump_loc is None:
            msg = "Could not find ncdump executable"
            raise AssertionError(msg)

        # Not clear how input could be further validated hence noqa
        file_ncdump_h = subprocess.check_output(
            [ncdump_loc, "-h", str(filepath)]  # noqa: S603
        ).decode()

        error_msgs: list[str] = []
        for error in error_container:
            process, exc = error
            formatted_exc = f"{type(exc).__name__}: {exc}"
            error_msgs.append(f"{process} failed. Exception: {formatted_exc}")

        error_msgs_str = "\n\n".join(error_msgs)

        error_msg = (
            f"Failed to validate {filepath=}\n"
            f"File's `ncdump -h` output:\n\n{file_ncdump_h}\n\n"
            "Caught error messages:\n\n"
            f"{error_msgs_str}"
        )

        super().__init__(error_msg)


class InvalidTreeError(ValueError):
    """
    Raised when a tree does not pass all of the validation
    """

    def __init__(
        self,
        root: Path | str,
        error_container: list[tuple[str, Exception]],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        root
            The root of the tree we tried to validate

        error_container
            The thing which was being done
            and the error which was caught
            while validating the file.
        """
        error_msgs: list[str] = []
        for error in error_container:
            process, exc = error
            formatted_exc = f"{type(exc).__name__}: {exc}"
            error_msgs.append(f"{process} failed. Exception: {formatted_exc}")

        error_msgs_str = "\n\n".join(error_msgs)

        error_msg = (
            f"Failed to validate {root=}\n"
            "Caught error messages:\n\n"
            f"{error_msgs_str}"
        )

        super().__init__(error_msg)


class FileAssociatedWithDatabaseEntryError(ValueError):
    """
    Raised when the file associated with a database entry has a problem
    """

    def __init__(
        self,
        entry: Input4MIPsDatabaseEntryFile,
        error_container: list[tuple[str, Exception]],
    ) -> None:
        """
        Initialise the error

        Parameters
        ----------
        entry
            The entry we tried to validate

        error_container
            The thing which was being done
            and the error which was caught
            while validating the file.
        """
        error_msgs: list[str] = []
        for error in error_container:
            process, exc = error
            formatted_exc = f"{type(exc).__name__}: {exc}"
            error_msgs.append(f"{process} failed. Exception: {formatted_exc}")

        error_msgs_str = "\n\n".join(error_msgs)

        error_msg = (
            f"Failed to validate {entry=}\n"
            "Caught error messages:\n\n"
            f"{error_msgs_str}"
        )

        super().__init__(error_msg)
