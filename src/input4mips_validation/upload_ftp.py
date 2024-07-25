"""
FTP upload support

Note: this module is not formally tested at the moment,
currently a more chaos engineering approach instead.
Bugs are likely :)
"""

from __future__ import annotations

import concurrent.futures
import ftplib
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Callable

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
    logger.debug(f"Logged into {ftp_server} using {username=}")

    yield ftp

    ftp.quit()
    logger.debug(f"Closed connection to {ftp_server}")


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


def upload_file(
    file: Path, strip_pre_upload: Path, ftp_dir_upload_in: str, ftp: ftplib.FTP
) -> ftplib.FTP:
    """
    Upload a file to an FTP server

    Parameters
    ----------
    file
        File to upload.

        The full path of the file relative to `strip_pre_upload` will be uploaded.
        In other words, any directories in `file` will be made on the
        FTP server before uploading.

    strip_pre_upload
        The parts of the path that should be stripped before the file is uploaded.

        For example, if `file` is `/path/to/a/file/somewhere/file.nc`
        and `strip_pre_upload` is `/path/to/a`,
        then we will upload the file to `file/somewhere/file.nc` on the FTP server
        (relative to whatever directory the FTP server is in
        when we enter this function).

    ftp_dir_upload_in
        Directory on the FTP server in which to upload `file`
        (after removing `strip_pre_upload`).

    ftp
        FTP connection to use for the upload.

    Returns
    -------
    :
        The FTP connection.
    """
    logger.debug(f"Uploading {file}")
    cd_v(ftp_dir_upload_in, ftp=ftp)

    filepath_upload = file.relative_to(strip_pre_upload)
    logger.info(
        f"Relative to {ftp_dir_upload_in} on the FTP server, "
        f"will upload {file} to {filepath_upload}"
    )

    logger.info("Ensuring directories exist on the FTP server")
    for parent in list(filepath_upload.parents)[::-1]:
        if parent == Path("."):
            continue

        to_make = parent.parts[-1]
        mkdir_v(to_make, ftp=ftp)
        cd_v(to_make, ftp=ftp)

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

    return ftp


def upload_file_p(
    file: Path,
    strip_pre_upload: Path,
    ftp_dir_upload_in: str,
    get_ftp_connection: Callable[[], Iterator[ftplib.FTP]],
) -> None:
    """
    File for uploading a file to an FTP server as part of a parallel process

    Parameters
    ----------
    file
        File to upload.

        For full details,
        see [`upload_file`][input4mips_validation.upload_ftp.upload_file].

    strip_pre_upload
        The path, relative to which the file should be upload.

        For full details,
        see [`upload_file`][input4mips_validation.upload_ftp.upload_file].

    ftp_dir_upload_in
        Directory on the FTP server in which to upload `file`
        (after removing `strip_pre_upload`).

    get_ftp_connection
        Callable that returns a new FTP connection with which to do the upload.

        This should be a context manager that closes the FTP connection when exited.
    """
    with get_ftp_connection() as ftp:
        upload_file(
            file,
            strip_pre_upload=strip_pre_upload,
            ftp_dir_upload_in=ftp_dir_upload_in,
            ftp=ftp,
        )


def upload_files_p(  # noqa: PLR0913
    files_to_upload: Iterable[Path],
    get_ftp_connection: Callable[[], Iterator[ftplib.FTP]],
    ftp_dir_root: str,
    ftp_dir_rel_to_root: str,
    cvs: Input4MIPsCVs,
    n_threads: int,
) -> ftplib.FTP:
    """
    Upload files to the FTP server in parallel

    Parameters
    ----------
    files_to_upload
        Files to upload

    get_ftp_connection
        Callable that returns a new FTP connection with which to do the upload.

        This should be a context manager that closes the FTP connection when exited.

    ftp_dir_root
        Root directory on the FTP server for receiving files.

    ftp_dir_rel_to_root
        Directory, relative to `ftp_dir_root`, in which to upload the files

    cvs
        CVs used when writing the files.

        These are needed to help determine where the DRS path starts.

    n_threads
        Number of threads to use for uploading

    Returns
    -------
    :
        The FTP connection
    """
    with get_ftp_connection() as ftp:
        cd_v(ftp_dir_root, ftp=ftp)

        mkdir_v(ftp_dir_rel_to_root, ftp=ftp)
        cd_v(ftp_dir_rel_to_root, ftp=ftp)

    logger.info(
        "Uploading in parallel using up to "
        f"{n_threads} {'threads' if n_threads > 1 else 'thread'}"
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        for file in files_to_upload:
            directory_metadata = cvs.DRS.extract_metadata_from_path(
                file.parent,
                include_root_data_dir=True,
            )

            futures = [
                executor.submit(
                    upload_file_p,
                    file,
                    strip_pre_upload=directory_metadata["root_data_dir"],
                    ftp_dir_upload_in=f"{ftp_dir_root}/{ftp_dir_rel_to_root}",
                    get_ftp_connection=get_ftp_connection,
                )
            ]

        for future in concurrent.futures.as_completed(futures):
            # Call in case there are any errors
            future.result()

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
    n_threads: int = 4,
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

    n_threads
        Number of threads to use for uploading
    """
    get_ftp_connection = partial(
        login_to_ftp, ftp_server=ftp_server, username=username, password=password
    )

    upload_files_p(
        files_to_upload=tree_root.rglob(rglob_input),
        get_ftp_connection=get_ftp_connection,
        ftp_dir_root=ftp_dir_root,
        ftp_dir_rel_to_root=ftp_dir_rel_to_root,
        cvs=cvs,
        n_threads=n_threads,
    )
