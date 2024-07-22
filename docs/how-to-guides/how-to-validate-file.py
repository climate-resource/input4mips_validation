# %% [markdown]
# # How to validate a file

# %% [markdown]
# Coming soon

# %%

# %% [markdown]
# ## Starting point
#
# Imagine we have a file that we wish to validate.

# %%
# Create and explain test file here

# %% [markdown]
# ## Validation
#
# We can validate it using input4MIPs validation.

# %% [markdown]
# ### Command-line interface
#
# The most common way to do this is via the command-line interface (CLI).

# %%
# Print the help string using the line below
# # !input4mips-validation validate-file --help

# %%
example_file = "tmp.nc"

# %%
# !input4mips-validation validate-file ${example_file}

# %% [markdown]
# ### Python API
#
# The same thing can be achived via the Python API.

# %%
# validate_file(example_file, cv_source="TBD")
