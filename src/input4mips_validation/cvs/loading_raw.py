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
import pooch.utils
import validators
from attrs import field, frozen

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
    "https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/52841b0117474efd2705a083c21b3760531974f3/CVs/": pooch.create(  # noqa: E501
        path=HERE / "input4MIPs_CVs_52841b0117474efd2705a083c21b3760531974f3",
        base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/52841b0117474efd2705a083c21b3760531974f3/CVs",
        registry={
            "input4MIPs_activity_id.json": "sha256:a2fef6e6ea9eb9787288b080d6696d74fd490b7a3c9e0d3d1dd48b9fb5584e6e",  # noqa: E501
            "input4MIPs_DRS.json": "sha256:e9fa7bd692be6054c405a7381654b84df4565800c0b21e2c5c62e61fb3e8f046",  # noqa: E501
            "input4MIPs_institution_id.json": "sha256:db2a6364347aa4848a21416a41f4d1ad24d036e80897c80af6d132b274d562d7",  # noqa: E501
            "input4MIPs_license.json": "sha256:ba771256d7148187675d5f27f17a2b79e5a42db6b620f19120808065c84e5deb",  # noqa: E501
            "input4MIPs_source_id.json": "sha256:cf0c77aa38c456b86f3f37d81137c2703699abe3355a6577440f63e000feec01",  # noqa: E501
        },
    )
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


@frozen
class RawCVLoaderLocal:
    """
    Loader of raw CV data from local data
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


@frozen
class RawCVLoaderKnownRemoteRegistry:
    """
    Loader of raw CV data from a known remote registry

    Known remote registries are assumed to be represented as [pooch.Pooch][].
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


@frozen
class RawCVLoaderBaseURL:
    """
    Loader of raw CV data from some base URL

    Uses [pooch.retrieve][] to manage downloading and storage of files.
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

    Passed to [pooch.retrieve][].

    Defaults to being inside the package so that downloaded files
    are removed when the package is removed.
    """

    force_download: bool = False
    """
    Whether to force a new download of the file if it already exists
    """

    @base_url.validator
    def ends_with_forward_slash(
        self, attribute: attr.Attribute[Any], value: str
    ) -> None:
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
    cv_source: None | str | Path = None, force_download: bool | None = None
) -> RawCVLoader:
    """
    Get the raw CVs loader

    Parameters
    ----------
    cv_source
        String identifying the source of the CVs.

        If not supplied, this is retrieved from the environment variable
        `INPUT4MIPS_VALIDATION_CV_SOURCE`.

        If this environment variable is also not set,
        we raise a `NotImplementedError`.

        If this starts with "gh:", we retrieve the data from PCMD's GitHub,
        using everything after the colon as the ID for the Git commit to use
        (where the ID can be a branch name, a tag or a commit ID).

        Otherwise we simply return the path as provided
        and use the [validators](https://validators.readthedocs.io/en/stable)
        package to decide if the source points to a URL or not.

    force_download
        If we are downloading from a remote source,
        should the raw CV loader be configured so that downloads are forced.

        If not supplied, this is retrieved from the environment variable
        `INPUT4MIPS_VALIDATION_CV_SOURCE_FORCE_DOWNLOAD`.

        If this environment variable is also not set,
        we assume `False`.

    Returns
    -------
    :
        Raw CV loader

    Raises
    ------
    NotImplementedError
        `cv_source` is not supplied and
        `INPUT4MIPS_VALIDATION_CV_SOURCE` is also not set.
    """
    if cv_source is None:
        cv_source = os.environ.get("INPUT4MIPS_VALIDATION_CV_SOURCE", None)

    if cv_source is None:
        msg = "Default source has not been decided yet"
        raise NotImplementedError(msg)

    if force_download is None:
        try:
            force_download = bool(
                os.environ["INPUT4MIPS_VALIDATION_CV_SOURCE_FORCE_DOWNLOAD"]
            )

        except KeyError:
            # Nothing provided as environment variable, hence set a default
            force_download = False

    if isinstance(cv_source, str) and cv_source.startswith("gh:"):
        # Expand out the given value
        source = cv_source.split("gh:")[1]
        cv_source = (
            f"https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/{source}/CVs/"
        )

    if isinstance(cv_source, Path):
        res: RawCVLoader = RawCVLoaderLocal(cv_source)

    elif not validators.url(cv_source):
        res = RawCVLoaderLocal(Path(cv_source))

    else:
        try:
            res = RawCVLoaderKnownRemoteRegistry(KNOWN_REGISTRIES[cv_source])
        except KeyError:
            res = RawCVLoaderBaseURL(base_url=cv_source)

    return res
