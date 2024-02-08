"""
Integration tests of :mod:`carpet_concentrations.input4mips`

Checks that we can produce well formatted netCDF files
"""
from pathlib import Path

import cf_xarray.units
import cftime
import numpy as np
import pint_xarray  # noqa: F401 # required to enable pint accessors
import xarray as xr

from input4mips_validation.controlled_vocabularies import (
    CREATION_DATE_REGEX,
    UUID_REGEX,
)
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.metadata import (
    Input4MIPsMetadata,
    Input4MIPsMetadataOptional,
)
from input4mips_validation.time import get_start_of_next_month

# TODO: PR into cf_xarray adding these units
# TODO: PR into cf_xarray so it is easier to handle unit registry etc.
cf_xarray.units.units.define("ppb = ppm / 1000")

RNG = np.random.default_rng()


def test_file_creation(tmpdir):
    # TODO: update this depending on which metadata we think is actually compulsory
    metadata = Input4MIPsMetadata(
        contact="contact test (test@address.com)",
        dataset_category="GHGConcentrations",
        frequency="mon",
        further_info_url="cmip6.science.unimelb.edu.au",
        grid_label="gr1-GMNHSH",
        Conventions="CF-1.6",
        activity_id="input4MIPs",
        institution="Climate Resource",
        institution_id="CR",
        mip_era="CMIP6",
        nominal_resolution="10000 km",
        realm="atmos",
        source_version="1.2.1",
        source_id="CR-1-2-1",
        source="CR 1.2.1: Test file",
        target_mip="ScenarioMIP",
        title="CR 1.2.1 test dataset for testing",
    )

    # TODO: update this depending on our approach to optional metadata and CVs
    metadata_optional = Input4MIPsMetadataOptional(
        comment="Some comment",
        data_specs_version="01.00.31",
        # Could check a) value and b) consistency with grid here if we had
        # external variables submitted at the same time...
        external_variables="areacella",
        grid=(
            "global and hemispheric means - area-averages "
            "from the original latitudinal 15-degree bands"
        ),
        history="some history info here",
        product="observations",
        references="refs",
        region="some region",
        release_year="2019",
        source_description="desc",
        source_type="satellite_blended",
        table_id="some table",
        table_info="table info",
        license="license",
    )

    time = [
        cftime.datetime(y, m, 15)
        for y in range(2010, 2015 + 1)
        for m in range(1, 12 + 1)
    ]
    lat = np.arange(-82.5, 82.5 + 1, 15)
    dimensions = ("time", "lat")

    time_ref = cftime.datetime(2010, 1, 1)
    time_bounds_exp = []
    for dt in time:
        start_ts = (cftime.datetime(dt.year, dt.month, 1) - time_ref).days
        end_ts = (get_start_of_next_month(dt.year, dt.month) - time_ref).days
        time_bounds_exp.append([start_ts, end_ts])

    time_bounds_exp = np.vstack(time_bounds_exp)

    lat_diffs = np.diff(lat) / 2
    lat_diffs = np.hstack([lat_diffs, lat_diffs[0]])
    lat_bounds_exp = np.vstack(
        [
            lat - lat_diffs,
            lat + lat_diffs,
        ]
    ).T

    bounds_exp = {
        "time": ("days since 2010-01-01", time_bounds_exp),
        "lat": ("degrees_north", lat_bounds_exp),
    }

    ds = xr.Dataset(
        {
            "windspeed": (
                dimensions,
                RNG.random(size=(len(time), len(lat))),
                {"units": "m / s"},
            ),
            "mole_fraction_of_carbon_dioxide_in_air": (
                dimensions,
                RNG.random(size=(len(time), len(lat))),
                {"units": "ppm"},
            ),
            "mole_fraction_of_methane_in_air": (
                dimensions,
                RNG.random(size=(len(time), len(lat))),
                {"units": "ppb"},
            ),
        },
        coords={
            "time": time,
            "lat": lat,
        },
    ).pint.quantify(unit_registry=cf_xarray.units.units)
    ds["time"].encoding = {
        "calendar": "standard",
        "units": "days since 2010-01-01",
    }

    for data_var in ds.data_vars:
        data_var_dataset = ds[[data_var]]
        input4mips_ds = Input4MIPsDataset.from_metadata_autoadd_bounds_to_dimensions(
            data_var_dataset,
            dimensions,
            metadata=metadata,
            metadata_optional=metadata_optional,
        )
        written = input4mips_ds.write(root_data_dir=Path(tmpdir))

        assert written.name.endswith(".nc")
        assert data_var.replace("_", "-") in written.name

        read = xr.load_dataset(written, decode_times=False)

        # Check units were written to disk following UDUNITS conventions
        raw_units = read[data_var].attrs["units"]
        udunits = f"{cf_xarray.units.units.Unit(raw_units):~cf}"
        assert raw_units == udunits

        for dim in dimensions:
            exp_units, expected_bounds = bounds_exp[dim]

            assert read[dim].attrs["units"] == exp_units
            bounds = read[read[dim].bounds]
            np.testing.assert_equal(bounds.values, expected_bounds)
            # Bounds should be written with the same info
            # as the dimension to which they apply, hence have no attributes.
            # See https://cfconventions.org/cf-conventions/cf-conventions.html
            # and https://github.com/pydata/xarray/pull/2965
            assert not bounds.attrs

        read = xr.decode_cf(read, use_cftime=True).pint.quantify(
            unit_registry=cf_xarray.units.units
        )

        xr.testing.assert_equal(read[data_var], ds[data_var])
        assert (
            CREATION_DATE_REGEX.fullmatch(read.attrs["creation_date"]).string
            == read.attrs["creation_date"]
        )
        assert (
            UUID_REGEX.fullmatch(read.attrs["tracking_id"]).string
            == read.attrs["tracking_id"]
        )
        assert read.attrs["variable_id"] == data_var
