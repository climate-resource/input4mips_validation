"""
Test that a valid file passes our testing
"""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from input4mips_validation.cli import cli

TEST_DATA_DIR = Path(__file__).parent.parent / "test-data"


@pytest.mark.parametrize(
    "valid_file",
    (
        pytest.param(
            TEST_DATA_DIR / "valid-files" / "path_to_pauls_file.nc",
            id="paul_durack_cmip6plus",
            marks=pytest.mark.xfail(reason="Waiting to download file"),
        ),
    ),
)
def test_valid_file_passes(valid_file):
    runner = CliRunner()

    result = runner.invoke(cli, ["validate", valid_file])
    assert not result.exception
    expected_stdout = (
        "TBD, could confirm that the file is valid "
        "or something else depending on e.g. logging levels"
    )
    assert result.output == expected_stdout
