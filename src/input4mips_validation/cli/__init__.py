"""
Command-line interface
"""
# Have to import everything in here so that the root_cli registers
# that it has other commands.
from input4mips_validation.cli.root import root_cli  # noqa: F401
from input4mips_validation.cli.validate_file import validate_file_command  # noqa: F401
