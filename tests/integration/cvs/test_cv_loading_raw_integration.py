"""
Test loading of raw CV data

This includes testing how loading from different sources will be handled.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pooch
import pytest

from input4mips_validation.cvs.loading_raw import (
    RawCVLoaderBaseURL,
    RawCVLoaderKnownRemoteRegistry,
    # KNOWN_REGISTRIES,
    RawCVLoaderLocal,
    get_raw_cvs_loader,
)


@pytest.mark.parametrize(
    "input4mips_cv_source, force_download, exp",
    [
        pytest.param(
            "gh:main",
            None,
            RawCVLoaderBaseURL(
                base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main/CVs/",
            ),
            id="github_main",
        ),
        pytest.param(
            "gh:main",
            False,
            RawCVLoaderBaseURL(
                base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main/CVs/",
            ),
            id="github_main_no_force_download",
        ),
        pytest.param(
            "gh:main",
            True,
            RawCVLoaderBaseURL(
                base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main/CVs/",
            ),
            id="github_main_force_download",
        ),
        pytest.param(
            "gh:branch-name",
            None,
            RawCVLoaderBaseURL(
                base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/branch-name/CVs/",
            ),
            id="github_branch",
        ),
        pytest.param(
            "gh:commitae84110",
            None,
            RawCVLoaderBaseURL(
                base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/commitae84110/CVs/",
            ),
            id="github_commit",
        ),
        pytest.param(
            "gh:v1.0.0",
            None,
            RawCVLoaderKnownRemoteRegistry(
                registry="junk",
                # # In future, this will have something like the below
                # registry=KNOWN_REGISTRIES["https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/v1.0.0/CVs/"],
            ),
            id="github_known_version",
            marks=pytest.mark.xfail(reason="No known version release on GitHub yet"),
        ),
        pytest.param(
            "gh:v1.0.0",
            False,
            RawCVLoaderKnownRemoteRegistry(
                registry="junk",
                # # In future, this will have something like the below
                # registry=KNOWN_REGISTRIES["https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/v1.0.0/CVs/"],
            ),
            id="github_known_version_no_force_download",
            marks=pytest.mark.xfail(reason="No known version release on GitHub yet"),
        ),
        pytest.param(
            "gh:v1.0.0",
            True,
            RawCVLoaderKnownRemoteRegistry(
                registry="junk",
                # # In future, this will have something like the below
                # registry=KNOWN_REGISTRIES["https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/v1.0.0/CVs/"],
                force_download=True,
            ),
            id="github_known_version_force_download",
            marks=pytest.mark.xfail(reason="No known version release on GitHub yet"),
        ),
        pytest.param(
            "../path/to/somewhere",
            None,
            RawCVLoaderLocal(
                root_dir=Path("../path/to/somewhere"),
            ),
            id="no_gh_prefix_hence_path",
        ),
        pytest.param(
            "../path/to/somewhere",
            True,
            RawCVLoaderLocal(
                root_dir=Path("../path/to/somewhere"),
            ),
            id="no_gh_prefix_hence_path_force_passed_too",
        ),
    ],
)
def test_get_raw_cvs_loader(input4mips_cv_source, force_download, exp):
    call_kwargs = {}
    if force_download is not None:
        call_kwargs["force_download"] = force_download

    res = get_raw_cvs_loader(cv_source=input4mips_cv_source, **call_kwargs)

    assert res == exp

    # Also test setting through environment variables
    environ_patches = {
        "INPUT4MIPS_VALIDATION_CV_SOURCE": input4mips_cv_source,
    }

    if force_download is not None:
        environ_patches["INPUT4MIPS_VALIDATION_CV_SOURCE_FORCE_DOWNLOAD"] = str(
            force_download
        )

    with patch.dict(os.environ, environ_patches):
        res = get_raw_cvs_loader()

    assert res == exp


def test_load_raw_local():
    root_dir = Path("/test/root/dir")
    filename = "input4MIPs_cv_file.json"
    exp = "Some data\nprobably json\nis expected"

    with patch("builtins.open", mock_open(read_data=exp)) as mock_open_func:
        res = RawCVLoaderLocal(root_dir=root_dir).load_raw(filename)

    assert res == exp

    # Check the filepath that would have been opened
    mock_open_func.assert_called_once_with(root_dir / filename)


@pytest.mark.parametrize(
    "force_download, file_already_exists",
    (
        (True, True),
        (True, False),
        (False, None),
    ),
)
def test_load_raw_known_remote_registry(force_download, file_already_exists, tmp_path):
    registry_path = tmp_path / "cache-dir"
    filename = "input4MIPs_cv_file.json"

    mock_fetch_return_value = str(Path(registry_path) / filename)

    exp = "Some data\nprobably json\nis expected"

    if force_download and file_already_exists:
        # Actually create a file, so we can check it is deleted later
        Path(mock_fetch_return_value).parent.mkdir(parents=True, exist_ok=True)
        with open(mock_fetch_return_value, "w") as fh:
            fh.write(exp)

    mock_registry = MagicMock()
    mock_registry.path = registry_path
    mock_registry.fetch = MagicMock(return_value=mock_fetch_return_value)

    with patch("builtins.open", mock_open(read_data=exp)) as mock_open_func:
        res = RawCVLoaderKnownRemoteRegistry(
            registry=mock_registry, force_download=force_download
        ).load_raw(filename)

    assert res == exp

    # Check the filepath that would have been opened
    mock_open_func.assert_called_once_with(Path(mock_fetch_return_value))

    if force_download:
        # Check that the file was removed or never existed.
        # No file should have been downloaded in its place because our registry
        # is just a mock registry.
        assert not Path(mock_fetch_return_value).exists()


def test_load_raw_base_url_no_slash_ending():
    bad_url = "http://www.domain.com/incorrect/ending"
    error_msg = re.escape(f"base_url must end with a '/', received: value={bad_url!r}")
    with pytest.raises(ValueError, match=error_msg):
        RawCVLoaderBaseURL(base_url=bad_url)


@pytest.mark.parametrize(
    "force_download, file_already_exists",
    (
        (True, True),
        (True, False),
        (False, None),
    ),
)
@patch("input4mips_validation.cvs.loading_raw.pooch.retrieve")
def test_load_raw_base_url(
    mock_pooch_retrieve, force_download, file_already_exists, tmp_path
):
    base_url = "http://path-to-somewhere.com/folder/here/something/"
    download_path = tmp_path / "cache-dir"
    filename = "input4MIPs_cv_file.json"

    expected_url = f"{base_url}{filename}"
    filename_pooch = pooch.utils.unique_file_name(expected_url)

    mock_pooch_retrieve.return_value = str(Path(download_path) / filename_pooch)

    exp = "Some data\nprobably json\nis expected"

    if force_download and file_already_exists:
        # Actually create a file, so we can check it is deleted later
        Path(mock_pooch_retrieve.return_value).parent.mkdir(parents=True, exist_ok=True)
        with open(mock_pooch_retrieve.return_value, "w") as fh:
            fh.write(exp)

    with patch("builtins.open", mock_open(read_data=exp)) as mock_open_func:
        res = RawCVLoaderBaseURL(
            base_url=base_url,
            download_path=download_path,
            force_download=force_download,
        ).load_raw(filename)

    assert res == exp

    # Check that pooch was called correctly
    mock_pooch_retrieve.assert_called_once_with(
        url=expected_url,
        fname=filename_pooch,
        path=download_path,
        known_hash=None,
    )
    # Check the filepath that would have been opened
    mock_open_func.assert_called_once_with(Path(mock_pooch_retrieve.return_value))

    if force_download:
        # Check that the file was removed or never existed.
        # No file should have been downloaded in its place because our registry
        # is just a mock registry.
        assert not Path(mock_pooch_retrieve.return_value).exists()
