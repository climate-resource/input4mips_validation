"""
Tests of path parsing with the DRS
"""

from contextlib import nullcontext as does_not_raise

import pytest

from input4mips_validation.cvs.drs import DataReferenceSyntax


@pytest.mark.parametrize(
    "directory_path_template, directory, exp_raise, exp_res",
    (
        (
            "<activity_id>/<mip_era>/<target_mip>/<institution_id>/<source_id>/<realm>/<frequency>/<variable_id>/<grid_label>/v<version>",
            "/root/input4MIPs/CMIP6Plus/CMIP/PCMDI/PCMDI-AMIP-1-1-9/ocean/mon/tos/gn/v20230512/",
            does_not_raise(),
            {
                "activity_id": "input4MIPs",
                "frequency": "mon",
                "grid_label": "gn",
                "institution_id": "PCMDI",
                "mip_era": "CMIP6Plus",
                "realm": "ocean",
                "source_id": "PCMDI-AMIP-1-1-9",
                "target_mip": "CMIP",
                "variable_id": "tos",
                "version": "20230512",
            },
        ),
        pytest.param(
            "<activity_id>/<mip_era>/<target_mip>/<institution_id>/<source_id>/<realm>/<frequency>/<variable_id>/<grid_label>/v<version>",
            "input4MIPs/CMIP/PCMDI/PCMDI-AMIP-1-1-9/ocean/mon/tos/gn/v20230512/",
            pytest.raises(
                AssertionError,
                match="regexp failed. directory_regexp='.*'. directory='.*'",
            ),
            None,
            id="missing_mip_era",
        ),
    ),
)
def test_extract_metadata_from_path(
    directory_path_template, directory, exp_raise, exp_res
):
    drs = DataReferenceSyntax(
        directory_path_template=directory_path_template,
        directory_path_example="not_used",
        filename_template="not_used",
        filename_example="not_used",
    )
    with exp_raise:
        res = drs.extract_metadata_from_path(directory)

    if exp_res is not None:
        assert res == exp_res


@pytest.mark.parametrize(
    "filename_template, filename, exp_raise, exp_res",
    (
        (
            "<variable_id>_<activity_id>_<dataset_category>_<target_mip>_<source_id>_<grid_label>[_<time_range>].nc",
            "tos_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc",
            does_not_raise(),
            {
                "activity_id": "input4MIPs",
                "dataset_category": "SSTsAndSeaIce",
                "grid_label": "gn",
                "source_id": "PCMDI-AMIP-1-1-9",
                "target_mip": "CMIP",
                "time_range": "187001-202212",
                "variable_id": "tos",
            },
        ),
        pytest.param(
            "<variable_id>_<activity_id>_<dataset_category>_<target_mip>_<source_id>_<grid_label>[_<time_range>].nc",
            "tos_percentage_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc",
            pytest.raises(
                AssertionError,
                match="regexp failed. filename_regexp='.*'. filename='.*'",
            ),
            None,
            id="underscore_in_variable_id",
        ),
    ),
)
def test_extract_metadata_from_filename(
    filename_template, filename, exp_raise, exp_res
):
    drs = DataReferenceSyntax(
        directory_path_template="not_used",
        directory_path_example="not_used",
        filename_template=filename_template,
        filename_example="not_used",
    )
    with exp_raise:
        res = drs.extract_metadata_from_filename(filename)

    if exp_res is not None:
        assert res == exp_res
