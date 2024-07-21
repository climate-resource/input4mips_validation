"""
Data reference syntax data model
"""

from __future__ import annotations

import datetime as dt
import functools
import json
import os
import re
import string
from collections.abc import Iterable
from pathlib import Path

import cftime
import numpy as np
import pandas as pd
from attrs import frozen
from typing_extensions import TypeAlias

from input4mips_validation.cvs.loading_raw import RawCVLoader
from input4mips_validation.inference.from_data import create_time_range
from input4mips_validation.serialisation import converter_json

DATA_REFERENCE_SYNTAX_FILENAME: str = "input4MIPs_DRS.json"
"""Default name of the file in which the data reference syntax is saved"""

DataReferenceSyntaxUnstructured: TypeAlias = dict[str, str]
"""Form into which the DRS is serialised for the CVs"""


@frozen
class DataReferenceSyntax:
    """
    Data reference syntax definition

    This defines how directories and filepaths should be created.

    Within the templates, we apply the following rules for parsing the templates.

    Carets ("<" and ">") are placeholders for values
    that should be replaced with metadata values.
    E.g. assuming that the data's model_id is "BD29",
    "CMIP/<model_id>" will be translated to "CMIP/BD29".

    Square brackets ("[" and "]") indicate that the part of the template is optional.
    If the optional metadata isn't there, this part of the DRS will not be included.
    E.g. assuming that the data's frequency is "mon" and the model ID is "AB34",
    "<model_id>[_<frequency>]" will be translated to "AB34_mon",
    but if there is no frequency metadata,
    then the result will simply be "AB34".

    Paths are handled using [pathlib.Path][],
    hence unix-like paths can be used in the template
    and they will still work on Windows machines.
    """

    directory_path_template: str
    """Template for creating directories"""

    directory_path_example: str
    """Example of a complete directory path"""

    filename_template: str
    """Template for creating filenames"""

    filename_example: str
    """Example of a complete filename"""

    def get_file_path(  # noqa: PLR0913
        self,
        root_data_dir: Path,
        available_attributes: dict[str, str],
        time_start: cftime.datetime | dt.datetime | np.datetime64 | None = None,
        time_end: cftime.datetime | dt.datetime | np.datetime64 | None = None,
        frequency_metadata_key: str = "frequency",
        version: str | None = None,
    ) -> Path:
        """
        Get the (full) path to a file based on the DRS

        Parameters
        ----------
        root_data_dir
            Root directory in which the data is to be written.

            The generated path will be relative to `root_data_dir`.

        available_attributes
            The available metadata attributes for creating the path.

            All the elements expected by the DRS must be provided.
            For example, if the DRS' filename template is
            "<model_id>_<institution_id>.nc",
            then `available_attributes` must provide both
            `"model_id"` and `"institution_id"`.

        time_start
            The earliest time point in the data's time axis.

            This is a special case.
            Some DRS definitions expect time range information,
            but this metadata is not contained in any of the file's metadata,
            hence the end time must be supplied
            so that the time range information can be included.

        time_end
            The latest time point in the data's time axis.

            This is a special case.
            Some DRS definitions expect time range information,
            but this metadata is not contained in any of the file's metadata,
            hence the end time must be supplied
            so that the time range information can be included.

        frequency_metadata_key
            The key in the data's metadata
            which points to information about the data's frequency.

        version
            The version to use when creating the path.

            This is a special case.
            Some DRS definitions expect version metadata,
            but this metadata is not contained in any of the file's metadata,
            hence must be supplied separately.
            If not supplied and version is required,
            we simply use today's date, formatted as YYYYMMDD.

        Returns
        -------
            The path in which to write the file according to the DRS

        Raises
        ------
        KeyError
            A metadata attribute expected by the DRS is not supplied.

        ValueError
            Time range information is required by the DRS,
            but `time_start` and `time_end` are not supplied.
        """
        # First step: apply a number of known replacements
        all_available_metadata = {
            k: apply_known_replacements(v) for k, v in available_attributes.items()
        }

        directory_substitutions = self.parse_drs_template(
            drs_template=self.directory_path_template
        )
        filename_substitutions = self.parse_drs_template(
            drs_template=self.filename_template
        )

        all_substitutions = (*directory_substitutions, *filename_substitutions)
        if (
            key_required_for_substitutions("version", all_substitutions)
            and version is None
        ):
            version = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
            all_available_metadata["version"] = version

        time_information_provided = (time_start is not None) and (time_end is not None)
        if (
            key_required_for_substitutions("time_range", all_substitutions)
            and not time_information_provided
        ):
            msg = (
                "The DRS requires time range information "
                "so both time_start and time_end must be provided. "
                f"Received {time_start=} and {time_end=}."
            )
            ValueError(msg)

        if (
            key_in_substitutions("time_range", all_substitutions)
            and time_information_provided
        ):
            # Hard-code here for now because the rules about time-range
            # creation cannot be inferred from the DRS as currently written.
            all_available_metadata["time_range"] = create_time_range(
                time_start=time_start,
                time_end=time_end,
                ds_frequency=all_available_metadata[frequency_metadata_key],
            )

        apply_subs = functools.partial(
            apply_substitutions,
            metadata=all_available_metadata,
            validate_substituted_metadata=True,
        )
        # Cast to path to ensure windows compatibility
        directory = Path(
            apply_subs(
                self.directory_path_template,
                substitutions=directory_substitutions,
            )
        )
        filename = apply_subs(
            self.filename_template,
            substitutions=filename_substitutions,
        )

        generated_path = directory / filename
        # Check validity of everything, excluding the suffix
        for component in generated_path.with_suffix("").parts:
            assert_full_filepath_only_contains_valid_characters(component)

        return root_data_dir / generated_path

    @functools.cache
    def parse_drs_template(self, drs_template: str) -> tuple[DRSSubstitution, ...]:
        """
        Parse a DRS template string

        For the rules about parsing, see [DataReferenceSyntax][].

        Parameters
        ----------
        drs_template
            DRS template to parse

        Returns
        -------
            Substitutions defined by `drs_template`
        """
        # This is a pretty yuck implementation.
        # PRs welcome to improve it
        # (will need quite some tests too to ensure correctness)
        # For now, we are ok with this because
        # a) it is relatively easy to follow
        # b) we use caching so it doesn't matter too much that it is slow

        # Hard-code here to ensure we match docstrings.
        # Could loosen this in future of course,
        # but I don't want to abstract that far right now.
        start_placeholder = "<"
        end_placeholder = ">"
        start_optional = "["
        end_optional = "]"

        substitutions_l = []
        in_optional_section = False
        in_placeholder = False
        placeholder_pieces = []
        optional_pieces = []
        for i, c in enumerate(drs_template):
            if c == start_optional:
                if optional_pieces:
                    msg = (
                        "Starting new optional section, "
                        "should not have optional_pieces"
                    )
                    # Can use the below for better error messages
                    # drs_template[:i + 1]
                    raise AssertionError(msg)

                in_optional_section = True
                continue

            if c == start_placeholder:
                if placeholder_pieces:
                    msg = (
                        "Starting new placeholder section, "
                        "should not have placeholder_pieces"
                    )
                    raise AssertionError(msg)

                in_placeholder = True
                if in_optional_section:
                    optional_pieces.append(c)
                continue

            if c == end_placeholder:
                if not in_placeholder:
                    msg = "Found end_placeholder without being in_placeholder"
                    raise AssertionError(msg)

                if in_optional_section:
                    optional_pieces.append(c)

                else:
                    # Can finalise this section
                    metadata_key = "".join(placeholder_pieces)
                    substitutions_l.append(
                        DRSSubstitution(
                            optional=False,
                            string_to_replace=f"{start_placeholder}{metadata_key}{end_placeholder}",
                            required_metadata=(metadata_key,),
                            replacement_string=f"{{{metadata_key}}}",
                        )
                    )

                    placeholder_pieces = []

                in_placeholder = False
                continue

            if c == end_optional:
                if not in_optional_section:
                    msg = "Found end_optional without being in_optional_section"
                    raise AssertionError(msg)

                if in_placeholder:
                    msg = "Should have already exited placeholder"
                    raise AssertionError(msg)

                metadata_key = "".join(placeholder_pieces)
                optional_section = "".join(optional_pieces)
                substitutions_l.append(
                    DRSSubstitution(
                        optional=False,
                        string_to_replace=f"{start_optional}{optional_section}{end_optional}",
                        required_metadata=(metadata_key,),
                        replacement_string=optional_section.replace(
                            f"{start_placeholder}{metadata_key}{end_placeholder}",
                            f"{{{metadata_key}}}",
                        ),
                    )
                )

                placeholder_pieces = []
                optional_pieces = []
                in_optional_section = False
                continue

            if in_placeholder:
                placeholder_pieces.append(c)

            if in_optional_section:
                optional_pieces.append(c)

        return tuple(substitutions_l)

    def extract_metadata_from_path(self, path: Path) -> dict[str, str]:
        """
        Extract metadata from a path

        To be specific, the bit of the path
        that corresponds to `self.directory_path_template`.
        In other words,
        `path` should only be the directory/folder bit of the full filepath,
        the filename should not be part of `path`.

        Parameters
        ----------
        directory
            Directory from which to extract the metadata

        Returns
        -------
            Extracted metadata
        """
        root_data_dir_key = "root_data_dir"

        directory_regexp = self.get_regexp_for_capturing_directory_information(
            root_data_dir_group=root_data_dir_key
        )
        match = re.match(directory_regexp, str(path))
        match_groups = match.groupdict()

        res = {k: v for k, v in match_groups.items() if k != root_data_dir_key}

        return res

    @functools.cache
    def get_regexp_for_capturing_directory_information(
        self, root_data_dir_group: str = "root_data_dir"
    ) -> str:
        """
        Get a regular expression for capturing information from a directory

        Parameters
        ----------
        root_data_dir_group
            Group name for the group which captures the root data directory.

        Returns
        -------
            Regular expression which can be used to capture information
            from a directory.

        Notes
        -----
        According to [the DRS description](https://docs.google.com/document/d/1h0r8RZr_f3-8egBMMh7aqLwy3snpD6_MrDz1q8n5XUk):

        - only [a-zA-Z0-9-] are allowed in file path names
          except where underscore is used as a separator.

        We use this to significantly simplify our regular expression.
        """
        # Hard-code according to the spec
        valid_chars_names = "[a-zA-Z0-9-]"

        drs_template = self.directory_path_template
        directory_substitutions = self.parse_drs_template(drs_template=drs_template)

        capturing_regexp = drs_template
        for substitution in directory_substitutions:
            if substitution.optional:
                raise NotImplementedError()

            capturing_group = substitution.replacement_string.replace(
                "}", f">{valid_chars_names}+)"
            ).replace("{", "(?P<")
            capturing_regexp = capturing_regexp.replace(
                substitution.string_to_replace,
                capturing_group,
            )

        # Make sure that the separators will behave
        sep_escape = re.escape(os.sep)
        capturing_regexp = capturing_regexp.replace("/", sep_escape)
        # And that our regexp allows for the root directory
        capturing_regexp = (
            f"(?P<{root_data_dir_group}>.*){sep_escape}{capturing_regexp}"
        )

        return capturing_regexp


@frozen
class DRSSubstitution:
    """
    A substitution to apply to a DRS template
    """

    string_to_replace: str
    """String in the DRS template to replace"""

    required_metadata: tuple[str, ...]
    """The metadata required to correctly apply the substitution"""

    replacement_string: str
    """
    String to use to replace `self.string_to_replace` in the DRS template

    This contains placeholders.
    The actual replacement is generated by calling `replacement_string.format`
    as part of `self.format_replacement_string`.
    """

    optional: bool
    """Whether this substitution is optional or not.

    If the substitution is optional, then,
    if metadata is not present when calling `self.apply_substitution`,
    `self.string_to_replace` is simply deleted from the DRS template.
    If the substitution is not optional, then,
    if metadata is not present when calling `self.apply_substitution`,
    a `KeyError` is raised.
    """

    def apply_substitution(
        self,
        start: str,
        metadata: dict[str, str],
        validate_substituted_metadata: bool = True,
    ):
        """
        Apply the substitution

        Parameters
        ----------
        start
            String to which to apply the substitution

        metadata
            Metadata from which the substitution values can be retrieved

        validate_substituted_metadata
            If `True`, the substituted metadata is validated to ensure that its values
            only contain allowed characters before being applied.

        Returns
        -------
            `start` with the substitution defined by `self` applied
        """
        missing_metadata = [k for k in self.required_metadata if k not in metadata]
        if missing_metadata:
            if not self.optional:
                # raise a custom error here which shows what metadata is missing
                # and the start string
                # raise MetadataRequiredForSubstitutionMissingError(missing_metadata)
                raise NotImplementedError()

            # Optional but meadata no there, so simply delete this section
            res = start.replace(self.string_to_replace, "")

        else:
            metadata_to_substitute = {k: metadata[k] for k in self.required_metadata}
            if validate_substituted_metadata:
                assert_all_metadata_substitutions_only_contain_valid_characters(
                    metadata_to_substitute
                )

            res = start.replace(
                self.string_to_replace,
                self.replacement_string.format(**metadata_to_substitute),
            )

        return res


def apply_known_replacements(
    inp: str, known_replacements: dict[str, str] | None = None
) -> str:
    """
    Apply known replacements of characters in metadata values

    This helps ensure that only valid characters appear in our populated DRS templates.
    For further details about the characters which are valid,
    see [`assert_all_metadata_substitutions_only_contain_valid_characters`][assert_all_metadata_substitutions_only_contain_valid_characters]
    and [`assert_full_filepath_only_contains_valid_characters`][assert_full_filepath_only_contains_valid_characters].

    Parameters
    ----------
    inp
        Input metadata value

    known_replacements
        Known replacements to apply.

        If `None`, a default set is used.

    Result
    ------
        `inp` with known replacements applied.
    """  # noqa: E501
    if known_replacements is None:
        known_replacements = {"_": "-", ".": "-"}

    res = inp
    for old, new in known_replacements.items():
        res = res.replace(old, new)

    return res


def assert_only_valid_chars(inp: str | Path, valid_chars: set[str]) -> None:
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


def assert_all_metadata_substitutions_only_contain_valid_characters(
    metadata: dict[str, str],
) -> None:
    """
    Assert that all the metadata substitutions only contain valid characters

    For metadata being applied to a DRS template, only certain characters are allowed.

    According to [the DRS description](https://docs.google.com/document/d/1h0r8RZr_f3-8egBMMh7aqLwy3snpD6_MrDz1q8n5XUk):

    - only [a-zA-Z0-9-] are allowed in file path names
      except where underscore is used as a separator.
      This is enforced here.

    - we're meant to use the CMIP data request variable names, not CF standards,
      so that there aren't hyphens in the values for the "variable_id" key.
      We've clearly not done that in input4MIPs,
      so we are ignoring that rule here
      (but it would be important for other CV implementations!).

    Parameters
    ----------
    metadata
        Metadata substitutions to check

    Raises
    ------
    ValueError
        One of the metadata substitutions contains invalid characters

    See Also
    --------
    [`assert_full_filepath_only_contains_valid_characters`][assert_full_filepath_only_contains_valid_characters]
    """
    # Hard-code according to the spec
    valid_chars = set(string.ascii_letters + string.digits + "-")
    for k, v in metadata.items():
        # Special case for variable_id would go here if we applied it
        try:
            assert_only_valid_chars(v, valid_chars=valid_chars)
        except ValueError as exc:
            msg = f"Metadata for {k}, {v!r}, contains invalid characters"
            raise ValueError(msg) from exc


def assert_full_filepath_only_contains_valid_characters(
    full_filepath: str | Path,
) -> None:
    """
    Assert that a filepath only contains valid characters

    According to [the DRS description](https://docs.google.com/document/d/1h0r8RZr_f3-8egBMMh7aqLwy3snpD6_MrDz1q8n5XUk):

    - only [a-zA-Z0-9-] are allowed in file path names
      except where underscore is used as a separator.

    Parameters
    ----------
    full_filepath
        Full filepath (directories and filename) to validate

    Raises
    ------
    ValueError
        `full_filepath` contains invalid characters

    See Also
    --------
    [`assert_all_metadata_substitutions_only_contain_valid_characters`][assert_all_metadata_substitutions_only_contain_valid_characters]
    """
    # Hard-code according to the spec
    valid_chars = set(string.ascii_letters + string.digits + "-" + "_")
    assert_only_valid_chars(full_filepath, valid_chars=valid_chars)


def apply_substitutions(
    drs_template: str,
    substitutions: Iterable[DRSSubstitution, ...],
    metadata: dict[str, str],
    validate_substituted_metadata: bool = True,
) -> str:
    """
    Apply a series of substitutions to a DRS template

    Parameters
    ----------
    drs_template
        DRS template to which the substitutions should be applied

    substitutions
        Substitutions to apply

    metadata
        Metadata from which the substitution values can be retrieved

    validate_substituted_metadata
        Passed to
        [`DRSSubstitution.apply_substitution`][DRSSubstitution.apply_substitution].

    Returns
    -------
        DRS template, with all substitutions in `substitutions` applied
    """
    res = drs_template
    for substitution in substitutions:
        res = substitution.apply_substitution(
            res,
            metadata=metadata,
            validate_substituted_metadata=validate_substituted_metadata,
        )
        # # TODO: swap to the below
        # try:
        #     res = substitution.apply_substitution(res, metadata=metadata)
        # except MetadataRequiredForSubstitutionMissingError:
        #     # Add information about the full DRS, then raise from

    return res


def key_required_for_substitutions(
    key: str, substitutions: tuple[DRSSubstitution]
) -> bool:
    """
    Return whether a key is required metadata or not for populating the DRS

    Parameters
    ----------
    key
        Metadata key

    substitutions
        Substitutions that will be applied to the DRS

    Returns
    -------
        `True` if the key is required metadata to populate the DRS, otherwise `False`.
    """
    return any(key in v.required_metadata and not v.optional for v in substitutions)


def key_in_substitutions(key: str, substitutions: tuple[DRSSubstitution]) -> bool:
    """
    Return whether a key is in the DRS or not

    Parameters
    ----------
    key
        Metadata key

    substitutions
        Substitutions that will be applied to the DRS

    Returns
    -------
        `True` if the key is in the DRS, otherwise `False`.
    """
    return any(key in v.required_metadata for v in substitutions)


def format_date_for_time_range(
    date: cftime.datetime | dt.datetime | np.datetime64,
    ds_frequency: str,
) -> str:
    """
    Format date for providing time range information

    Parameters
    ----------
    date
        Date to format

    ds_frequency
        Frequency of the data in the underlying dataset

    Returns
    -------
        Formatted date
    """
    if isinstance(date, np.datetime64):
        date_safe: cftime.datetime | dt.datetime = pd.to_datetime(str(date))
    else:
        date_safe = date

    if ds_frequency.startswith("mon"):
        return date_safe.strftime("%Y%m")

    if ds_frequency.startswith("yr"):
        return date_safe.strftime("%Y")

    if ds_frequency.startswith("day"):
        return date_safe.strftime("%Y%m%d")

    if ds_frequency.startswith("3hr"):
        return date_safe.strftime("%Y%m%d%H%M")

    raise NotImplementedError(ds_frequency)


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
