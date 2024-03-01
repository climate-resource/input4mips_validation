"""
Test that a valid file passes our testing
"""
from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from input4mips_validation.cli import app

TEST_DATA_DIR = Path(__file__).parent.parent / "test-data"


xfail_paul_file = pytest.mark.xfail(
    reason=(
        "Somehow xarray can't tell "
        "that only one variable is a data variable in these files. "
        "Not sure whether this is an xarray problem or a file formatting problem."
        "On CI, test files don't exist "
        "(haven't worked out how to handle that best yet)."
    )
)


@pytest.mark.parametrize(
    "valid_file",
    (
        pytest.param(
            str(
                TEST_DATA_DIR
                / "input4MIPs"
                / "CMIP6Plus"
                / "CMIP"
                / "PCMDI"
                / "PCMDI-AMIP-1-1-9"
                / "ocean"
                / "mon"
                / "tos"
                / "gn"
                / "v20230512"
                / "tos_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc"  # noqa: E501
            ),
            id="paul_example_cmip6plus_tos",
            marks=xfail_paul_file,
        ),
        pytest.param(
            str(
                TEST_DATA_DIR
                / "input4MIPs"
                / "CMIP6Plus"
                / "CMIP"
                / "PCMDI"
                / "PCMDI-AMIP-1-1-9"
                / "ocean"
                / "mon"
                / "siconc"
                / "gn"
                / "v20230512"
                / "siconc_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc"  # noqa: E501
            ),
            id="paul_example_cmip6plus_siconc",
            marks=xfail_paul_file,
        ),
        pytest.param(
            str(
                TEST_DATA_DIR
                / "input4MIPs"
                / "CMIP6Plus"
                / "CMIP"
                / "PCMDI"
                / "PCMDI-AMIP-1-1-9"
                / "ocean"
                / "fx"
                / "sftof"
                / "gn"
                / "v20230512"
                / "sftof_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn.nc"
            ),
            id="paul_example_cmip6plus_sftof",
            marks=xfail_paul_file,
        ),
        pytest.param(
            str(
                TEST_DATA_DIR
                / "input4MIPs"
                / "CMIP6Plus"
                / "CMIP"
                / "PCMDI"
                / "PCMDI-AMIP-1-1-9"
                / "ocean"
                / "fx"
                / "areacello"
                / "gn"
                / "v20230512"
                / "areacello_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn.nc"
            ),
            id="paul_example_cmip6plus_areacello",
            marks=xfail_paul_file,
        ),
    ),
)
def test_valid_file_passes(valid_file):
    runner = CliRunner()

    result = runner.invoke(app, ["validate-file", valid_file])
    assert not result.exception
    expected_stdout = (
        "TBD, could confirm that the file is valid "
        "or something else depending on e.g. logging levels"
    )
    assert result.output == expected_stdout
