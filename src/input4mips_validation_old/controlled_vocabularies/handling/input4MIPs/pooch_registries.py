"""
{py:mod}`pooch` registries

These capture the known registries for CVs
"""
from __future__ import annotations

from pathlib import Path

# import pooch


HERE = Path(__file__).parent

KNOWN_REGISTRIES = {
    # Empty for now
    # # The idea would be to do something like
    # "https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/v1.0.0": pooch.create(
    #     # Use the default cache folder for the operating system
    #     path=HERE / "input4MIPs_CVs_v1.0.0",
    #     base_url="https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main",
    #     registry={
    #         "input4MIPs_source_id.json": "sha256:19uheidhlkjdwhoiwuhc0uhcwljchw9ochwochw89dcgw9dcgwc",  # noqa: E501
    #         "input4MIPs_activity_id.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #         "input4MIPs_institution_id.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #         "input4MIPs_license.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #         "input4MIPs_mip_era.json": "sha256:1upodh2ioduhw9celdjhlfvhksgdwikdgcowjhcwoduchowjg8w",  # noqa: E501
    #     },
    # )
}
