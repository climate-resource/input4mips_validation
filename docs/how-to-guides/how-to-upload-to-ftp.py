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
# # How to upload to an FTP server
#
# Here we document how to upload file(s) to an FTP server.
# For input4MIPs, the most common target server is LLNL's FTP server,
# but this tool should, in theory, work for any FTP server.
# This is the last step in submitting files to the input4MIPs collection
# and, ultimately, publication in the ESGF index.
# This document assumes that you already have file(s)
# that you have validated and want to upload.
# If you don't already have files, check out
# ["How to write a single valid file"](../how-to-write-a-single-valid-file).
# If you haven't validated your files, check out
# ["How to validate a single file"](../how-to-validate-a-single-file).

# %% editable=true slideshow={"slide_type": ""}
from pathlib import Path

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Starting point
#
# We assume that you are starting from existing file(s).
# For this demo, we use the files which are used for other demos.
#
# **Note:** This is just a demo, so we don't actually upload files.
# Instead we do a dry run, so you can see what would happen,
# without actually having to do the upload.

# %% editable=true slideshow={"slide_type": ""}
# Show the files that we would upload
tree_root = Path(".")
list(tree_root.rglob("*.nc"))

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Upload the files
#
# Uploading the files is quite simple.
# If you find a bug while using this tool,
# please [raise an issue](https://github.com/climate-resource/input4mips_validation/issues/new?assignees=&labels=bug&projects=&template=bug.md&title=).
#
# Below, we use our [command-line interface](https://input4mips-validation.readthedocs.io/en/latest/cli/).
# There is also a [Python API](https://input4mips-validation.readthedocs.io/en/latest/api/input4mips_validation/Validation/#input4mips_validation.upload_ftp.upload_files_p),
# in case you want to do this directly from Python
# (note, the logging is setup slightly differently in the Python API
# so the default shown messages are different,
# but the behaviour is the same and you can always adjust the logging
# to suit your own preferences).

# %% editable=true slideshow={"slide_type": ""}
# !input4mips-validation \
#     --logging-level DEBUG \
#     upload-ftp . \
#     --password "your-email-goes-here@invalid.com" \
#     --cv-source "gh:main" \
#     --ftp-dir-rel-to-root "cr-testing-11" \
#     --n-threads 10
