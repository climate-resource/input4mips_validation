"""
Test CLI passes through correctly
"""
from __future__ import annotations

import re

from typer.testing import CliRunner

from input4mips_validation.cli import app


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)


def test_subcommand_validate_file_help():
    runner = CliRunner()
    result = runner.invoke(app, ["validate-file", "--help"])
    assert result.exit_code == 0
    assert re.match(r"Usage: ", result.output)


def test_subcommand_validate_file_invalid_if_input_does_not_exist():
    runner = CliRunner()
    result = runner.invoke(app, ["validate-file", "junk.py"])
    assert result.exit_code == 2
    assert re.search(r"Invalid value for 'FILEPATH'.*does not exist", result.output)


def test_subcommand_validate_file_invalid_if_input_is_directory(tmpdir):
    runner = CliRunner()
    result = runner.invoke(app, ["validate-file", str(tmpdir)])
    assert result.exit_code == 2
    assert re.search(r"Invalid value for 'FILEPATH'.*is a directory", result.output)
