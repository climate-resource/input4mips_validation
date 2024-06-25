"""
Validation of input4MIPs data (checking file formats, metadata etc.).

This package also contains tools for creating valid input4MIPs data
(e.g. inference based on the controlled vocabularies (CVs)).

Finally, it also currently contains tools for working with the CMIP CVs.
These may be moved in future.
"""
import importlib.metadata

__version__ = importlib.metadata.version("input4mips_validation")
