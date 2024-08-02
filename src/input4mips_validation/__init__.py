"""
Validation of input4MIPs data (checking file formats, metadata etc.).
"""

import importlib.metadata

from loguru import logger

logger.disable("input4mips_validation")

__version__ = importlib.metadata.version("input4mips_validation")
