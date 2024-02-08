"""
Test that a valid file passes our testing
"""
from __future__ import annotations

from pathlib import Path

import pytest
from click.testing import CliRunner

from input4mips_validation.cli import root_cli

TEST_DATA_DIR = Path(__file__).parent.parent / "test-data"


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
            id="paul_durack_cmip6plus_tos",
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
            id="paul_durack_cmip6plus_siconc",
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
            id="paul_durack_cmip6plus_sftof",
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
            id="paul_durack_cmip6plus_areacello",
        ),
    ),
)
def test_valid_file_passes(valid_file):
    runner = CliRunner()

    result = runner.invoke(root_cli, ["validate-file", valid_file])
    assert not result.exception
    expected_stdout = (
        "TBD, could confirm that the file is valid "
        "or something else depending on e.g. logging levels"
    )
    assert result.output == expected_stdout
