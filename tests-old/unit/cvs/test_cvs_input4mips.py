"""
Test of input4MIPs CVs handling
"""
from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest

import input4mips_validation.controlled_vocabularies.handling.input4MIPs
from input4mips_validation.controlled_vocabularies.handling.input4MIPs import (
    CVsRoot,
    get_cvs_root,
    load_raw_cv,
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
        res = load_raw_cv(filename=filename, root=root)

    assert res == exp
    mock_open_func.assert_called_once_with(Path(root.location) / filename)


@patch(
    "input4mips_validation.controlled_vocabularies.handling.input4MIPs.get_full_path_from_known_registry"
)
def test_load_raw_cv_gh_known_registry(
    mock_get_full_path_from_known_registry,
):
    filename = "filename_cv.json"
    known_url = "http://known/url"
    root = CVsRoot(location=known_url, remote=True)

    mock_full_path = "path/to/some/pooch/location.txt"
    mock_get_full_path_from_known_registry.return_value = mock_full_path
    exp = "Some data\nprobably json\nis expected"

    mock_registries = {known_url: MagicMock()}

    with patch.dict(
        input4mips_validation.controlled_vocabularies.handling.input4MIPs.KNOWN_REGISTRIES,
        mock_registries,
    ):
        with patch("builtins.open", mock_open(read_data=exp)) as mock_open_func:
            res = load_raw_cv(filename=filename, root=root)

    assert res == exp
    mock_get_full_path_from_known_registry.assert_called_once_with(
        filename=filename,
        registry=mock_registries[known_url],
        force_download=False,
    )
    mock_open_func.assert_called_once_with(mock_full_path)
