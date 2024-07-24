"""
Auto-generate a number of classes

This allows us to keep the field definitions in line,
without having to type them in multiple places
or worry about them becoming inconsistent.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from string import Template

import typer
from attrs import define

SRC = Path(__file__).parent.parent / "src" / "input4mips_validation"


attribute_declaration_template = Template(
    """${name}: ${type_dec}
${docstring}
${comments}"""
)


@define
class Attribute:
    """Declaration of a class attribute"""

    name: str
    """Name of the attribute"""

    type_dec: str
    """Type declaration of the attribute, can also include the default value"""

    docstring: str
    """Docstring for the attribute"""

    comments: Iterable[str]
    """Comments to put below the attribute declaration"""

    def to_python(self) -> str:
        """Convert the attribute to its Python equivalent"""
        if "\n" in self.docstring:
            docstring = f'"""\n{self.docstring}\n"""'
        else:
            docstring = f'"""{self.docstring}"""'

        return attribute_declaration_template.substitute(
            name=self.name,
            type_dec=self.type_dec,
            docstring=docstring,
            comments="",
        )


class_declaration_template = Template(
    '''
@define
class ${class_name}:
    """
    ${class_docstring}
    """
'''
)


@define
class FileToWrite:
    """Definition of a file to write"""

    path: Path
    """Path in which to write the file"""

    module_docstring: str
    """Docstring to use for the file's header"""

    imports: tuple[str, ...]
    """Imports required for the file"""

    class_name: str
    """Name of the class to write"""

    class_docstring: str
    """Docstring of the class to write"""

    class_attributes: tuple[Attribute, ...]
    """Attributes to write on the class"""

    def write(self) -> None:
        """
        Write the file
        """
        with open(self.path, "w") as fh:
            fh.write(
                "# This file is auto-generated by pre-commit, do not edit by hand!!\n"
            )
            fh.write(f'"""{self.module_docstring}"""\n')
            imports = "\n".join(self.imports)
            fh.write(f"\n{imports}\n")
            fh.write("\n")
            fh.write(
                class_declaration_template.substitute(
                    class_name=self.class_name,
                    class_docstring=indnt(self.class_docstring),
                )
            )
            for attribute in self.class_attributes:
                fh.write("\n")
                fh.write(indnt(attribute.to_python(), include_first=True))


def indnt(inv: str, levels: int = 1, include_first: bool = False) -> str:
    """
    Indent the input a given number of levels

    Parameters
    ----------
    inv
        Input to which to add indent

    levels
        Number of levels to indent

    Returns
    -------
        Indented `inv`
    """
    indent = levels * "    "

    res_l = []
    for i, line in enumerate(inv.splitlines()):
        if i == 0:
            if include_first:
                res_l.append(f"{indent}{line}")
            else:
                res_l.append(line)

            continue

        if line:
            res_l.append(f"{indent}{line}")
        else:
            res_l.append("")

    res = "\n".join(res_l)
    if inv.endswith("\n"):
        res = f"{res}\n"

    return res


# Things to consider:
# - comment_provider and comment_esgf
#   - split so that provider can provide comments,
#     but we can also add comments to ESGF database after the file is published
#
# - title
#   - seems to make little sense to track this in the database

ALL_KNOWN_ATTRIBUTES = {
    "Conventions": Attribute(
        name="Conventions",
        type_dec="str",
        docstring="CF conventions used in the file",
        comments=["TODO: validation", "string that matches CF-X.Y"],
    ),
    "activity_id": Attribute(
        name="activity_id",
        type_dec="str",
        docstring="Activity ID that applies to the file",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "contact": Attribute(
        name="contact",
        type_dec="str",
        docstring="Email addresses to contact in case of questions about the file",
        comments=["TODO: validation", "Should follow some sort of standard form"],
    ),
    "creation_date": Attribute(
        name="creation_date",
        type_dec="str",
        docstring="Date the file was created",
        comments=["TODO: validation", "YYYY-mm-DDTHH:MM:ssZ I think i.e. ISO format"],
    ),
    "dataset_category": Attribute(
        name="dataset_category",
        type_dec="str",
        docstring="The file's category",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "datetime_end": Attribute(
        name="datetime_end",
        type_dec="str",
        docstring="The file's end time",
        comments=[
            "TODO: validation",
            "Should have specific form, based on file's frequency or standard",
            "but unclear right now what the rules are",
        ],
    ),
    "datetime_start": Attribute(
        name="datetime_start",
        type_dec="str",
        docstring="The file's start time",
        comments=[
            "TODO: validation",
            "Should have specific form, based on file's frequency or standard",
            "but unclear right now what the rules are",
        ],
    ),
    "frequency": Attribute(
        name="frequency",
        type_dec="str",
        docstring="Frequency of the data in the file",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "further_info_url": Attribute(
        name="further_info_url",
        type_dec="str",
        docstring=(
            "URL where further information about the file/data in the file can be found"
        ),
        comments=["TODO: validation", "Should be a URL"],
    ),
    "grid": Attribute(
        name="grid",
        type_dec="Union[str, None] = None",
        docstring="Long-form description of the grid referred to by `grid_label`",
        comments=["# No validation, any string is fine"],
    ),
    "grid_label": Attribute(
        name="grid_label",
        type_dec="str = field()",
        docstring="""Label that identfies the file's grid

[TODO: cross-ref to the CVs]""",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "institution": Attribute(
        name="institution",
        type_dec="Union[str, None] = None",
        docstring=(
            "Long-form description of the institute referred to by `institution_id`"
        ),
        comments=["No validation, any string is fine"],
    ),
    "institution_id": Attribute(
        name="institution_id",
        type_dec="str",
        docstring="ID of the institute that created the file",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "license": Attribute(
        name="license",
        type_dec="str",
        docstring="License information for the dataset",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "license_id": Attribute(
        name="license_id",
        type_dec="Union[str, None] = None",
        docstring="ID of the license that applies to this dataset",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "mip_era": Attribute(
        name="mip_era",
        type_dec="str",
        docstring="The MIP era to which this file belong",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "nominal_resolution": Attribute(
        name="nominal_resolution",
        type_dec="str",
        docstring="Nominal resolution of the data in the file",
        comments=[
            "TODO: validation",
            "https://github.com/PCMDI/nominal_resolution",
            "May need to add more bins to the tool",
        ],
    ),
    "product": Attribute(
        name="product",
        type_dec="str",
        docstring="The kind of data in the file",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "realm": Attribute(
        name="realm",
        type_dec="str",
        docstring="The realm of the data in the file",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "references": Attribute(
        name="references",
        type_dec="Union[str, None] = None",
        docstring=("References relevant to the file"),
        comments=["TODO: validation (?) e.g. expect only DOIs?"],
    ),
    "region": Attribute(
        name="region",
        type_dec="str",
        docstring="The region of the data in the file",
        comments=[
            "TODO: validation",
            "Has to be validated against CV/CF conventions",
            "https://github.com/PCMDI/obs4MIPs-cmor-tables/blob/master/obs4MIPs_region.json",
        ],
    ),
    "source": Attribute(
        name="source",
        type_dec="Union[str, None] = None",
        docstring=("Long-form description of the source referred to by `source_id`"),
        comments=["No validation, any string is fine"],
    ),
    "source_id": Attribute(
        name="source_id",
        type_dec="str",
        docstring="The ID of the file's source",
        comments=[
            "TODO: validation",
            "Should be in CVs",
            "Other fields which must be consistent with source ID values should match",
        ],
    ),
    "source_version": Attribute(
        name="source_version",
        type_dec="str",
        docstring="The version of the file, as defined by the source",
        comments=[
            "TODO: validation",
            "Should be consistent with CVs",
        ],
    ),
    "target_mip": Attribute(
        name="target_mip",
        type_dec="str",
        docstring="The MIP that this file targets",
        comments=[
            "TODO: validation",
            "Should be in CVs",
        ],
    ),
    "time_range": Attribute(
        name="time_range",
        type_dec="str",
        docstring="The file's time range",
        comments=[
            "TODO: validation",
            "Should have specific form, based on file's frequency.",
            "Should match file name",
        ],
    ),
    "tracking_id": Attribute(
        name="tracking_id",
        type_dec="str",
        docstring="""Tracking ID of the file

This should be unique for every file.
We typically use the uuid library to generate this.

```python
# For example
import uuid  # part of the standard library

tracking_id = f"hdl:21.14100/{uuid.uuid4()}"
```""",
        comments=[
            "TODO: validation",
            "Should match specific regexp",
        ],
    ),
    "variable_id": Attribute(
        name="variable_id",
        type_dec="str",
        docstring="The ID of the variable contained in the file",
        comments=[
            "TODO: validation (?)",
            "Should match file contents/CF conventions (?)",
        ],
    ),
    "version": Attribute(
        name="version",
        type_dec="str",
        docstring="The version of the file, as defined by the ESGF index",
        comments=[
            "TODO: validation",
            "Should be 'vYYYYMMDD', ",
            "where YYYYMMDD is the date that it was put into the DRS",
            "(which is unverifiable within this package)",
        ],
    ),
}


def get_files_to_write() -> Iterable[FileToWrite]:
    """
    Get the files to write

    Returns
    -------
        Files to (auto-)write
    """
    RAW_DATABASE_FIELDS = [
        "Conventions",
        "activity_id",
        "contact",
        "creation_date",
        "dataset_category",
        "datetime_end",
        "datetime_start",
        "frequency",
        "further_info_url",
        "grid_label",
        "institution_id",
        "license",
        "mip_era",
        "nominal_resolution",
        "product",
        "realm",
        "region",
        "source_id",
        "source_version",
        "target_mip",
        "time_range",
        "tracking_id",
        "variable_id",
        "version",
        # Fields with default values have to go at the end
        "grid",
        "institution",
        "license_id",
        "references",
        "source",
    ]

    missing = set(ALL_KNOWN_ATTRIBUTES.keys()).difference(set(RAW_DATABASE_FIELDS))
    if missing:
        raise AssertionError(missing)

    file_raw_database = FileToWrite(
        SRC / "database" / "raw.py",
        module_docstring="""
Raw database definition

This only contains the fields, no methods.
For a more useful class, see
[`Input4MIPsDatabaseEntryFile`][input4mips_validation.database.Input4MIPsDatabaseEntryFile].
""",
        imports=(
            "from typing import Union",
            "",
            "from attrs import define, field",
        ),
        class_name="Input4MIPsDatabaseEntryFileRaw",
        class_docstring="Raw data model for a file entry in the input4MIPs database",
        class_attributes=(ALL_KNOWN_ATTRIBUTES[k] for k in RAW_DATABASE_FIELDS),
    )

    DATASET_METADATA_FIELDS = (
        "activity_id",
        "contact",
        "dataset_category",
        "frequency",
        "further_info_url",
        "grid_label",
        "institution_id",
        "license",
        "mip_era",
        "nominal_resolution",
        "product",
        "realm",
        "region",
        "source_id",
        "source_version",
        "target_mip",
        "variable_id",
        # Fields with default values have to go at the end
        "institution",
        "license_id",
        "source",
    )
    file_input4mips_dataset_metadata = FileToWrite(
        SRC / "dataset" / "metadata.py",
        module_docstring="""
Metadata for `Input4MIPsDataset` objects

See [Input4MIPsDataset][input4mips_validation.dataset.dataset.Input4MIPsDataset]
""",
        imports=(
            "from typing import Union",
            "",
            "from attrs import define, field",
        ),
        class_name="Input4MIPsDatasetMetadata",
        class_docstring="""Metadata for an input4MIPs dataset""",
        class_attributes=(ALL_KNOWN_ATTRIBUTES[k] for k in DATASET_METADATA_FIELDS),
    )

    DATASET_PRODUCER_MINIMUM_ATTRIBUTES = (
        "grid_label",
        "nominal_resolution",
        "product",
        "region",
        "source_id",
        "target_mip",
    )
    file_metadata_producer_minimum = FileToWrite(
        SRC / "dataset" / "metadata_data_producer_minimum.py",
        module_docstring=(
            "Minimum metadata required from an input4MIPs dataset producer"
        ),
        imports=("from attrs import define, field",),
        class_name="Input4MIPsDatasetMetadataDataProducerMinimum",
        class_docstring="""Minimum metadata required from an input4MIPs dataset producer

This is the minimum metadata required to create a valid
[`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
[`from_data_producer_minimum_information`][input4mips_validation.dataset.Input4MIPsDataset.from_data_producer_minimum_information].""",
        class_attributes=(
            ALL_KNOWN_ATTRIBUTES[k] for k in DATASET_PRODUCER_MINIMUM_ATTRIBUTES
        ),
    )

    file_metadata_producer_multi_variable_minimum = FileToWrite(
        SRC / "dataset" / "metadata_data_producer_multiple_variable_minimum.py",
        module_docstring="""
Minimum metadata required from an input4MIPs dataset producer for a multi-variable file
""",
        imports=("from attrs import define, field",),
        class_name="Input4MIPsDatasetMetadataDataProducerMultipleVariableMinimum",
        class_docstring="""Minimum metadata required from input4MIPs dataset producer for a multi-variable file

This is the minimum metadata required to create a valid
[`Input4MIPsDataset`][input4mips_validation.dataset.Input4MIPsDataset] object using
[`from_data_producer_minimum_information_multiple_variable`][input4mips_validation.dataset.dataset.Input4MIPsDataset.from_data_producer_minimum_information_multiple_variable].""",  # noqa E501
        class_attributes=(
            ALL_KNOWN_ATTRIBUTES[k]
            for k in [
                *DATASET_PRODUCER_MINIMUM_ATTRIBUTES,
                "dataset_category",
                "realm",
            ]
        ),
    )

    file_source_id_values = FileToWrite(
        SRC / "cvs" / "source_id" / "values.py",
        module_docstring="Source ID values definition",
        imports=(
            "from typing import Union",
            "",
            "from attrs import define",
        ),
        class_name="SourceIDValues",
        class_docstring="Values defined by a source ID",
        class_attributes=(
            ALL_KNOWN_ATTRIBUTES[k]
            for k in [
                "contact",
                "further_info_url",
                "institution_id",
                "mip_era",
                "source_version",
                "license_id",
            ]
        ),
    )

    return [
        file_raw_database,
        file_input4mips_dataset_metadata,
        file_metadata_producer_minimum,
        file_metadata_producer_multi_variable_minimum,
        file_source_id_values,
    ]


def main() -> None:
    """
    Write our auto-generated classes
    """
    files_to_write = get_files_to_write()

    for file in files_to_write:
        file.write()


if __name__ == "__main__":
    typer.run(main)
