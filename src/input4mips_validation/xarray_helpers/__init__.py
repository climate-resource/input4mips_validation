"""
Helpers for working with [xarray][]
"""

# Docs on cross-references for the above:
# https://mkdocstrings.github.io/usage/#cross-references-to-other-projects-inventories
from input4mips_validation.xarray_helpers.time import add_time_bounds

__all__ = [
    "add_time_bounds",
]
