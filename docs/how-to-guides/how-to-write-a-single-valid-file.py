# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.16.3
#   kernelspec:
#     display_name: Python 3 (ipykernel)
#     language: python
#     name: python3
# ---

# %% [markdown] editable=true slideshow={"slide_type": ""}
# # How to write a single valid file
#
# Here we document how to write a single, valid file with input4MIPs validation.
# This is the first step in preparing files
# for submission to the input4MIPs collection
# and, ultimately, publication in the ESGF index.
# This document assumes that you don't already have a file you want to submit.
# If you already have files, you can skip straight to
# ["How to validate a single file"](../how-to-validate-a-single-file).
#
# **Note:** Before you submit your files,
# there are a few other steps you need to do too.
# See the [instructions for data producers in the input4MIPs CVS repository](https://github.com/PCMDI/input4MIPs_CVs#as-a-data-producer).
# Don't forget to do those steps at some point too.

# %% editable=true slideshow={"slide_type": ""}
import cftime
import numpy as np
import xarray as xr

from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.dataset.metadata_data_producer_minimum import (
    Input4MIPsDatasetMetadataDataProducerMinimum,
)

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Creating our file
#
# Here we are going to go through a basic example
# of how we can create a valid data file.
# This is a very basic example.
# If it doesn't fit your case,
# please [raise an issue](https://github.com/climate-resource/input4mips_validation/issues/new?assignees=&labels=triage&projects=&template=default.md&title=File%20creation%20help).
# and we can see if we can add docs which fit your use case too.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# In the below, we use [xarray](https://docs.xarray.dev/en/stable/)
# because we find it easiest to use.
# However, under the hood we are also using
# [ncdata](https://ncdata.readthedocs.io/en/latest/index.html)
# and [iris](https://scitools-iris.readthedocs.io/en/latest/index.html).
# We use this combination because,
# while we find xarray easiest to work with,
# only iris writes the files correctly,
# and ncdata is the best to translate between the two
# (yes, you can imagine how fun it was figuring all of this out).
#
# Ultimately, the choice of library is up to you.
# The simplest path (in our opinion) is below,
# but as long as your file passes validation,
# we don't mind how you created it.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## The data
#
# Let's imagine you have some data on a lat, lon, time grid.

# %% editable=true slideshow={"slide_type": ""}
lon = np.arange(-165.0, 180.0, 30.0, dtype=np.float64)
lat = np.arange(-82.5, 90.0, 15.0, dtype=np.float64)
time = [cftime.datetime(y, m, 1) for y in range(2000, 2023 + 1) for m in range(1, 13)]

rng = np.random.default_rng()
ds_data = rng.random((lon.size, lat.size, len(time)))

# %% [markdown] editable=true slideshow={"slide_type": ""}
# We can put this into an xarray object.

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
ds

# %% [markdown] editable=true slideshow={"slide_type": ""}
# In order to ensure that your data passes validation,
# you also have to specify either the "standard_name" of your variable
# (if there is a standard name for your variable
# in [the official list](https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html))
# or the "long_name" attribute of your variable
# (you can specify both if you want, but you must have at least one).
# In this case, the variable is in the official list so we will set "standard_name".

# %% editable=true slideshow={"slide_type": ""}
ds["siconc"].attrs["standard_name"] = "sea_ice_area_fraction"

# %% [markdown] editable=true slideshow={"slide_type": ""}
# You don't have to do the step below, but we recommend it.
# Specifying encodings ensures that your data is written to disk as intended.

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

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### The metadata

# %% [markdown] editable=true slideshow={"slide_type": ""}
# Assuming that you have already registered in the
# [controlled vocabularies (CVs)](https://github.com/PCMDI/input4MIPs_CVs),
# creating a valid dataset is very straightforward.
# The key information is your source ID,
# from which lots of other information can be inferred.
# The rest of the metadata can be inferred from the data.

# %% editable=true slideshow={"slide_type": ""}
metadata_minimum = Input4MIPsDatasetMetadataDataProducerMinimum(
    grid_label="gn",
    nominal_resolution="10000 km",
    source_id="CR-CMIP-0-2-0",
    target_mip="CMIP",
)
metadata_minimum

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### The CVs
#
# - point to the right version of the CVs
# - can be local or on GitHub
# - load here
# - then use in next step

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Putting it together
#
# With the data and metadata,
# we can now create a valid `Input4MIPsDataset` object.

# %% editable=true slideshow={"slide_type": ""}
input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
    data=ds,
    metadata_minimum=metadata_minimum,
)


# %% [markdown] editable=true slideshow={"slide_type": ""}
# - file gets written in DRS, so do validation but you can skip write in DRS and go straight to upload

# %% editable=true slideshow={"slide_type": ""}
