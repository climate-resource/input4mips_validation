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

# %% [markdown]
# # How to manage a database
#
# Input4MIPs validation includes the ability to create a database of file entries.
# This database captures key metadata about the files.
# In this notebook, we go through how this database management works.
#
# If you're reading this notebook, we assume that you're already familiar
# with input4MIPs validation's key concepts, e.g. its CV handling.
# If you're not, have a look at
# ["How to write a single valid file"](../how-to-write-a-single-valid-file).

# %%
import tempfile
from pathlib import Path

import netCDF4
import pint
import pint_xarray  # noqa: F401
from loguru import logger

from input4mips_validation.cvs import load_cvs
from input4mips_validation.database import (
    load_database_file_entries,
)
from input4mips_validation.testing import create_files_in_tree

# %%
logger.disable("input4mips_validation")

# %%
UR = pint.get_application_registry()
UR.define("ppb = ppm * 1000")
UR.define("ppt = ppb * 1000")

# %% [markdown]
# ## Create some files
#
# We start by adding some files, so that we have a tree of files to work with.

# %%
FILE_TREE_ROOT = Path(tempfile.mkdtemp())
FILE_TREE_ROOT

# %%
cv_version = "52841b0117474efd2705a083c21b3760531974f3"
cvs = load_cvs(
    f"https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/{cv_version}/CVs/"
)
cvs.source_id_entries.source_ids


# %%
starting_files = create_files_in_tree(
    (
        "mole_fraction_of_carbon_dioxide_in_air",
        "mole_fraction_of_methane_in_air",
    ),
    ("ppm", "ppb"),
    tree_root=FILE_TREE_ROOT,
    cvs=cvs,
)
print("To start with, these are the files in our tree: ")
for file in starting_files:
    print(f"- {file}")

# %% [markdown]
# We're going to deliberately break one of the files here,
# so you can see how validation of broken files works below too.

# %%
broken_file = starting_files[0]
ncds = netCDF4.Dataset(broken_file, "a")
# Add units to bounds variable, which isn't allowed
ncds["lat_bnds"].setncattr("units", "degrees_north")
ncds.close()

# %% [markdown]
# ## Create the database
#
# The first step is to create our database.
# Below, we use our [command-line interface](https://input4mips-validation.readthedocs.io/en/latest/cli/).
# There is also a [Python API](https://input4mips-validation.readthedocs.io/en/latest/api/input4mips_validation/database/Creation/#input4mips_validation.database.creation),
# in case you want to do this directly from Python
# (note, the logging is setup slightly differently in the Python API
# so the default shown messages are different,
# but the behaviour is the same and you can always adjust the logging
# to suit your own preferences).

# %% [markdown]
# The first step is to define where you want to create the database.
# Note, this must be a directory
# because the database is serialised as a collection of files in this directory
# (with the file's sha acting as the filename to avoid clashes).

# %%
DB_DIR_ROOT = Path(tempfile.mkdtemp()) / "example-db"
DB_DIR_ROOT

# %%
# The full docs of this command can be accessed with
# # !input4mips-validation db create --help
# !input4mips-validation db create \
#     --cv-source "gh:{cv_version}" \
#     --db-dir {DB_DIR_ROOT} \
#     {FILE_TREE_ROOT}

# %% [markdown]
# As we said, the database is serialised as a number of files, one for each file,
# with the filename being defined by the file's hash to avoid filename clashes.

# %%
list(DB_DIR_ROOT.rglob("*"))

# %% [markdown]
# The format of the database on disk is really a detail though.
# A database can be loaded trivially like below.

# %%
db = load_database_file_entries(DB_DIR_ROOT)

# %% [markdown]
# ## Validating the entries in the database
#
# When the database is created,
# all the entries are assigned a validation status of `None`.
# This signals that we have not yet tried to validate the entries.

# %%
[(f"Validation status: {v.validated_input4mips}", Path(v.filepath).name) for v in db]

# %% [markdown]
# We can go through and update the validation status using the `db validate` command.

# %%
# The full docs of this command can be accessed with
# # !input4mips-validation db validate --help
# !input4mips-validation --logging-level INFO_FILE \
#     db validate \
#     --cv-source "gh:{cv_version}" \
#     --db-dir {DB_DIR_ROOT}

# %% [markdown]
# This updates the validation status of the files in our database.
# We can see that the file that is broken failed validation,
# while the other file passed.

# %%
[
    (f"Validation status: {v.validated_input4mips}", Path(v.filepath).name)
    for v in load_database_file_entries(DB_DIR_ROOT)
]

# %% [markdown]
# ## Imagine that more files were added to our tree
#
# For example, new files were published on ESGF.
# We simulate this below by adding some more files to our file tree.

# %%
added_files = create_files_in_tree(
    (
        "mole_fraction_of_halon1211_in_air",
        "mole_fraction_of_pfc6116_in_air",
    ),
    ("ppt", "ppt"),
    tree_root=FILE_TREE_ROOT,
    cvs=cvs,
)
print("Added these files in our tree: ")
for file in added_files:
    print(f"- {file}")

# %% [markdown]
# ## Adding files to the database
#
# We can add these files to our database using `db add-tree`.
# This adds any files in a tree, which are not already in the database,
# to the database.

# %%
# The full docs of this command can be accessed with
# # !input4mips-validation db add-tree --help
# !input4mips-validation --logging-level INFO_FILE \
#     db add-tree \
#     --cv-source "gh:{cv_version}" \
#     --db-dir {DB_DIR_ROOT} \
#     {FILE_TREE_ROOT}

# %% [markdown]
# Initially, the new entries have a validation status of `None`,
# while the entries for the other files are left unchanged.

# %%
[
    (f"Validation status: {v.validated_input4mips}", Path(v.filepath).name)
    for v in load_database_file_entries(DB_DIR_ROOT)
]

# %% [markdown]
# ## Re-validate the database
#
# Now that we have added more entries to the database,
# we can also validate them.

# %%
# The full docs of this command can be accessed with
# # !input4mips-validation db validate --help
# !input4mips-validation --logging-level INFO_FILE \
#     db validate \
#     --cv-source "gh:{cv_version}" \
#     --db-dir {DB_DIR_ROOT}

# %% [markdown]
# You will see that only the entries which were not previously validated were validated.
# The validation status of the previously unvalidated files in the database
# has been updated too.

# %%
[
    (f"Validation status: {v.validated_input4mips}", Path(v.filepath).name)
    for v in load_database_file_entries(DB_DIR_ROOT)
]

# %% [markdown]
# If we try and validate again, nothing happens because the function
# realises that all the files in the database have already been validated.

# %%
# The full docs of this command can be accessed with
# # !input4mips-validation db validate --help
# !input4mips-validation --logging-level INFO_FILE \
#     db validate \
#     --cv-source "gh:{cv_version}" \
#     --db-dir {DB_DIR_ROOT}

# %% [markdown]
# If we want to re-validate all the files in our database,
# irrespective of their current validation status,
# we can use the `--force` flag.

# %%
# The full docs of this command can be accessed with
# # !input4mips-validation db validate --help
# !input4mips-validation --logging-level INFO_FILE \
#     db validate \
#     --cv-source "gh:{cv_version}" \
#     --db-dir {DB_DIR_ROOT} \
#     --force

# %% [markdown]
# ## Next steps
#
# Now that you know how to manage a database, you can manage a database of your own.
# As always, if you hit any issues, please
# [raise an issue](https://github.com/climate-resource/input4mips_validation/issues/new?assignees=&labels=bug&projects=&template=bug.md&title=).
