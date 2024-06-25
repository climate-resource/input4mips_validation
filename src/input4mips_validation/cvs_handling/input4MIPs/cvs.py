"""Data model for input4MIPs' controlled vocabularies (CVs)"""
from __future__ import annotations

import string
from pathlib import Path
from typing import Protocol

from attrs import define

from input4mips_validation.cvs_handling.input4MIPs.activity_id import ActivityIDEntries
from input4mips_validation.cvs_handling.input4MIPs.raw_cv_loading import RawCVLoader
from input4mips_validation.cvs_handling.input4MIPs.source_id import SourceIDEntries


class DatasetMetadataLike(Protocol):
    """Protocol for classes that hold metadata about a dataset"""

    activity_id: str

    dataset_category: str

    frequency: str

    grid_label: str

    institution_id: str

    mip_era: str

    realm: str

    source_id: str

    time_range: str

    target_mip: str

    variable_id: str

    version: str


@define
class CVsInput4MIPs:
    """
    Data model of input4MIPs' CVs
    """

    raw_loader: RawCVLoader
    """Object used to load the raw CVs"""

    activity_id_entries: ActivityIDEntries
    """Activity ID entries"""

    # dataset_categories: tuple[str, ...]
    # """Recognised dataset categories"""
    # Would make sense for this to actually be entries,
    # and to specify the variables in each category here

    # data_file_required_global_attributes: tuple[str, ...]
    # """Global attributes that must be in data files"""
    # Not sure if these can be linked back to global CVs/should somehow be split.
    # Having this seems like duplication to me...

    # data_reference_syntax: DataReferenceSyntax
    # """Data reference syntax (drs) specification"""

    # instutition_ids: tuple[str, ...]
    # """Recognised institution IDs"""
    # These should be linked back to the global CVs somehow
    # (probably as part of validation)

    # license: LicenseSpecification
    # """License specification that can be used with the data"""

    # mip_era: tuple[str, ...]
    # """Recognised MIP eras"""
    # These should be linked back to the global CVs somehow
    # (probably as part of validation)

    # product: tuple[str, ...]
    # """Recognised product types"""
    # These should be linked back to the global CVs somehow I assume (?)
    # (probably as part of validation)

    source_id_entries: SourceIDEntries
    """Source ID entries"""

    # target_mip_entries: TargetMIPEntries
    # """Target MIP entries"""
    # These should be linked back to the global CVs somehow I assume (?)
    # (probably as part of validation)

    # tracking_id_regexp: str | regexp
    # """Regular expression which files' tracking IDs must match"""

    def get_file_path(self, metadata: DatasetMetadataLike) -> Path:
        """
        Get file path for given metadata based on the data reference syntax

        This excludes any root directory
        i.e. the location within which to write the file.

        Parameters
        ----------
        metadata
            Metadata information

        Returns
        -------
            File path consistent with ``metadata``

        Notes
        -----
        According to [the DRS description](https://docs.google.com/document/d/1h0r8RZr_f3-8egBMMh7aqLwy3snpD6_MrDz1q8n5XUk/edit):

        - we're meant to use the CMIP data request variable names,
          not CF standards so that there aren't hyphens in variable_id.
          We've clearly not done that in input4MIPs in the past,
          so we are ignoring that rule here
          (but it would be important for other CV implementations!).

        - only [a-zA-Z0-9-] are allowed in file path names
          (keeping in mind the point above about how we're ignoring
          the 'standard' extra restriction on variable names in the file name),
          except where underscore is used as a separator.
          This is enforced here.
        """

        def akr(inp: str) -> str:
            """Apply known replacements"""
            known_replacements = {"_": "-", ".": "-"}
            res = inp
            for old, new in known_replacements.items():
                res = res.replace(old, new)

            return res

        directory = (
            Path(akr(metadata.activity_id))
            / akr(metadata.mip_era)
            / akr(metadata.target_mip)
            / akr(metadata.institution_id)
            / akr(metadata.source_id)
            / akr(metadata.realm)
            / akr(metadata.frequency)
            / akr(metadata.variable_id)
            / akr(metadata.grid_label)
            / akr(metadata.version)
        )
        for component in directory.parts:
            assert_all_valid_filepath_component_characters(component)

        filename_components = [
            akr(metadata.variable_id),
            akr(metadata.activity_id),
            akr(metadata.dataset_category),
            akr(metadata.target_mip),
            akr(metadata.source_id),
            akr(metadata.grid_label),
            akr(metadata.time_range),
        ]
        for component in filename_components:
            assert_all_valid_filepath_component_characters(component)

        filename = f"{'_'.join(filename_components)}.nc"

        res = directory / filename
        # Check validity of everything, excluding the suffix which we can safely
        # ignore because we set it
        for component in res.with_suffix("").parts:
            assert_all_valid_filepath_characters(component)

        return res


def assert_all_valid_filepath_component_characters(inp: str | Path) -> None:
    """
    Assert that the input only contains characters valid for filepath components

    Here, components means the things which make up the filepath
    and excludes any separators (e.g. underscores).

    Parameters
    ----------
    inp
        Input to validate

    See Also
    --------
    :py:func:`~input4mips_validation.cvs_handling.input4MIPs.cvs.assert_all_valid_filepath_characters`
    """
    valid_chars = set(string.ascii_letters + string.digits + "-")
    assert_only_valid_chars(inp, valid_chars=valid_chars)


def assert_all_valid_filepath_characters(inp: str | Path) -> None:
    """
    Assert that the input only contains characters valid for filepaths

    Separators (e.g. underscores) are included in the valid characters.

    Parameters
    ----------
    inp
        Input to validate

    See Also
    --------
    :py:func:`~input4mips_validation.cvs_handling.input4MIPs.cvs.assert_all_valid_filepath_component_characters`
    """
    valid_chars = set(string.ascii_letters + string.digits + "-" + "_")
    assert_only_valid_chars(inp, valid_chars=valid_chars)


def assert_only_valid_chars(inp: str | Path, valid_chars: set[str]):
    """
    Assert that the input only contains valid characters

    Parameters
    ----------
    inp
        Input to validate

    valid_chars
        Set of valid characters

    Raises
    ------
    ValueError
        ``inp`` contains characters that are not in ``valid_chars``
    """
    inp_set = set(str(inp))
    invalid_chars = inp_set.difference(valid_chars)

    if invalid_chars:
        msg = (
            f"Input contains invalid characters. "
            f"{inp=}, {sorted(invalid_chars)=}, {sorted(valid_chars)=}"
        )
        raise ValueError(msg)
