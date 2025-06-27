# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.6
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% editable=true slideshow={"slide_type": ""}
import tempfile
from pathlib import Path

import cftime
import numpy as np
import xarray as xr
from loguru import logger

from input4mips_validation.cvs.loading import load_cvs_known_loader
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.dataset.metadata_data_producer_minimum import (
    Input4MIPsDatasetMetadataDataProducerMinimum,
)

# %% editable=true slideshow={"slide_type": ""}
# For this demonstration, disable the logger
logger.disable("input4mips_validation")

# %% editable=true slideshow={"slide_type": ""}
lon = np.arange(-165.0, 180.0, 30.0, dtype=np.float64)
lat = np.arange(-82.5, 90.0, 15.0, dtype=np.float64)
# Monthly timesteps
time = [cftime.datetime(y, m, 1) for y in range(2000, 2023 + 1) for m in range(1, 13)]
# Yearly timesteps
time = [cftime.datetime(y, 7, 1) for y in range(2000, 2023 + 1)]

rng = np.random.default_rng()
ds_data = rng.random((lon.size, lat.size, len(time)))

# %% editable=true slideshow={"slide_type": ""}
ds = xr.Dataset(
    data_vars={
        "siconc": (["lat", "lon", "time"], ds_data),
    },
    coords=dict(
        lon=("lon", lon),
        lat=("lat", lat),
        time=time,
    ),
)
ds.coords

# %% editable=true slideshow={"slide_type": ""}
ds["siconc"].attrs["standard_name"] = "sea_ice_area_fraction"

# %% editable=true slideshow={"slide_type": ""}
ds["time"].encoding = {
    "calendar": "proleptic_gregorian",
    "units": "days since 1850-01-01 00:00:00",
    # Time has to be encoded as float
    # to ensure that non-integer days etc. can be handled
    # and the CF-checker doesn't complain.
    "dtype": np.dtypes.Float32DType,
}
# If you want to reduce your file size,
# you might want to encode some co-ordinates
# at lower resolution.
ds["lat"].encoding = {"dtype": np.dtypes.Float16DType}

# %% editable=true slideshow={"slide_type": ""}
metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
    grid_label="gn",
    nominal_resolution="100 km",
    source_id="PIK-CMIP-1-0-0",
    target_mip="CMIP",
)
metadata_minimum

# %% editable=true slideshow={"slide_type": ""}
# Load CVs from specific commit from Dom's branch
root_url = "https://raw.githubusercontent.com/dompap/input4MIPs_CVs"
commit_sha = "ebd0d39"
raw_cvs_loader = get_raw_cvs_loader(f"{root_url}/{commit_sha}/CVs/")
raw_cvs_loader

# %% editable=true slideshow={"slide_type": ""}
# Note: I wouldn't do a source ID for each SSP,
# rather a source ID for each scenario.
# That will mean we end up with duplicate data,
# but ESM teams no nothing about SSPs
# so we should just give them something simple
# rather than forcing them to learn the mapping
# between e.g. vllo, vlho, l, m, ml, h
# and the relevant SSP.
cvs = load_cvs_known_loader(raw_cvs_loader)
cvs.source_id_entries.source_ids

# %%
from functools import partial

from input4mips_validation.dataset.dataset import prepare_ds_and_get_frequency
from input4mips_validation.xarray_helpers.time import add_time_bounds

# %% editable=true slideshow={"slide_type": ""}
input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
    data=ds,
    metadata_minimum=metadata_minimum,
    cvs=cvs,
    # We recommend using the two arguments below as well.
    # There is some rudimentary support guessing their values
    # based on the variable, but you are much more likely
    # to avoid errors if you don't rely on this
    dataset_category="population",
    realm="land",
    # This is where the stuff for adding yearly time bounds go.
    # If you've never seen this before, it's confusing,
    # but it's a pretty common pattern that gives us the control we want.
    # (Now that we have more users, we'd maybe consider adding a simpler API too,
    # but for now it's like this.)
    prepare_func=partial(
        prepare_ds_and_get_frequency,
        add_time_bounds=partial(
            add_time_bounds,
            monthly_time_bounds=False,
            yearly_time_bounds=True,
        ),
    ),
)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# This object holds both the data and metadata.
# For example, we can look at some of the metadata fields
# which were auto-generated from the CVs.

# %% editable=true slideshow={"slide_type": ""}
# Inferred from CVs
print(f"{input4mips_ds.metadata.contact=}")
print()
# Inferred from the data
print(f"{input4mips_ds.metadata.frequency=}")
print()
# Inferred from CVs
print(f"{input4mips_ds.metadata.source_version=}")
print()
# Inferred from the data
print(f"{input4mips_ds.metadata.variable_id=}")
print()
# Inferred from CVs
print(f"{input4mips_ds.metadata.license=}")

# %%
# If you want, you can also force override metadata like the below.
# Be a bit careful though, because you can also produce things that are just wrong this way.
# (The attrs evolve thing is weird if you haven't seen it before,
# but makes sense within the rest of the project as it avoids users mucking up metadata by accident.)
from attrs import evolve

input4mips_ds = evolve(
    input4mips_ds,
    metadata=evolve(
        input4mips_ds.metadata,
        # frequency = "mon",
        further_info_url="my/nice/url",
    ),
)

# %%
# You can then check changed values using e.g. this
input4mips_ds.metadata.further_info_url

# %% editable=true slideshow={"slide_type": ""}
print(f"{cvs.DRS.directory_path_template=}")
print(f"{cvs.DRS.filename_template=}")

# %% editable=true slideshow={"slide_type": ""}
TMP_DIR = Path(tempfile.mkdtemp())
written_file = input4mips_ds.write(TMP_DIR)
print(f"The file was written in {written_file}")

# %%
# If you want to do anything really fancy with metadata,
# my advice is to just write the file
# then update the metadata of the written file using netCDF4,
# e.g.
import netCDF4

with netCDF4.Dataset(written_file, "a") as ds:
    ds.setncattr("fancy_attribute", "My special value")

# %%
xr.load_dataset(written_file).attrs["fancy_attribute"]
