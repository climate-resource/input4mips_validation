"""
Handling of controlled vocabularies specific to input4MIPs
"""
from __future__ import annotations

import json
import os
from pathlib import Path

import pooch.utils
import validators
from attrs import define

from input4mips_validation.controlled_vocabularies.handling.input4MIPs.pooch_registries import (  # noqa: E501
    KNOWN_REGISTRIES,
)
from input4mips_validation.controlled_vocabularies.handling.input4MIPs.source_id import (  # noqa: E501
    SourceIDEntry,
)
from input4mips_validation.controlled_vocabularies.handling.serialisation import (
    converter_json,
)

HERE = Path(__file__).parent


@define
class CVsRoot:
    """CVs root information"""

    location: str
    """Location"""

    remote: bool
    """
    Whether the root CVs information needs to be retrieved from a remote source or not
    """


def get_cvs_root(cv_source: None | str = None) -> CVsRoot:
    """
    Get the root of the CVs

    Parameters
    ----------
    cv_source
        String identifying the source of the CVs.

        If not supplied, this is retrieved from the environment variable
        `INPUT4MIPS_VALIDATION_INPUT4MIPS_CV_SOURCE`.

        If this environment variable is also not set,
        we use [TODO decide what default should be].

        If this starts with "gh:", we retrieve the data from PCMD's GitHub.

        Otherwise we simply return the path as provided
        and use the {py:mod}`validators` package
        to decide if the source is remote or not.

    Returns
    -------
        Root of the CVs
    """
    if cv_source is None:
        cv_source = os.environ.get("INPUT4MIPS_VALIDATION_INPUT4MIPS_CV_SOURCE", None)

    if cv_source is None:
        msg = "Default source has not been decided yet"
        raise NotImplementedError(msg)

    if cv_source.startswith("gh:"):
        source = cv_source.split("gh:")[1]
        return CVsRoot(
            location=f"https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/{source}/",
            remote=True,
        )

    if validators.url(cv_source):
        remote = True
    else:
        remote = False

    return CVsRoot(location=cv_source, remote=remote)


def load_raw_cv(
    filename: str, root: CVsRoot, force_download: bool | None = None
) -> str:
    """
    Load raw CV data

    Parameters
    ----------
    filename
        Filename of the data to load

    root
        Root from which the file should be loaded

    force_download
        If we are downloading from a remote source,
        should the download be forced.

        If not supplied, this is retrieved from the environment variable
        `INPUT4MIPS_VALIDATION_INPUT4MIPS_CV_SOURCE_FORCE_DOWNLOAD`.

        If this environment variable is also not set,
        we use ``False``.

    Returns
    -------
        Raw data contained in the file
    """
    if force_download is None:
        force_download = bool(
            os.environ.get(
                "INPUT4MIPS_VALIDATION_INPUT4MIPS_CV_SOURCE_FORCE_DOWNLOAD", None
            )
        )
        if force_download is None:
            force_download = False

    if not root.remote:
        full_path = Path(root.location) / filename

    elif root.location in KNOWN_REGISTRIES:
        full_path = get_full_path_from_known_registry(
            filename=filename,
            registry=KNOWN_REGISTRIES[root.location],
            force_download=force_download,
        )

    else:
        full_path = get_full_path_no_known_registry(
            filename=filename, root_url=root.location, force_download=force_download
        )

    with open(full_path) as fh:
        res = fh.read()

    return res


def get_full_path_from_known_registry(
    filename: str, registry: pooch.Pooch, force_download: bool
) -> Path:
    """
    Get the full path to a local file from a known {py:mod}`pooch` registry

    Parameters
    ----------
    filename
        Filename to retrieve

    registry
        {py:mod}`pooch` registry to use to retrieve the file

    force_download
        Should the download of this file be forced?

    Returns
    -------
        Full path to the local file
    """
    if force_download:
        expected_out_file = registry.path / filename
        if expected_out_file.exists():
            expected_out_file.unlink()

    return Path(registry.fetch(filename))


def get_full_path_no_known_registry(
    filename: str, root_url: str, force_download: bool
) -> Path:
    """
    Get the full path to a local file without a known {py:mod}`pooch` registry

    Parameters
    ----------
    filename
        Filename to retrieve

    root_url
        Root URL from which to retrieve the file.
        It is assumed that the path to the file can be created by simply
        joining ``root_url`` and ``filename``.

    force_download
        Should the download of this file be forced?

    Returns
    -------
        Full path to the local file
    """
    url = f"{root_url}{filename}"

    path = HERE / "user_cvs"
    fname_pooch = pooch.utils.unique_file_name(url)

    if force_download:
        expected_out_file = path / fname_pooch
        if expected_out_file.exists():
            expected_out_file.unlink()

    return Path(
        pooch.retrieve(
            url=url,
            fname=fname_pooch,
            path=path,
            known_hash=None,
        )
    )


def convert_raw_cv_to_source_id_entries(
    raw: dict[str, dict[str, dict[str, str]]],
) -> tuple[SourceIDEntry, ...]:
    """
    Convert the raw CV data to {py:obj}`SourceIDEntry`

    Parameters
    ----------
    raw
        Raw CV data

    Returns
    -------
        Source ID entries
    """
    raw_json = json.loads(raw)
    restructured = [
        dict(
            source_id=key,
            **value,
        )
        for key, value in raw_json["source_id"].items()
    ]

    return converter_json.structure(restructured, tuple[SourceIDEntry, ...])


def load_source_ids(
    filename: str = "input4MIPs_source_id.json",
    cv_source: str | None = None,
    force_download: bool | None = None,
) -> tuple[SourceIDEntry, ...]:
    """
    Load source IDs from the CVs

    Parameters
    ----------
    filename
        Filename from which to load the source IDs

    cv_source
        String identifying the source of the CVs.

        Passed to {py:func}`get_cvs_root`.
        For futher details, see the docstring of {py:func}`get_cvs_root`.

    force_download
        Whether to force the download of the CVs.
        Passed to {py:func}`load_raw_cv`.

    Returns
    -------
        Loaded source ID entries.
    """
    cvs_root = get_cvs_root(cv_source=cv_source)
    raw = load_raw_cv(filename=filename, root=cvs_root, force_download=force_download)

    return convert_raw_cv_to_source_id_entries(raw=raw)
