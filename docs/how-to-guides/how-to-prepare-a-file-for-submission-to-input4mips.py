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
# # How to prepare a file for submission to input4MIPs
#
# Here we document how to prepare a file for submission to the input4MIPs collection
# and publication in the ESGF index.
# This document assumes that you already have a file you want to submit.
# If you want to create the file from scratch,
# check out [TODO: cross reference once we have made the notebook].
#
# **Note:** Before you submit your files,
# there are a few other steps you need to do too.
# See the [instructions for data producers in the input4MIPs CVS repository](https://github.com/PCMDI/input4MIPs_CVs#as-a-data-producer).
# Don't forget to do those steps at some point too.
#
# **Second note:** This tool is still under active development.
# It is very likely that files that pass now may not in future,
# as we tighten the checks.
# This may be annoying, as files have to be re-written,
# but having clean data makes a massive difference to users
# so we hope you can appreciate the importance of this
# (and we hope to get the importance recognised at some point in the future too,
# watch this space).

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

# %% [markdown]
# ### Getting more detail
#
# In this case, our file has failed validation.
# We can see that the only check which failed was the check with the cf-checker.
# To find out exactly why this failed,
# we can re-run the validation with a more detailed log level.
# **Note:** This produces **a lot** more output.

# %%
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
# - the supplied value of "external_variables" is "areacello,sources".
#   This is meant to be a set of whitespace separated values, i.e. "areacello sources".
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
# ## Write the file in the data reference syntax (DRS)
#
# The file is currently just a single file.
# However, for input4MIPs,
# it is best if we receive the file in a specific directory structure,
# with a specific file name.
# Input4MIPs validation will do this for you too, as shown below.

# %%
tree_to_write_in = (
    TMP_DIR
    / "how-to-prepare-a-file-for-submission-to-input4mips-example-input4mips-ready-data"
)
# !input4mips-validation \
#     validate-file --cv-source "gh:main" {fixed_file} --write-in-drs {tree_to_write_in}

# %% [markdown]
# As the log output shows,
# the file is re-written with a full file path that matches the DRS.
# This file is then ready for submission to input4MIPs.

# %% [markdown]
# If it is of interest, we show some of the file's attributes below.

# %%
written_file = list(Path(tree_to_write_in).rglob("*.nc"))
if len(written_file) != 1:
    raise AssertionError

written_file = written_file[0]
print(f"The file's name according to the DRS is {written_file.name}")
print(
    "The file's path according to the DRS is "
    f"{written_file.parent.relative_to(tree_to_write_in)}"
)

# %%
rewritten = xr.open_dataset(written_file)
rewritten

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Creating a complete dataset and uploading to LLNL
#
# This procedure can obviously be repeated over a number of files with loops etc.
# We currently don't have a tool that repeats this procedure over numerous files,
# but are happy to receive requests for one in
# [our issues](https://github.com/climate-resource/input4mips_validation).
# Having said that, if you've got this far,
# we assume you can write a loop in Python or bash :)
#
# Once you have written your files,
# you can upload them to LLNL's ftp server using our upload FTP command, docs to come.
