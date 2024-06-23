"""
Tools for loading the raw CVs

This allows us to access CVs defined locally as well as in remote sources,
specifically on GitHub.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Protocol

import attr
import attrs
import pooch
import validators
from attrs import define, field

HERE = Path(__file__).parent

KNOWN_REGISTRIES: dict[str, pooch.Pooch] = {
    # Empty for now
    # # The idea would be to do something like
    # "https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/v1.0.0": pooch.create(
    #     # Use the default cache folder for the operating system
    #     path=HERE / "input4MIPs_CVs_v1.0.0",
    #     base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main",
    #     registry={
    #         "input4MIPs_source_id.json": "sha256:19uheidhlkjdwhoiwuhc0uhcwljchw9ochwochw89dcgw9dcgwc",  # noqa: E501
    #         "input4MIPs_activity_id.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #         "input4MIPs_institution_id.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #         "input4MIPs_license.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #         "input4MIPs_mip_era.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #     },
    # )
}


class RawCVLoader(Protocol):
    """Loader of raw CV data"""

    def load_raw(self, filename: str) -> str:
        """
        Load raw CV data

        Parameters
        ----------
        filename
            Filename from which to load raw CV data

        Returns
        -------
            Raw CV data
        """
        ...


@define
class RawCVLoaderLocal:
    """
    Loader of raw CV data from local data

    Known remote registries are assumed to be represented as {py:obj}`pooch.Pooch`.
    """

    root_dir: Path
    """
    Root directory in which the raw CV data is stored
    """

    def load_raw(self, filename: str) -> str:
        """
        Load raw CV data

        Parameters
        ----------
        filename
            Filename from which to load raw CV data

        Returns
        -------
            Raw CV data
        """
        with open(self.root_dir / filename) as fh:
            raw = fh.read()

        return raw


@define
class RawCVLoaderKnownRemoteRegistry:
    """
    Loader of raw CV data from a known remote registry

    Known remote registries are assumed to be represented as {py:obj}`pooch.Pooch`.
    """

    registry: pooch.Pooch
    """
    Pooch registry to use for retrieving and managing files
    """

    force_download: bool = False
    """
    Whether to force a new download of the file if it already exists
    """

    def load_raw(self, filename: str) -> str:
        """
        Load raw CV data

        Parameters
        ----------
        filename
            Filename from which to load raw CV data

        Returns
        -------
            Raw CV data
        """
        if self.force_download:
            expected_out_file = Path(self.registry.path) / filename
            if expected_out_file.exists():
                expected_out_file.unlink()

        with open(Path(self.registry.fetch(filename))) as fh:
            raw = fh.read()

        return raw


@define
class RawCVLoaderBaseURL:
    """
    Loader of raw CV data from some base URL

    Uses {py:func}`pooch.retrieve` to manage downloading and storage of files.
    """

    base_url: str = field(validator=attrs.validators.instance_of(str))
    """
    Base URL from which to load files

    The filename is simply appended to the end of the base URL
    to create the URL from which to request the file.
    """

    download_path: Path = HERE / "user_cvs"
    """
    Path in which to save downloaded files

    Passed to {py:func}`pooch.retrieve`.

    Defaults to being inside the package so that downloaded files
    are removed when the package is removed.
    """

    force_download: bool = False
    """
    Whether to force a new download of the file if it already exists
    """

    @base_url.validator
    def ends_with_forward_slash(self, attribute: attr.Attribute[Any], value: str):
        """
        Assert that the value ends with a forward slash
        """
        if not value.endswith("/"):
            msg = f"{attribute.name} must end with a '/', received: {value=!r}"
            raise ValueError(msg)

    def load_raw(self, filename: str) -> str:
        """
        Load raw CV data

        Parameters
        ----------
        filename
            Filename from which to load raw CV data

        Returns
        -------
            Raw CV data
        """
        url = f"{self.base_url}{filename}"
        fname_pooch = pooch.utils.unique_file_name(url)

        if self.force_download:
            expected_out_file = self.download_path / fname_pooch
            if expected_out_file.exists():
                expected_out_file.unlink()

        with open(
            Path(
                pooch.retrieve(
                    url=url,
                    fname=fname_pooch,
                    path=self.download_path,
                    known_hash=None,
                )
            )
        ) as fh:
            raw = fh.read()

        return raw


def get_raw_cvs_loader(
    cv_source: None | str = None, force_download: bool | None = None
) -> RawCVLoader:
    """
    Get the raw CVs loader

    Parameters
    ----------
    cv_source
        String identifying the source of the CVs.

        If not supplied, this is retrieved from the environment variable
        ``INPUT4MIPS_VALIDATION_CV_SOURCE``.

        If this environment variable is also not set,
        we raise a ``NotImplementedError``.

        If this starts with "gh:", we retrieve the data from PCMD's GitHub,
        using everything after the colon as the ID for the Git commit to use
        (where the ID can be a branch name, a tag or a commit ID).

        Otherwise we simply return the path as provided
        and use the {py:mod}`validators` package
        to decide if the source points to a URL or not.

    force_download
        If we are downloading from a remote source,
        should the raw CV loader be configured so that downloads are forced.

        If not supplied, this is retrieved from the environment variable
        ``INPUT4MIPS_VALIDATION_CV_SOURCE_FORCE_DOWNLOAD``.

        If this environment variable is also not set,
        we use ``False``.

    Returns
    -------
        Raw CV loader

    Raises
    ------
    NotImplementedError
        ``cv_source`` is not supplied and
        ``INPUT4MIPS_VALIDATION_CV_SOURCE`` is also not set.
    """
    if cv_source is None:
        cv_source = os.environ.get("INPUT4MIPS_VALIDATION_CV_SOURCE", None)

    if cv_source is None:
        msg = "Default source has not been decided yet"
        raise NotImplementedError(msg)

    if force_download is None:
        force_download = bool(
            os.environ.get("INPUT4MIPS_VALIDATION_CV_SOURCE_FORCE_DOWNLOAD", None)
        )
        if force_download is None:
            force_download = False

    if cv_source.startswith("gh:"):
        # Expand out the given value
        source = cv_source.split("gh:")[1]
        cv_source = f"https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/{source}/"

    if not validators.url(cv_source):
        res = RawCVLoaderLocal(Path(cv_source))

    else:
        try:
            res = RawCVLoaderKnownRemoteRegistry(KNOWN_REGISTRIES[cv_source])
        except KeyError:
            res = RawCVLoaderBaseURL(base_url=cv_source)

    return res
