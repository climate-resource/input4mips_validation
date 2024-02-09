"""
Integration tests of :mod:`carpet_concentrations.input4mips`

Checks that we can produce well formatted netCDF files
"""
from __future__ import annotations

from functools import partial

import cf_xarray.units
import cftime
import numpy as np
import pint_xarray  # noqa: F401 # required to enable pint accessors
import xarray as xr

import input4mips_validation.xarray_helpers
from input4mips_validation.controlled_vocabularies.constants import (
    CREATION_DATE_REGEX,
    UUID_REGEX,
)
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.metadata import (
    Input4MIPsMetadata,
    Input4MIPsMetadataOptional,
)
from input4mips_validation.time import get_start_of_next_month
from input4mips_validation.validation import assert_file_is_valid

# TODO: PR into cf_xarray adding these units
# TODO: PR into cf_xarray so it is easier to handle unit registry etc.
cf_xarray.units.units.define("ppb = ppm / 1000")

RNG = np.random.default_rng()


def test_file_creation(tmp_path):
    # TODO: update this depending on which metadata we think is actually compulsory
    metadata = Input4MIPsMetadata(
        activity_id="input4MIPs",
        contact="contact test (test@address.com)",
        mip_era="CMIP6Plus",
        target_mip="CMIP",
        institution_id="PCMDI",
        source_id="PCMDI-AMIP-1-1-9",
        # rules here make no sense to me,
        # can this be inferred from the data or only checked against it?
        grid_label="placeholder",
    )

    # TODO: update this depending on our approach to optional metadata and CVs
    metadata_optional = Input4MIPsMetadataOptional(
        comment="Some comment",
    )

    time = [
        cftime.datetime(y, m, 15)
        for y in range(2010, 2015 + 1)
        for m in range(1, 12 + 1)
    ]
    lat = np.arange(-82.5, 82.5 + 1, 15)
    dimensions = ("time", "lat")
    time_dimension = "time"

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
            "mole_fraction_of_carbon_dioxide_in_air": (
                dimensions,
                RNG.random(size=(len(time), len(lat))),
                {"units": "ppm"},
            ),
            "tos": (
                dimensions,
                RNG.random(size=(len(time), len(lat))),
                {"units": "K"},
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
        input4mips_ds = Input4MIPsDataset.from_raw_dataset(
            data_var_dataset,
            dimensions=dimensions,
            time_dimension=time_dimension,
            metadata=metadata,
            metadata_optional=metadata_optional,
            add_time_bounds=partial(
                input4mips_validation.xarray_helpers.add_time_bounds,
                monthly_time_bounds=True,
            ),
        )
        written = input4mips_ds.write(root_data_dir=tmp_path)

        # Make sure the written file passes validation
        # (The specific checks below may be moved into this validation file later.)
        assert_file_is_valid(written)

        assert written.name.endswith(".nc")
        # Check that data variable is included in the filename, except with
        # underscores replaced with hyphens to match input4MIPs conventions.
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

        # Assert the data was not mangled while writing
        xr.testing.assert_equal(read[data_var], ds[data_var])

        # Check that the creation date and UUID are there and were written correctly
        assert (
            CREATION_DATE_REGEX.fullmatch(read.attrs["creation_date"]).string
            == read.attrs["creation_date"]
        )
        assert (
            UUID_REGEX.fullmatch(read.attrs["tracking_id"]).string
            == read.attrs["tracking_id"]
        )
        assert read.attrs["variable_id"] == data_var
