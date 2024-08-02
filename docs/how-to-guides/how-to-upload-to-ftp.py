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
tree_root = Path(".")

# %% editable=true slideshow={"slide_type": ""} tags=["remove_input"]
# Some trickery to make sure we pick up files in the right path,
# even when building the docs :)
if "docs" not in str(tree_root):
    tree_root = Path("docs") / "how-to-guides"

# %% editable=true slideshow={"slide_type": ""}
# Show the files that we would upload
list(tree_root.rglob("*.nc"))

# %% editable=true slideshow={"slide_type": ""} tags=["remove_input"]
# Some trickery to check
if not list(tree_root.rglob("*.nc")):
    msg = f"No files in path? {tree_root=}. {tree_root.rglob('*.nc')=}"
    raise AssertionError(msg)

# %% [markdown]
# ## The CVs
#
# A note before we continue.
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

# %% [markdown] editable=true slideshow={"slide_type": ""}
# ## Upload the files
#
# Uploading the files is quite simple.
# Below, we demonstrate how to do this.
# Note that we do a dry run here,
# i.e. we don't actually upload any files.
# When you are using this command,
# remove the `--dry-run` flag to actually upload the files.
#
# If you find a bug while using this tool,
# please [raise an issue](https://github.com/climate-resource/input4mips_validation/issues/new?assignees=&labels=bug&projects=&template=bug.md&title=).
#
# Below, we use our [command-line interface](https://input4mips-validation.readthedocs.io/en/latest/cli/).
# There is also a [Python API](https://input4mips-validation.readthedocs.io/en/latest/api/input4mips_validation/Validation/#input4mips_validation.upload_ftp.upload_ftp),
# in case you want to do this directly from Python
# (note, the logging is setup slightly differently in the Python API
# so the default shown messages are different,
# but the behaviour is the same and you can always adjust the logging
# to suit your own preferences).

# %% editable=true slideshow={"slide_type": ""}
# Below we do a dry run, i.e. we don't actually upload the files.
# Make sure you remove the --dry-run flag for your own uploads.
# !input4mips-validation \
#     --logging-level DEBUG \
#     upload-ftp . \
#     --password "your-email-goes-here@invalid.com" \
#     --cv-source "gh:52841b0117474efd2705a083c21b3760531974f3" \
#     --ftp-dir-rel-to-root "dir-to-upload-in-goes-here-eg-your-institute-name" \
#     --n-threads 10 \
#     --dry-run

# %% [markdown]
# ## Next steps
#
# Once you have your files, now you are ready to upload them.
# Before/during/just after you have upload the files,
# please make an issue at [PCMDI/input4MIPs_CVs](https://github.com/PCMDI/input4MIPs_CVs/issues/new)
# so we can ensure that your files are published as quickly as possible.
