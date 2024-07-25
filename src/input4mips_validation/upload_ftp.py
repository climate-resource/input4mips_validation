"""
FTP upload support
"""

from __future__ import annotations

import ftplib
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

import tqdm
import tqdm.utils
from loguru import logger

from input4mips_validation.cvs import Input4MIPsCVs


@contextmanager
def login_to_ftp(ftp_server: str, username: str, password: str) -> Iterator[ftplib.FTP]:
    """
    Create a connection to an FTP server

    When the context block is excited, the connection is closed.

    Parameters
    ----------
    ftp_server
        FTP server to login to

    username
        Username

    password
        Password

    Yields
    ------
    :
        Connection to the FTP server
    """
    ftp = ftplib.FTP(ftp_server, passwd=password, user=username)  # noqa: S321
    logger.info(f"Logged into {ftp_server} using {username=}")

    yield ftp

    ftp.quit()
    logger.info(f"Closed connection to {ftp_server}")


def cd_v(dir_to_move_to: str, ftp: ftplib.FTP) -> ftplib.FTP:
    """
    Change directory verbosely

    Parameters
    ----------
    dir_to_move_to
        Directory to move to on the server

    ftp
        FTP connection

    Returns
    -------
    :
        The FTP connection
    """
    ftp.cwd(dir_to_move_to)
    logger.debug(f"Now in {ftp.pwd()} on FTP server")

    return ftp


def mkdir_v(dir_to_make: str, ftp: ftplib.FTP) -> None:
    """
    Make directory verbosely

    Also, don't fail if the directory already exists

    Parameters
    ----------
    dir_to_make
        Directory to make

    ftp
        FTP connection
    """
    try:
        logger.debug(f"Attempting to make {dir_to_make} on {ftp.host=}")
        ftp.mkd(dir_to_make)
        logger.debug(f"Made {dir_to_make} on {ftp.host=}")
    except ftplib.error_perm:
        logger.debug(f"{dir_to_make} already exists on {ftp.host=}")


def upload_file(file: Path, upload_path_rel_to: Path, ftp: ftplib.FTP) -> ftplib.FTP:
    """
    Upload a file to an FTP server

    We ensure that the FTP connection is left in the same directory
    as it was in when this function was entered,
    irrespective of the directory creation and selection commands
    we run in this function.

    Parameters
    ----------
    file
        File to upload.
        The full path of the file relative to ``root_dir`` will be uploaded.
        In other words, any directories in ``file`` will be made on the
        FTP server before uploading.

    upload_path_rel_to
        The path, relative to which the file should be upload.

        In other words, `upload_path_rel_to` will not be included when we update `file`.

        For example, if `file` is `/path/to/a/file/somewhere/file.nc`
        and `upload_path_rel_to` is `/path/to/a`,
        then we will upload the file to `file/somewhere/file.nc` on the FTP server
        (relative to whatever directory the FTP server is in
        when we enter this function).

    ftp
        FTP connection to use for the upload.

    Returns
    -------
    :
        The FTP connection.
    """
    logger.info(f"Uploading {file}")

    # Save the starting directory for later
    ftp_pwd_in = ftp.pwd()

    filepath_upload = file.relative_to(upload_path_rel_to)
    logger.info(
        f"Relative to {ftp_pwd_in} on the FTP server, will upload to {filepath_upload}"
    )

    for parent in list(filepath_upload.parents)[::-1]:
        if parent == Path("."):
            continue

        to_make = parent.parts[-1]
        mkdir_v(to_make, ftp=ftp)
        cd_v(to_make, ftp=ftp)

    logger.info(f"Uploading {file}")
    with open(file, "rb") as fh:
        upload_command = f"STOR {file.name}"
        logger.debug(f"Upload command: {upload_command}")

        file_size = file.stat().st_size
        try:
            with tqdm.tqdm(
                total=file_size,
                desc=file.name,
                unit="B",
                unit_scale=True,
                unit_divisor=1024,
            ) as pbar:
                wrapped_file = tqdm.utils.CallbackIOWrapper(pbar.update, fh, "read")
                ftp.storbinary(upload_command, wrapped_file)

            logger.info(f"Successfully uploaded {file}")
        except ftplib.error_perm:
            logger.exception(
                f"{file.name} already exists on the server in {ftp.pwd()}. "
                "Use a different root directory on the receiving server "
                "if you really wish to upload again."
            )

    cd_v(ftp_pwd_in, ftp=ftp)

    return ftp


def upload_files(
    files_to_upload: Iterable[Path],
    ftp: ftplib.FTP,
    ftp_dir_root: str,
    ftp_dir_rel_to_root: str,
    cvs: Input4MIPsCVs,
) -> ftplib.FTP:
    """
    Upload files to the FTP server

    Parameters
    ----------
    files_to_upload
        Files to upload

    ftp
        FTP server connection.

    ftp_dir_root
        Root directory on the FTP server for receiving files.

    ftp_dir_rel_to_root
        Directory, relative to `ftp_dir_root`, in which to upload the files

    cvs
        CVs used when writing the files.

        These are needed to help determine where the DRS path starts.

    Returns
    -------
    :
        The FTP connection
    """
    cd_v(ftp_dir_root, ftp=ftp)

    mkdir_v(ftp_dir_rel_to_root, ftp=ftp)
    cd_v(ftp_dir_rel_to_root, ftp=ftp)

    for file in files_to_upload:
        directory_metadata = cvs.DRS.extract_metadata_from_path(
            file.parent,
            include_root_data_dir=True,
        )
        upload_file(
            file, upload_path_rel_to=directory_metadata["root_data_dir"], ftp=ftp
        )

    logger.debug("Uploaded all files")
    return ftp


def upload_ftp(  # noqa: PLR0913
    tree_root: Path,
    ftp_dir_rel_to_root: str,
    password: str,
    cvs: Input4MIPsCVs,
    username: str = "anonymous",
    ftp_server: str = "ftp.llnl.gov",
    ftp_dir_root: str = "/incoming",
    rglob_input: str = "*.nc",
) -> None:
    """
    Upload a tree of files to an FTP server

    Parameters
    ----------
    tree_root
        Root of the tree of files to upload

    ftp_dir_rel_to_root
        Directory, relative to `ftp_dir_root`, in which to upload the tree

        For example, "my-institute-input4mips"

    password
        Password to use when logging in to the FTP server.

        If uploading to LLNL, please use your email address here.

    cvs
        CVs used when writing the files.

        These are needed to help determine where the DRS path starts.

    username
        Username to use when logging in to the FTP server.

    ftp_server
        FTP server to log in to.

    ftp_dir_root
        Root directory on the FTP server for receiving files.

    rglob_input
        Input to rglob which selects only the files of interest in the tree to upload.
    """
    with login_to_ftp(
        ftp_server=ftp_server, username=username, password=password
    ) as ftp_logged_in:
        upload_files(
            files_to_upload=tree_root.rglob(rglob_input),
            ftp=ftp_logged_in,
            ftp_dir_root=ftp_dir_root,
            ftp_dir_rel_to_root=ftp_dir_rel_to_root,
            cvs=cvs,
        )
