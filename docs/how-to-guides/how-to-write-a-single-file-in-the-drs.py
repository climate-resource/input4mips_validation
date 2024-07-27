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
# # How to write a single file according to the data reference syntax (DRS)
#
# Here we document how to write a single file according to the input4MIPs DRS.
# This is an optional step in preparing files
# for submission to the input4MIPs collection
# and, ultimately, publication in the ESGF index.
# If you don't do it, the ESGF publishers will.
# However, doing it yourself means
# that you understand how your data is treated
# and have a copy of the file which is ultimately published to the ESGF.
# This document assumes that you already have a file that passes validation.
# If you don't have that yet,
# check out ["How to validate a single file"](../how-to-validate-a-single-file).
#
# **Note:** Before you write your files according to the DRS,
# there are a few other steps you need to do too.
# See the [instructions for data producers in the input4MIPs CVS repository](https://github.com/PCMDI/input4MIPs_CVs#as-a-data-producer).
# Don't forget to do those steps at some point too.

# %%
import tempfile
from pathlib import Path

import iris
import xarray as xr

# %% editable=true slideshow={"slide_type": ""}
starting_file = Path(
    "fixed_CH4-em-biomassburning_input4MIPs_emissions_CMIP_CR-CMIP-0-2-0_gn_200001-201012.nc"
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
# We assume that you are starting from an existing file,
# which can pass validation.
# If you don't have that yet,
# check out ["How to validate a single file"](../how-to-validate-a-single-file).

# %% editable=true slideshow={"slide_type": ""}
start = xr.open_dataset(starting_file)
start.data_vars

# %% editable=true slideshow={"slide_type": ""}
start_iris = iris.load(starting_file)
start_iris

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Write the file in the DRS
#
# Writing the file in the DRS is very similar to validating a file.
# We simply add the `--write-in-drs` option to our `validate-file`
# call, then the file is automatically written in the DRS for us.
#
# Below, we use our [command-line interface](https://input4mips-validation.readthedocs.io/en/latest/cli/).
# There is also a [Python API](https://input4mips-validation.readthedocs.io/en/latest/api/input4mips_validation/Validation/#input4mips_validation.validation.validate_file),
# in case you want to do this directly from Python
# (note, the logging is setup slightly differently in the Python API
# so the default shown messages are different,
# but the behaviour is the same and you can always adjust the logging
# to suit your own preferences).
#
# ### The CVs
#
# In the below, you will notice that there is an option, `--cv-source`.
# This points to the source of the controlled vocabularies (CVs).
# You can pick different sources for the CVs.
# For example, you can load the CVs from local files,
# or from the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)
# (or any other web source).
#
# In this example, we're going to use a specific commit
# from the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)
# to avoid anything breaking, even if we make further changes to the CVs.
# For your own work, you will probably want to use either:
#
# 1. local files, e.g. `--cv-source path/to/local/files`
# 1. the branch where you have added your information to the CVs,
#    `--cv-source https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/branch_name/CVs/`
# 1. a tagged version of the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)
#    `--cv-source gh:tag-id`
# 1. the main branch of the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs)
#    `--cv-source gh:main`
# 1. a specific commit in the [input4MIPs CVs GitHub](https://github.com/PCMDI/input4MIPs_CVs),
#    like we do below, `--cv-source gh:commit-hash`
#
# This is definitely not the best documented feature of the library,
# so if anything is unclear,
# please [raise an issue](https://github.com/climate-resource/input4mips_validation/issues/new?assignees=&labels=triage&projects=&template=default.md&title=).

# %% editable=true slideshow={"slide_type": ""}
TMP_DIR = Path(tempfile.mkdtemp())
tree_to_write_in = TMP_DIR / "how-to-write-a-single-file-in-drs"
# !input4mips-validation \
#     validate-file \
#     --cv-source "gh:52841b0117474efd2705a083c21b3760531974f3" {starting_file} \
#     --write-in-drs {tree_to_write_in}

# %% [markdown] editable=true slideshow={"slide_type": ""}
# As the log output shows,
# the file is re-written with a full file path that matches the DRS.
# This file is then ready for submission to input4MIPs.

# %% [markdown] editable=true slideshow={"slide_type": ""}
# If it is of interest, we show some of the file's attributes below.

# %% editable=true slideshow={"slide_type": ""}
written_file = list(tree_to_write_in.rglob("*.nc"))
if len(written_file) != 1:
    msg = f"Found {written_file=}"
    raise AssertionError(msg)

written_file = written_file[0]
print(f"The file's name according to the DRS is {written_file.name}")
print(
    "The file's path according to the DRS is "
    f"{written_file.parent.relative_to(tree_to_write_in)}"
)

rewritten = xr.open_dataset(written_file)
print(f"The written file's tracking ID is {rewritten.attrs['tracking_id']}")
print(f"The written file's creation date is {rewritten.attrs['creation_date']}")

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
# Once you have written your files, the next step is to
# upload the files to LLNL's FTP server,
# please see [TODO: cross-ref].
