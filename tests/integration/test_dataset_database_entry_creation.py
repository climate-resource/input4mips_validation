"""
Test the results of creating datasets and database entries
"""

from __future__ import annotations

from pathlib import Path

import cf_xarray  # noqa: F401 # required to activate cf accessor
import cftime
import numpy as np
import pint
import pint_xarray  # noqa: F401 # required to activate pint accessor
import pytest
import xarray as xr

from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.database import Input4MIPsDatabaseEntryFile
from input4mips_validation.dataset import (
    Input4MIPsDataset,
)
from input4mips_validation.dataset.metadata import Input4MIPsDatasetMetadata
from input4mips_validation.validation.file import get_validate_file_result
from input4mips_validation.xarray_helpers import add_time_bounds

UR = pint.get_application_registry()

DEFAULT_TEST_INPUT4MIPS_CV_SOURCE = (
    Path(__file__).parent / ".." / "test-data" / "cvs" / "default"
).absolute()


@pytest.mark.parametrize(
    "metadata_kwargs, non_input4mips_metadata",
    (
        pytest.param(
            dict(
                activity_id="input4MIPs",
                contact="zebedee.nicholls@climate-resource.com",
                dataset_category="GHGConcentrations",
                frequency="mon",
                further_info_url="www.climate-resource.com",
                grid_label="gn",
                institution="Climate Resource",
                institution_id="CR",
                license=(
                    "The input4MIPs data linked to this entry "
                    "is licensed under a "
                    "Creative Commons Attribution 4.0 International "
                    "(https://creativecommons.org/licenses/by/4.0/). "
                    "Consult https://pcmdi.llnl.gov/CMIP6/TermsOfUse "
                    "for terms of use governing CMIP6Plus output, "
                    "including citation requirements and proper acknowledgment. "
                    "The data producers and data providers make no warranty, "
                    "either express or implied, including, but not limited to, "
                    "warranties of merchantability "
                    "and fitness for a particular purpose. "
                    "All liabilities arising from the supply of the information "
                    "(including any liability arising in negligence) "
                    "are excluded to the fullest extent permitted by law."
                ),
                license_id="CC BY 4.0",
                mip_era="CMIP6Plus",
                nominal_resolution="10000km",
                realm="atmos",
                source_id="CR-CMIP-0-2-0",
                source_version="0.2.0",
                target_mip="CMIP",
                doi="doi/12981.1212",
            ),
            {"nice_field": "Someone put something in"},
            id="basic-incl-doi",
        ),
    ),
)
def test_create_dataset_database_entry(
    metadata_kwargs, non_input4mips_metadata, tmp_path
):
    cvs = load_cvs(DEFAULT_TEST_INPUT4MIPS_CV_SOURCE)

    units = "ppm"
    variable_id = "co2"
    standard_name = "mole_fraction_of_carbon_dioxide_in_air"
    lon = np.arange(-165.0, 180.0, 15.0, dtype=np.float64)
    lat = np.arange(-82.5, 90.0, 15.0, dtype=np.float64)

    rng = np.random.default_rng()
    time = [
        cftime.datetime(y, m, 1) for y in range(2000, 2010 + 1) for m in range(1, 13)
    ]

    ds_data = UR.Quantity(
        rng.random((len(time), lat.size, lon.size)),
        units,
    )
    dimensions = ["time", "lat", "lon"]
    coords = dict(
        lon=("lon", lon),
        lat=("lat", lat),
        time=time,
    )

    ds = xr.Dataset(
        data_vars={
            variable_id: (dimensions, ds_data),
        },
        coords=coords,
        attrs={},
    )
    ds["time"].encoding = {
        "calendar": "proleptic_gregorian",
        "units": "days since 1850-01-01 00:00:00",
        # Time has to be encoded as float
        # to ensure that half-days etc. are handled.
        "dtype": np.dtypes.Float32DType,
    }
    ds = add_time_bounds(ds, monthly_time_bounds=True)
    for dim in ["lat", "lon"]:
        ds = ds.cf.add_bounds(dim, output_dim="bounds")

    ds[variable_id].attrs["standard_name"] = standard_name
    ds = ds.cf.guess_coord_axis().cf.add_canonical_attributes()

    metadata = Input4MIPsDatasetMetadata(**metadata_kwargs, variable_id=variable_id)

    input4mips_ds = Input4MIPsDataset(
        data=ds,
        metadata=metadata,
        cvs=cvs,
        non_input4mips_metadata=non_input4mips_metadata,
    )

    written_file = input4mips_ds.write(root_data_dir=tmp_path)

    get_validate_file_result(written_file, cvs=cvs).raise_if_errors()

    database_entry = Input4MIPsDatabaseEntryFile.from_file(
        written_file, cvs=input4mips_ds.cvs
    )

    assert database_entry.doi == metadata.doi

    written_ds = xr.open_dataset(written_file)

    for k, v in metadata_kwargs.items():
        assert written_ds.attrs[k] == v

    for k, v in non_input4mips_metadata.items():
        assert written_ds.attrs[k] == v
