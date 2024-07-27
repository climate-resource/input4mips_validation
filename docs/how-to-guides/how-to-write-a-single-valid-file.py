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
import tempfile
from pathlib import Path

import cftime
import numpy as np
import xarray as xr
from loguru import logger

from input4mips_validation.cvs.loading import load_cvs
from input4mips_validation.cvs.loading_raw import get_raw_cvs_loader
from input4mips_validation.dataset import Input4MIPsDataset
from input4mips_validation.dataset.metadata_data_producer_minimum import (
    Input4MIPsDatasetMetadataDataProducerMinimum,
)

# %% editable=true slideshow={"slide_type": ""}
# For this demonstration, disable the logger
logger.disable("input4mips_validation")

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
ds.coords

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
# The last thing to set up is the CVs.
# You can pick different sources for the CVs.
# For example, you can load the CVs from local files,
# or from the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)
# (or any other web source).
#
# In this example, we're going to use a specific commit
# from the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)
# to avoid anything breaking, even if we make
# further changes to the CVs.
# For your own work, you will probably want to use either:
#
# 1. local files
# 2. the branch where you have added your information to the CVs
# 3. a tagged version of the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)
# 4. the main branch of the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)

# %% editable=true slideshow={"slide_type": ""}
# The object which can load our raw CVs files
raw_cvs_loader = get_raw_cvs_loader(
    "https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/52841b0117474efd2705a083c21b3760531974f3/CVs/"
)

# # Other examples
# Load from local files
# raw_cvs_loader = get_raw_cvs_loader("/path/to/local/input4MIPs_CVs/CVs")
# Load from git branch
# branch_name = ""
# raw_cvs_loader = get_raw_cvs_loader(f"https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/{branch_name}/CVs/")
# Load from tagged version
# version_tag = ""
# raw_cvs_loader = get_raw_cvs_loader(f"https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/{version_tag}/CVs/")
# Load from input4MIPs CVs main
# raw_cvs_loader = get_raw_cvs_loader("https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main/CVs/")
raw_cvs_loader

# %% editable=true slideshow={"slide_type": ""}
cvs = load_cvs(raw_cvs_loader)
cvs.source_id_entries.source_ids

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Putting it together
#
# With the data and metadata,
# we can now create a valid `Input4MIPsDataset` object.

# %% editable=true slideshow={"slide_type": ""}
input4mips_ds = Input4MIPsDataset.from_data_producer_minimum_information(
    data=ds,
    metadata_minimum=metadata_minimum,
    cvs=cvs,
    # We recommend using the two arguments below as well.
    # There is some rudimentary support guessing their values
    # based on the variable, but you are much more likely
    # to avoid errors if you don't rely on this
    dataset_category="SSTsAndSeaIce",
    realm="seaIce",
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

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Writing our file
#
# The last thing to do is write the file.
# This can be done with the `write` method.
# The key piece of information that you have to supply
# is the root directory in which to write the file.
# The rest of the path to the file is then auto-generated
# based on the data reference syntax (DRS) defined by the CVs.
# Below, we write the file to a temporary directory.
# You would obviously pick a more sensible location.

# %% editable=true slideshow={"slide_type": ""}
print(f"{cvs.DRS.directory_path_template=}")
print(f"{cvs.DRS.filename_template=}")

# %% editable=true slideshow={"slide_type": ""}
written_file = input4mips_ds.write(Path(tempfile.mkdtemp()))
print(f"The file was written in {written_file}")

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Next steps
#
# This procedure can obviously be repeated to write multiple files.
#
# If you have written your files with input4MIPs validation,
# we recommend the following next steps:
#
# 1. Double check that your file(s) passes validation,
#    see ["How to validate a single file"](../how-to-validate-a-single-file).
# 1. (You can skip
#    ["How to write a file in the DRS"](../how-to-write-a-single-file-in-the-drs)
#    because your file is already written in the DRS.)
# 1. Upload the file(s) to LLNL's FTP server,
#    please see [TODO: cross-ref].
