"""
Data reference syntax data model
"""

from __future__ import annotations

import json

from attrs import define
from typing_extensions import TypeAlias

from input4mips_validation.cvs.loading_raw import RawCVLoader
from input4mips_validation.serialisation import converter_json

DATA_REFERENCE_SYNTAX_FILENAME: str = "input4MIPs_DRS.json"
"""Default name of the file in which the data reference syntax is saved"""

DataReferenceSyntaxUnstructured: TypeAlias = dict[str, str]
"""Form into which the DRS is serialised for the CVs"""


@define
class DataReferenceSyntax:
    """
    Data reference syntax definition

    This defines how directories and filepaths should be created
    """

    directory_path_template: str
    """Template for creating directories"""

    directory_path_example: str
    """Example of a complete directory path"""

    filename_template: str
    """Template for creating filenames"""

    filename_example: str
    """Example of a complete filename"""


# required parts of path
# - template
#   - e.g. <variable_id>
# - replacement (a string that can be called with .format(required_metadata))
#   - e.g. {variable_id}
#   - if required metadata isn't there, raise an error
# optional parts of path
# - template
#   - e.g. [_<time_range>]
# - replacement (a string that can be called with .format(required_metadata))
#   - e.g. _{time_range}
#   - if required metadata isn't there, just delete the template string

# parse the path to get the replacements
#   cache this using functools for speed
# then apply the replacements


# keep all the checks about characters etc. from prototype branch
# using pathlib should mean we don't need to worry about separators etc.


def convert_unstructured_cv_to_drs(
    unstructured: DataReferenceSyntaxUnstructured,
) -> DataReferenceSyntax:
    """
    Convert the raw CV data to its structured form

    Parameters
    ----------
    unstructured
        Unstructured CV data

    Returns
    -------
        Data reference syntax
    """
    return converter_json.structure(unstructured, DataReferenceSyntax)


def convert_drs_to_unstructured_cv(
    drs: DataReferenceSyntax,
) -> DataReferenceSyntaxUnstructured:
    """
    Convert the data reference syntax (DRS) to the raw CV form

    Parameters
    ----------
    drs
        DRS

    Returns
    -------
        Raw CV data
    """
    raw_cv_form = converter_json.unstructure(drs)

    return raw_cv_form


def load_drs(
    raw_cvs_loader: RawCVLoader,
    filename: str = DATA_REFERENCE_SYNTAX_FILENAME,
) -> DataReferenceSyntax:
    """
    Load the DRS in the CVs

    Parameters
    ----------
    raw_cvs_loader
        Loader of raw CVs data.

    filename
        Name of the file from which to load the CVs.

        Passed to
        [`raw_cvs_loader.load_raw`][input4mips_validation.loading_raw.RawCVLoader.load_raw].

    Returns
    -------
        Loaded DRS
    """
    return convert_unstructured_cv_to_drs(
        json.loads(raw_cvs_loader.load_raw(filename=filename))
    )
