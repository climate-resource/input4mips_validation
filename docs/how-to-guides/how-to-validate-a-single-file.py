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
# # How to validate a single file
#
# Here we document how to validate a single file with input4MIPs validation.
# This is the second step in preparing files
# for submission to the input4MIPs collection
# and, ultimately, publication in the ESGF index.
# This document assumes that you already have a file you want to submit.
# If you want to create the file from scratch,
# check out ["How to write a single valid file"](../how-to-write-a-single-valid-file).
#
# **Note:** Before you submit your files,
# there are a few other steps you need to do too.
# See the [instructions for data producers in the input4MIPs CVS repository](https://github.com/PCMDI/input4MIPs_CVs#as-a-data-producer).
# Don't forget to do those steps at some point too.

# %% editable=true slideshow={"slide_type": ""}
import tempfile
from pathlib import Path

import iris
import ncdata.iris_xarray
import xarray as xr

# %% editable=true slideshow={"slide_type": ""}
# Some iris config they recommend
iris.FUTURE.save_split_attrs = True

# %% editable=true slideshow={"slide_type": ""}
starting_file = Path(
    "CH4-em-biomassburning_input4MIPs_emissions_CMIP_CR-CMIP-0-2-0_gn_200001-201012.nc"
)

# %% editable=true slideshow={"slide_type": ""} tags=["remove_input"]
# Some trickery to make sure we pick up files in the right path,
# even when building the docs :)
if not starting_file.exists():
    starting_file = Path("docs") / "how-to-guides" / starting_file
    if not starting_file.exists():
        raise AssertionError

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Starting point
#
# We assume that you are starting from an existing file.
# We have prepared one for this demo.
#
# A word of advice here: start with the smallest file you possibly can.
# Get that passing validation first.
# Using a file with only a few years with data is a good approach,
# because this ensures that your grid information stays relevant
# and the time handling scales very easily to longer time axes
# (having said that, for particularly high resolution data,
# you may want to start with a coarser grid too).
# Once you've got your small/test files passing,
# then move onto validating your full data files.
# Applying the pattern to your full files is pretty straight forward,
# but figuring it out in the first place can be a bit fiddly,
# so you want the iteration time to be as short as possible.
# As bigger files are much slower to work with,
# your iteration time becomes much longer,
# which makes the whole process feel
# much more painful than it needs to.

# %% editable=true slideshow={"slide_type": ""}
start = xr.open_dataset(starting_file)
start.data_vars

# %% editable=true slideshow={"slide_type": ""}
start_iris = iris.load(starting_file)
start_iris

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Validate the file
#
# As a first step, run the file through our validation.
# Below, we use our [command-line interface](https://input4mips-validation.readthedocs.io/en/latest/cli/).
# There is also a [Python API](https://input4mips-validation.readthedocs.io/en/latest/api/input4mips_validation/Validation/#input4mips_validation.validation.validate_file),
# in case you want to do this directly from Python
# (note, the logging is setup slightly differently in the Python API
# so the default shown messages are different,
# but the behaviour is the same and you can always adjust the logging
# to suit your own preferences).

# %%
# The full docs of this command can be accessed with
# # !input4mips-validation validate-file --help
# !input4mips-validation validate-file --cv-source "gh:main" {starting_file}

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Getting more detail
#
# In this case, our file has failed validation.
# We can see that the only check which failed was the check with the cf-checker.
# To find out exactly why this failed,
# we can re-run the validation with a more detailed log level.
#
# **Note:** This produces **a lot** more output.

# %% editable=true slideshow={"slide_type": ""}
# !input4mips-validation --log-level "DEBUG" \
#     validate-file --cv-source "gh:main" {starting_file}

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ### Understanding the issue
#
# From the above we can see three issues:
#
# - the "external_variables" attribute is formatted incorrectly
# - the "standard_name" assigned to the variable doesn't exist
# - the "cell_measures" variable appears to be missing
#
# We will go through what these mean in the next paragraph.
# However, in general, there can be quite some mystery surrounding these errors.
# If something doesn't make sense, please
# [make an issue](https://github.com/climate-resource/input4mips_validation/issues/new)
# and tag "@znichollscr" and "@durack1" so we can help you.
# Please don't spend lots of time banging your head against a wall.
#
# In this particular case, the errors are the following:
#
# - the supplied value of "external_variables" is "gridcellarea,sources".
#   This is meant to be a set of whitespace separated values,
#   i.e. "gridcellarea sources".
#   The CF-checker error code, 2.6.3, can help us find the
#   [right part of the CF conventions docs](https://cfconventions.org/Data/cf-conventions/cf-conventions-1.11/cf-conventions.html#external-variables),
#   although you would be forgiven for not finding them completely obvious.
#   This is an easy fix, which we perform below
# - the standard_name assigned to the variable does not exist in the
#   [list of CF standard names](https://cfconventions.org/Data/cf-standard-names/current/build/cf-standard-name-table.html).
#   We're not sure where this is documented,
#   but the fix here is to simply use "long_name" instead of "standard_name"
#   for any variables which aren't in the CF standard name table.
# - because "external_variables" isn't formatted correctly,
#   the CF-checker gets confused and things
#   that cell_measures refers to variables which aren't properly documented.
#   As we will see, fixing the issue with "external_variables" will also fix this issue.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Fixing the file
#
# In this case, the fixes are relatively trivial.
# You could do them with any tool you like.
# Here, we do them with a combination of
# [xarray](https://docs.xarray.dev/en/stable/),
# [ncdata](https://ncdata.readthedocs.io/en/latest/index.html)
# and [iris](https://scitools-iris.readthedocs.io/en/latest/index.html).
# We use this combination because we find xarray easiest to work with,
# but only iris writes the files correctly,
# and ncdata is the best to translate between the two
# (yes, you can imagine how fun it was figuring all of this out).

# %% editable=true slideshow={"slide_type": ""}
fixed = xr.open_dataset(starting_file)
# Fix the whitespace issue in external_variables
fixed.attrs["external_variables"] = fixed.attrs["external_variables"].replace(",", " ")
# Convert long_name to standard_name
# (iris would actually do this for us, but for completeness...)
fixed["CH4"].attrs["long_name"] = fixed["CH4"].attrs.pop("standard_name")

# The eagle eyed will notice that this file name is definitely not correct.
# We will soon show you why this doesn't matter in this particular case.
TMP_DIR = Path(tempfile.mkdtemp())
fixed_file = (
    TMP_DIR
    / "fixed_CH4-em-biomassburning_input4MIPs_emissions_CMIP_CR-CMIP-0-2-0_gn_200001-201012.nc"  # noqa: E501
)

cubes = ncdata.iris_xarray.cubes_from_xarray(fixed)
iris.save(cubes, fixed_file)

# Check the updated attributes, could also be done with e.g. ncdump
print(f"New external_variables: {fixed.attrs['external_variables']!r}")
print(f"New variable attributes: {fixed['CH4'].attrs!r}")

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Validate again
#
# To make sure we have actually fixed the issues, let's run the validation again.

# %% editable=true slideshow={"slide_type": ""}
# !input4mips-validation validate-file --cv-source "gh:main" {fixed_file}

# %% [markdown] editable=true slideshow={"slide_type": ""}
# Now the file passes all of the validation.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Next steps
#
# This procedure can obviously be repeated over a number of files with loops etc.
# We currently don't have a tool that repeats this procedure over numerous files,
# but are happy to receive requests for one in
# [our issues](https://github.com/climate-resource/input4mips_validation/issues/new?assignees=&labels=feature&projects=&template=feature_request.md&title=).
# Having said that, if you've got this far,
# we assume you can write a loop in Python or bash :)
#
# Once you have written your files, you have two options for what to do next:
#
# 1. If you want to really understand how your data is handled,
#    you can write it according to the input4MIPs data reference syntax (DRS).
#    If you want to go this path, please see
#    ["How to write a file in the DRS"](../how-to-write-a-single-file-in-the-drs).
# 1. If you just want to get your data in the publishing queue,
#    you can upload it as is to LLNL's FTP server.
#    If you want to go this path, please see [TODO: cross-ref]
