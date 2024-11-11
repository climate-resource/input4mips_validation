"""
Tests of path parsing with the DRS
"""

from contextlib import nullcontext as does_not_raise
from pathlib import Path

import cftime
import numpy as np
import pytest
import xarray as xr

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
            "/root/input4MIPs/CMIP6Plus/CMIP/PCMDI/PCMDI-AMIP-1-1-9/ocean/mon/co2_em_anthro/gn/v20230512/",
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
                "variable_id": "co2_em_anthro",
                "version": "20230512",
            },
            id="underscore_in_variable_id",
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
def test_extract_metadata_from_directory(
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
            "co2-em-anthro_input4MIPs_SSTsAndSeaIce_CMIP_PCMDI-AMIP-1-1-9_gn_187001-202212.nc",
            does_not_raise(),
            {
                "activity_id": "input4MIPs",
                "dataset_category": "SSTsAndSeaIce",
                "grid_label": "gn",
                "source_id": "PCMDI-AMIP-1-1-9",
                "target_mip": "CMIP",
                "time_range": "187001-202212",
                "variable_id": "co2-em-anthro",
            },
            id="underscore_in_variable_id_correctly_replaced_by_hyphen",
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


@pytest.mark.parametrize(
    [
        "directory_path_template",
        "filename_template",
        "fullpath",
        "global_attributes",
        "time_axis",
        "exp_raise",
    ],
    (
        pytest.param(
            "<activity_id>/<mip_era>/<target_mip>/<institution_id>/<source_id>/<realm>/<frequency>/<variable_id>/<grid_label>/v<version>",
            "<variable_id>_<activity_id>_<dataset_category>_<target_mip>_<source_id>_<grid_label>[_<time_range>].nc",
            (
                Path("input4MIPs")
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
            {
                "activity_id": "input4MIPs",
                "dataset_category": "SSTsAndSeaIce",
                "frequency": "mon",
                "grid_label": "gn",
                "institution_id": "PCMDI",
                "mip_era": "CMIP6Plus",
                "realm": "ocean",
                "source_id": "PCMDI-AMIP-1-1-9",
                "target_mip": "CMIP",
                "time_range": "187001-202212",
                "variable_id": "tos",
                "version": "20230512",
            },
            [
                cftime.datetime(y, m, 1)
                for y in range(1870, 2022 + 1)
                for m in range(1, 12 + 1)
            ],
            does_not_raise(),
            id="cmip6_passing",
        ),
        pytest.param(
            "<activity_id>/<source_id>/<variable_id>",
            "<variable_id>_<source_id>[_<time_range>].nc",
            (
                Path("input4MIPs")
                / "CR-CMIP-1-0-0"
                / "co2_em_anthro"
                / "co2-em-anthro_CR-CMIP-1-0-0_2015-2020.nc"
            ),
            {
                "activity_id": "input4MIPs",
                "variable_id": "co2_em_anthro",
                "source_id": "CR-CMIP-1-0-0",
                "time_range": "2015-2020",
                "frequency": "yr",
            },
            [cftime.datetime(y, 7, 1) for y in range(2015, 2020 + 1)],
            does_not_raise(),
            id="hyphen_in_variable_id",
        ),
        pytest.param(
            "<activity_id>/<source_id>/<variable_id>",
            "<variable_id>_<source_id>[_<time_range>].nc",
            (
                Path("input4MIPs")
                / "CR-CMIP-1-0-0"
                / "co2_em_anthro"
                / "co2-em-anthro_CR-CMIP-1-0-0_2015-2020.nc"
            ),
            {
                "activity_id": "input4MIPs",
                "variable_id": "co2_em_anthro",
                "source_id": "CR-CMIP-1-0-0",
                "time_range": "2015-2020",
                "frequency": "yr",
                "molecular_weight": 45.3,
                "age": 83,
            },
            [cftime.datetime(y, 7, 1) for y in range(2015, 2020 + 1)],
            does_not_raise(),
            id="non_string_global_attributes",
        ),
    ),
)
def test_validate_file_written_according_to_drs(  # noqa: PLR0913
    directory_path_template,
    filename_template,
    fullpath,
    global_attributes,
    time_axis,
    exp_raise,
    tmpdir,
):
    tmp_out = Path(tmpdir) / fullpath
    tmp_out.parent.mkdir(exist_ok=False, parents=True)

    data = np.random.default_rng().random(len(time_axis))
    ds = xr.DataArray(
        data,
        dims=("time",),
        coords={"time": time_axis},
        name=global_attributes["variable_id"],
        attrs=global_attributes,
    ).to_dataset(promote_attrs=True)

    ds.to_netcdf(tmp_out)

    drs = DataReferenceSyntax(
        directory_path_template=directory_path_template,
        directory_path_example="not_used",
        filename_template=filename_template,
        filename_example="not_used",
    )

    with exp_raise:
        drs.validate_file_written_according_to_drs(file=tmp_out)
