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
from contextlib import AbstractContextManager, contextmanager
from functools import partial
from pathlib import Path
from types import TracebackType
from typing import Callable, Optional, Protocol

import tqdm
import tqdm.utils
from loguru import logger
from typing_extensions import TypeAlias

from input4mips_validation.cvs import Input4MIPsCVs
from input4mips_validation.logging import LOG_LEVEL_INFO_FILE

GetFTPConnection: TypeAlias = Callable[[], AbstractContextManager[Optional[ftplib.FTP]]]
"""
Type hint for callables that we can use for managing FTP connections
"""


@contextmanager
def login_to_ftp(
    ftp_server: str, username: str, password: str, dry_run: bool
) -> Iterator[Optional[ftplib.FTP]]:
    """
    Create a connection to an FTP server.

    When the context block is excited, the connection is closed.

    If we are doing a dry run, `None` is returned instead
    to signal that no connection was actually made.
    We do, however, log messages to indicate what would have happened.

    Parameters
    ----------
    ftp_server
        FTP server to login to

    username
        Username

    password
        Password

    dry_run
        Is this a dry run?

        If `True`, we won't actually login to the FTP server.

    Yields
    ------
    :
        Connection to the FTP server.

        If it is a dry run, we simply return `None`.
    """
    if dry_run:
        logger.debug(f"Dry run. Would log in to {ftp_server} using {username=}")
        ftp = None

    else:
        ftp = ftplib.FTP(ftp_server, passwd=password, user=username)  # noqa: S321
        logger.debug(f"Logged into {ftp_server} using {username=}")

    yield ftp

    if ftp is None:
        if not dry_run:  # pragma: no cover
            raise AssertionError
        logger.debug(f"Dry run. Would close connection to {ftp_server}")

    else:
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
    file: Path,
    strip_pre_upload: Path,
    ftp_dir_upload_in: str,
    ftp: Optional[ftplib.FTP],
) -> Optional[ftplib.FTP]:
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

        If this is `None`, we assume this is a dry run.

    Returns
    -------
    :
        The FTP connection.

        If it is a dry run, this can simply be `None`.
    """
    logger.debug(f"Uploading {file}")
    if ftp is None:
        logger.debug(f"Dry run. Would cd on the FTP server to {ftp_dir_upload_in}")

    else:
        cd_v(ftp_dir_upload_in, ftp=ftp)

    filepath_upload = file.relative_to(strip_pre_upload)
    logger.log(
        LOG_LEVEL_INFO_FILE.name,
        f"Relative to {ftp_dir_upload_in} on the FTP server, "
        f"will upload {file} to {filepath_upload}",
    )

    for parent in list(filepath_upload.parents)[::-1]:
        if parent == Path("."):
            continue

        to_make = parent.parts[-1]

        if ftp is None:
            logger.debug(
                "Dry run. "
                "Would ensure existence of "
                f"and cd on the FTP server to {to_make}"
            )

        else:
            mkdir_v(to_make, ftp=ftp)
            cd_v(to_make, ftp=ftp)

    if ftp is None:
        logger.log(LOG_LEVEL_INFO_FILE.name, f"Dry run. Would upload {file}")

        return ftp

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

            logger.log(LOG_LEVEL_INFO_FILE.name, f"Successfully uploaded {file}")
        except ftplib.error_perm:
            logger.error(
                f"{file.name} already exists on the server in {ftp.pwd()}. "
                "Use a different directory on the receiving server "
                "if you really wish to upload again."
            )
            raise

    return ftp


class FTPConnectionContextManager(Protocol):
    """
    FTP connection context manager
    """

    def __enter__(self) -> ftplib.FTP:
        """Establish the FTP connection"""

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the FTP connection"""


def upload_file_p(
    file: Path,
    strip_pre_upload: Path,
    ftp_dir_upload_in: str,
    get_ftp_connection: GetFTPConnection,
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

        The return type should be a context manager
        that closes the FTP connection when exited.

        If we are doing a dry run, `get_ftp_connection` can simply return `None`.
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
    get_ftp_connection: GetFTPConnection,
    ftp_dir_root: str,
    ftp_dir_rel_to_root: str,
    cvs: Input4MIPsCVs,
    n_threads: int,
    continue_on_error: bool = False,
) -> Optional[ftplib.FTP]:
    """
    Upload files to the FTP server in parallel

    Parameters
    ----------
    files_to_upload
        Files to upload

    get_ftp_connection
        Callable that returns a new FTP connection with which to do the upload.

        The return type should be a context manager
        that closes the FTP connection when exited.

        If we are doing a dry run, `get_ftp_connection` can simply return `None`.

    ftp_dir_root
        Root directory on the FTP server for receiving files.

    ftp_dir_rel_to_root
        Directory, relative to `ftp_dir_root`, in which to upload the files

    cvs
        CVs used when writing the files.

        These are needed to help determine where the DRS path starts.

    n_threads
        Number of threads to use for uploading

    continue_on_error
        Should the upload continue,
        even if an error is raised while trying to upload a particular file?

        If `True`, the exception will be logged and uploads will continue.

    Returns
    -------
    :
        The FTP connection
    """
    with get_ftp_connection() as ftp:
        if ftp is None:
            logger.debug(
                "Dry run. "
                f"Would ensure that {ftp_dir_root}/{ftp_dir_rel_to_root} "
                "existed on the server"
            )

        else:
            cd_v(ftp_dir_root, ftp=ftp)

            mkdir_v(ftp_dir_rel_to_root, ftp=ftp)
            cd_v(ftp_dir_rel_to_root, ftp=ftp)

    logger.info(
        "Uploading in parallel using up to "
        f"{n_threads} {'threads' if n_threads > 1 else 'thread'}"
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=n_threads) as executor:
        futures_dict = {}
        for file in files_to_upload:
            could_not_infer_root_data_dir = False
            try:
                directory_metadata = cvs.DRS.extract_metadata_from_path(
                    file.parent,
                    include_root_data_dir=True,
                )

                if directory_metadata["root_data_dir"] is None:
                    could_not_infer_root_data_dir = True

            except AssertionError:
                could_not_infer_root_data_dir = True

            if could_not_infer_root_data_dir:
                logger.warning(
                    f"Filepath could not be resolved with the DRS, "
                    "we will upload the following file "
                    "without any directory structure. "
                    f"{file=}. "
                    f"{cvs.DRS.directory_path_template=}"
                )
                strip_pre_upload = file.parent

            else:
                if directory_metadata["root_data_dir"] is None:  # pragma: no cover
                    raise AssertionError

                strip_pre_upload = Path(directory_metadata["root_data_dir"])

            future_h = executor.submit(
                upload_file_p,
                file,
                strip_pre_upload=strip_pre_upload,
                ftp_dir_upload_in=f"{ftp_dir_root}/{ftp_dir_rel_to_root}",
                get_ftp_connection=get_ftp_connection,
            )
            futures_dict[future_h] = file

        any_errors = False
        for future in concurrent.futures.as_completed(futures_dict):
            file = futures_dict[future]
            if continue_on_error:
                try:
                    future.result()
                except Exception:
                    any_errors = True
                    logger.exception(f"Exception raised while trying to upload {file}")

            else:
                # Call in case there are any errors
                future.result()

    if not any_errors:
        logger.success("Uploaded all files")

    else:
        logger.info("Finished trying to upload files")

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
    dry_run: bool = False,
    continue_on_error: bool = False,
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

    dry_run
        Is this a dry run?

        If `True`, we won't actually upload the files,
        we'll just log the messages.

    continue_on_error
        Should the upload continue,
        even if an error is raised while trying to upload a particular file?

        If `True`, the exception will instead be logged and uploads will continue.
    """
    get_ftp_connection = partial(
        login_to_ftp,
        ftp_server=ftp_server,
        username=username,
        password=password,
        dry_run=dry_run,
    )

    upload_files_p(
        files_to_upload=tree_root.rglob(rglob_input),
        get_ftp_connection=get_ftp_connection,
        ftp_dir_root=ftp_dir_root,
        ftp_dir_rel_to_root=ftp_dir_rel_to_root,
        cvs=cvs,
        n_threads=n_threads,
        continue_on_error=continue_on_error,
    )
