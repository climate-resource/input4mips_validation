"""
Integration tests of the CLI
"""

from __future__ import annotations

from typer.testing import CliRunner

import input4mips_validation
from input4mips_validation.cli import app

runner = CliRunner()


def test_version():
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0, result.exc_info
    assert (
        result.stdout == f"input4mips-validation {input4mips_validation.__version__}\n"
    )
