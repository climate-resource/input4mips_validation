"""
Test CLI passes through correctly
"""
from __future__ import annotations

import re

from click.testing import CliRunner

from input4mips_validation.cli import root_cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(root_cli, ["--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)


def test_subcommand_validate_file_help():
    runner = CliRunner()
    result = runner.invoke(root_cli, ["validate-file", "--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)
