"""
Command-line interface
"""
# TODO: check this
# Have to import everything in here so that the app registers
# that it has other commands.
from input4mips_validation.cli.root import app  # noqa: F401
from input4mips_validation.cli.validate_file import validate_file_command  # noqa: F401
