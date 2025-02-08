"""
Test that we can create a file which passes our validation tests
"""

from __future__ import annotations

import datetime as dt
import os
from functools import partial
from pathlib import Path
from unittest.mock import patch

import cftime
import netCDF4
import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import xarray as xr
from typer.testing import CliRunner

from input4mips_validation.cli import app
from input4mips_validation.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.dataset import (
    Input4MIPsDataset,
    Input4MIPsDatasetMetadataDataProducerMinimum,
    Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum,
)
from input4mips_validation.dataset.dataset import (
    prepare_ds_and_get_frequency,
)
from input4mips_validation.hashing import get_file_hash_sha256
from input4mips_validation.inference.from_data import BoundsInfo
from input4mips_validation.testing import get_valid_ds_min_metadata_example
from input4mips_validation.validation.file import get_validate_file_result

UR = pint.get_application_registry()
try:
    UR.define("ppb = ppm * 1000")
except pint.errors.RedefinitionError:
    pass

runner = CliRunner()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = (
    Path(__file__).parent / ".." / ".." / "test-data" / "cvs" / "default"
).absolute()


def test_validate_written_single_variable_file(tmp_path):
    """
    Test that we can write a single variable file that passes our validate-file CLI
    """
    variable_name = "mole_fraction_of_carbon_dioxide_in_air"
    ds, metadata_minimum = get_valid_ds_min_metadata_example(variable_id=variable_name)

    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
            data=ds,
            metadata_minimum=metadata_minimum,
            prepare_func=partial(
                prepare_ds_and_get_frequency,
                standard_and_or_long_names={
                    variable_name: {"standard_name": variable_name}
                },
            ),
        )

    written_file = input4mips_ds.write(root_data_dir=tmp_path)

    # Test the function directly first (helps with debugging)
    get_validate_file_result(
        written_file,
        cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        bounds_info=BoundsInfo(
            time_bounds="time_bnds",
            bounds_dim="bnds",
        ),
    ).raise_if_errors()

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        result = runner.invoke(app, ["validate-file", str(written_file)])

    assert result.exit_code == 0, result.exc_info

    database_entry = Input4MIPsDatabaseEntryFile.from_file(
        written_file, cvs=input4mips_ds.cvs
    )

    ds_attrs = xr.open_dataset(written_file).attrs
    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    database_entry_exp = Input4MIPsDatabaseEntryFile(
        Conventions="CF-1.7",
        activity_id="input4MIPs",
        contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
        creation_date=ds_attrs["creation_date"],
        dataset_category="GHGConcentrations",
        datetime_end="2010-12-01T00:00:00Z",
        datetime_start="2000-01-01T00:00:00Z",
        esgf_dataset_master_id=f"input4MIPs.CMIP6Plus.CMIP.CR.CR-CMIP-0-2-0.atmos.mon.mole_fraction_of_carbon_dioxide_in_air.gn.v{version_exp}",
        filepath=str(written_file),
        frequency="mon",
        further_info_url="http://www.tbd.invalid",
        grid_label="gn",
        institution_id="CR",
        license=(
            "The input4MIPs data linked to this entry "
            "is licensed under a Creative Commons Attribution 4.0 International "
            "(https://creativecommons.org/licenses/by/4.0/). "
            "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
            "for terms of use governing CMIP6Plus output, "
            "including citation requirements and proper acknowledgment. "
            "The data producers and data providers make no warranty, "
            "either express or implied, including, but not limited to, "
            "warranties of merchantability and fitness for a particular purpose. "
            "All liabilities arising from the supply of the information "
            "(including any liability arising in negligence) "
            "are excluded to the fullest extent permitted by law."
        ),
        license_id="CC BY 4.0",
        mip_era="CMIP6Plus",
        nominal_resolution="10000 km",
        product=None,
        realm="atmos",
        region=None,
        sha256=get_file_hash_sha256(written_file),
        source_id="CR-CMIP-0-2-0",
        source_version="0.2.0",
        target_mip="CMIP",
        time_range="200001-201012",
        tracking_id=ds_attrs["tracking_id"],
        variable_id="mole_fraction_of_carbon_dioxide_in_air",
        version=version_exp,
        grid=None,
        institution=None,
        references=None,
        source=None,
    )

    assert database_entry == database_entry_exp


def test_validate_written_multi_variable_file(tmp_path):
    """
    Test that we can write a multi-variable file that passes our validate-file CLI
    """
    co2_dat, _ = get_valid_ds_min_metadata_example(
        variable_id="mole_fraction_of_carbon_dioxide_in_air"
    )
    ch4_dat, _ = get_valid_ds_min_metadata_example(
        variable_id="mole_fraction_of_methane_in_air", units="ppb"
    )

    ds = xr.merge([co2_dat, ch4_dat])
    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum(
        dataset_category="GHGConcentrations",
        grid_label="gn",
        nominal_resolution="10000 km",
        realm="atmos",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
    )

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        input4mips_ds = (
            Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable(
                data=ds,
                metadata_minimum=metadata_minimum,
                prepare_func=partial(
                    prepare_ds_and_get_frequency,
                    dimensions=("time", "lat", "lon"),
                    standard_and_or_long_names={
                        "mole_fraction_of_carbon_dioxide_in_air": {
                            "standard_name": "mole_fraction_of_carbon_dioxide_in_air"
                        },
                        "mole_fraction_of_methane_in_air": {
                            "standard_name": "mole_fraction_of_methane_in_air"
                        },
                    },
                ),
            )
        )

    written_file = input4mips_ds.write(root_data_dir=tmp_path)

    # Test the function directly first (helps with debugging)
    get_validate_file_result(
        written_file,
        cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
        bounds_info=BoundsInfo(
            time_bounds="time_bnds",
            bounds_dim="bnds",
        ),
    ).raise_if_errors()

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        result = runner.invoke(app, ["validate-file", str(written_file)])

    assert result.exit_code == 0, result.exc_info

    database_entry = Input4MIPsDatabaseEntryFile.from_file(
        written_file, cvs=input4mips_ds.cvs
    )

    ds_attrs = xr.open_dataset(written_file).attrs
    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    database_entry_exp = Input4MIPsDatabaseEntryFile(
        Conventions="CF-1.7",
        activity_id="input4MIPs",
        contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
        creation_date=ds_attrs["creation_date"],
        dataset_category="GHGConcentrations",
        datetime_end="2010-12-01T00:00:00Z",
        datetime_start="2000-01-01T00:00:00Z",
        esgf_dataset_master_id=f"input4MIPs.CMIP6Plus.CMIP.CR.CR-CMIP-0-2-0.atmos.mon.multiple.gn.v{version_exp}",
        filepath=str(written_file),
        frequency="mon",
        further_info_url="http://www.tbd.invalid",
        grid_label="gn",
        institution_id="CR",
        license=(
            "The input4MIPs data linked to this entry "
            "is licensed under a Creative Commons Attribution 4.0 International "
            "(https://creativecommons.org/licenses/by/4.0/). "
            "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
            "for terms of use governing CMIP6Plus output, "
            "including citation requirements and proper acknowledgment. "
            "The data producers and data providers make no warranty, "
            "either express or implied, including, but not limited to, "
            "warranties of merchantability and fitness for a particular purpose. "
            "All liabilities arising from the supply of the information "
            "(including any liability arising in negligence) "
            "are excluded to the fullest extent permitted by law."
        ),
        license_id="CC BY 4.0",
        mip_era="CMIP6Plus",
        nominal_resolution="10000 km",
        product=None,
        realm="atmos",
        region=None,
        sha256=get_file_hash_sha256(written_file),
        source_id="CR-CMIP-0-2-0",
        source_version="0.2.0",
        target_mip="CMIP",
        time_range="200001-201012",
        tracking_id=ds_attrs["tracking_id"],
        variable_id="multiple",
        version=version_exp,
        grid=None,
        institution=None,
        references=None,
        source=None,
    )

    assert database_entry == database_entry_exp


def test_validate_written_region_file(tmp_path):
    """
    Test that we can write a file with region information

    The file should pass our validate-file CLI
    """
    metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
        grid_label="gn",
        nominal_resolution="250 km",
        source_id="CR-CMIP-0-2-0",
        target_mip="CMIP",
    )
    regions = ["africa", "red_sea"]
    region_max_len = max(len(v) for v in regions)
    time = [
        cftime.datetime(y, m, 1) for y in range(2000, 2010 + 1) for m in range(1, 13)
    ]

    rng = np.random.default_rng()
    data = rng.random((len(time), len(regions)))
    units = "K"

    data_xr = xr.DataArray(
        data,
        dims=["time", "lbl"],
        coords=dict(time=time),
        attrs={"standard_name": "air_temperature", "unit": units},
    )
    # Hmm creating this in xarray just doesn't really work.
    # # This causes issues with how things are written.
    # # x-ref: https://github.com/pp-mo/ncdata/issues/111
    # regions_char_array = netCDF4.stringtochar(
    #     np.array(regions, dtype=f"S{region_max_len}")
    # )
    # regions_xr = xr.DataArray(
    #     regions_char_array,
    #     dims=["lbl", "strlen"],
    #     attrs={"standard_name": "region"},
    # )
    # # This fails because of the below
    # # x-ref: https://github.com/pp-mo/ncdata/issues/111
    # regions_xr = xr.DataArray(
    #     regions,
    #     dims=["lbl"],
    #     attrs={"standard_name": "region"},
    # )

    ds = xr.Dataset(
        data_vars=dict(
            air_temperature=data_xr,
            # Added by hand below.
            # region=regions_xr,
        ),
    )

    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }

    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
            data=ds,
            metadata_minimum=metadata_minimum,
            dataset_category="Temperature",
            realm="atmos",
            # prepare_func=partial(
            #     prepare_ds_and_get_frequency,
            #     # TODO: remove this and make sure it still works
            #     dimensions=("time",),
            # ),
        )

    written_file = input4mips_ds.write(root_data_dir=tmp_path)
    # Add in region by hand
    with netCDF4.Dataset(written_file, "a") as ds:
        ds.createDimension("strlen", region_max_len)
        ds.createVariable("region", "S1", ("dim1", "strlen"))
        ds["region"][:] = netCDF4.stringtochar(
            np.array(regions, dtype=f"S{region_max_len}")
        )
        ds["region"].setncattr("standard_name", "region")

    # Test the function directly first (helps with debugging)
    get_validate_file_result(
        written_file,
        cv_source=DEFAULT_TEST_INPUT4MIPS_CV_SOURCE,
    ).raise_if_errors()

    # Then test the CLI
    with patch.dict(
        os.environ,
        {"INPUT4MIPS_VALIDATION_CV_SOURCE": str(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)},
    ):
        result = runner.invoke(app, ["validate-file", str(written_file)])

    assert result.exit_code == 0, result.exc_info

    database_entry = Input4MIPsDatabaseEntryFile.from_file(
        written_file, cvs=input4mips_ds.cvs
    )

    ds_attrs = xr.open_dataset(written_file).attrs
    # If this gets run just at the turn of midnight, this may fail.
    # That is a risk I am willing to take.
    version_exp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    database_entry_exp = Input4MIPsDatabaseEntryFile(
        Conventions="CF-1.7",
        activity_id="input4MIPs",
        contact="zebedee.nicholls@climate-resource.com;malte.meinshausen@climate-resource.com",
        creation_date=ds_attrs["creation_date"],
        dataset_category="Temperature",
        datetime_end="2010-12-01T00:00:00Z",
        datetime_start="2000-01-01T00:00:00Z",
        esgf_dataset_master_id=f"input4MIPs.CMIP6Plus.CMIP.CR.CR-CMIP-0-2-0.atmos.mon.air_temperature.gn.v{version_exp}",
        filepath=str(written_file),
        frequency="mon",
        further_info_url="http://www.tbd.invalid",
        grid_label="gn",
        institution_id="CR",
        license=(
            "The input4MIPs data linked to this entry "
            "is licensed under a Creative Commons Attribution 4.0 International "
            "(https://creativecommons.org/licenses/by/4.0/). "
            "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
            "for terms of use governing CMIP6Plus output, "
            "including citation requirements and proper acknowledgment. "
            "The data producers and data providers make no warranty, "
            "either express or implied, including, but not limited to, "
            "warranties of merchantability and fitness for a particular purpose. "
            "All liabilities arising from the supply of the information "
            "(including any liability arising in negligence) "
            "are excluded to the fullest extent permitted by law."
        ),
        license_id="CC BY 4.0",
        mip_era="CMIP6Plus",
        nominal_resolution="250 km",
        product=None,
        realm="atmos",
        region=None,
        sha256=get_file_hash_sha256(written_file),
        source_id="CR-CMIP-0-2-0",
        source_version="0.2.0",
        target_mip="CMIP",
        time_range="200001-201012",
        tracking_id=ds_attrs["tracking_id"],
        variable_id="air_temperature",
        version=version_exp,
        grid=None,
        institution=None,
        references=None,
        source=None,
    )

    assert database_entry == database_entry_exp
