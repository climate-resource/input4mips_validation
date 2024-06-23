"""
Test loading of raw CV data

This includes testing how loading from different sources will be handled.
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

import input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import (
    CVsRoot,
    get_cvs_root,
    load_raw_cv_definition,
)


@pytest.mark.parametrize(
    "input4mips_cv_source, exp_root",
    [
        pytest.param(
            "gh:main",
            CVsRoot(
                location="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main/",
                remote=True,
            ),
            id="github_main",
        ),
        pytest.param(
            "gh:branch-name",
            CVsRoot(
                location="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/branch-name/",
                remote=True,
            ),
            id="github_branch",
        ),
        pytest.param(
            "gh:commitae84110",
            CVsRoot(
                location="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/commitae84110/",
                remote=True,
            ),
            id="github_commit",
        ),
        pytest.param(
            "https://raw.githubusercontent.com/znichollscr/input4MIPs_CVs/commitae84109/",
            CVsRoot(
                location="https://raw.githubusercontent.com/znichollscr/input4MIPs_CVs/commitae84109/",
                remote=True,
            ),
            id="github_commit_fork",
        ),
        pytest.param(
            "../path/to/somewhere",
            CVsRoot(
                location="../path/to/somewhere",
                remote=False,
            ),
            id="no_gh_prefix_hence_path",
        ),
    ],
)
def test_get_cvs_root(input4mips_cv_source, exp_root):
    with patch.dict(
        os.environ, {"INPUT4MIPS_VALIDATION_INPUT4MIPS_CV_SOURCE": input4mips_cv_source}
    ):
        res = get_cvs_root()

    assert res == exp_root


def test_load_raw_cv_path():
    filename = "filename_cv.json"
    root = CVsRoot(location="path/to/somewhere", remote=False)
    exp = "Some data\nprobably json\nis expected"

    with patch("builtins.open", mock_open(read_data=exp)) as mock_open_func:
        res = load_raw_cv_definition(filename=filename, root=root)

    assert res == exp
    mock_open_func.assert_called_once_with(Path(root.location) / filename)


# TODO: add test of force download here
@pytest.mark.parametrize(
    "force_download, force_download_exp",
    (
        (None, False),
        (False, False),
        (True, True),
    ),
)
@patch("input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.remove_file")
def test_load_raw_cv_gh_known_registry(
    mock_remove_file, force_download, force_download_exp
):
    filename = "filename_cv.json"
    known_url = "http://known/url"
    root = CVsRoot(location=known_url, remote=True)

    exp = "Some data\nprobably json\nis expected"

    mock_full_path = "path/to/some/pooch/location.txt"
    mock_pooch_registry = MagicMock()
    mock_pooch_registry.fetch = MagicMock(return_value=mock_full_path)
    mock_registries = {known_url: mock_pooch_registry}

    call_kwargs = {}
    if force_download is not None:
        call_kwargs["force_download"] = force_download

    with patch.dict(
        input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading.KNOWN_REGISTRIES,
        mock_registries,
    ):
        with patch("builtins.open", mock_open(read_data=exp)) as mock_open_func:
            res = load_raw_cv_definition(filename=filename, root=root, **call_kwargs)

    assert res == exp

    if force_download_exp:
        mock_remove_file.assert_called_once_with(mock_pooch_registry.path / filename)

    # Check that pooch would be called correctly
    mock_pooch_registry.fetch.assert_called_once_with(
        filename,
    )

    # Check that the filepath would have been opened
    mock_open_func.assert_called_once_with(mock_full_path)
