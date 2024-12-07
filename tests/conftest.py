"""
Re-useable fixtures etc. for tests

See https://docs.pytest.org/en/7.1.x/reference/fixtures.html#conftest-py-sharing-fixtures-across-multiple-files
"""

from __future__ import annotations

from pathlib import Path

import pytest

from input4mips_validation.cvs import Input4MIPsCVs, load_cvs


@pytest.fixture
def test_cvs() -> Input4MIPsCVs:
    test_input4mips_cvs_path = (
        Path(__file__).parent / "test-data" / "cvs" / "default"
    ).absolute()

    res = load_cvs(test_input4mips_cvs_path)

    return res
