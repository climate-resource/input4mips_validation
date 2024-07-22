"""
Write a file we can use as our docs building environment on RtD
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
            fh.write("# This file is auto-generated, do not edit by hand!!\n")
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


ALL_KNOWN_ATTRIBUTES = {
    "Conventions": Attribute(
        name="Conventions",
        type_dec="str",
        docstring="CF conventions used in the file",
        comments=["TODO: validation", "string that matches CF-X.Y"],
    ),
    "grid_label": Attribute(
        name="grid_label",
        type_dec="str = field()",
        docstring="""Label that identfies the file's grid

[TODO: cross-ref to the CVs]""",
        comments=["TODO: validation", "Should be in CVs"],
    ),
    "grid": Attribute(
        name="grid",
        type_dec="Union[str, None] = None",
        docstring="Long-form description of the grid referred to by `grid_label`",
        comments=["# No validation, any string is fine"],
    ),
}


def get_files_to_write() -> Iterable[FileToWrite]:
    """
    Get the files to write

    Returns
    -------
        Files to (auto-)write
    """
    file_raw_database = FileToWrite(
        SRC / "database" / "raw.py",
        module_docstring="""
Raw database definition

This only contains the fields, no methods.
For a more useful class, see
[`Input4MIPsDatabaseEntryFile`][Input4MIPsDatabaseEntryFile].""",
        imports=(
            "from typing import Union",
            "",
            "from attrs import define, field",
        ),
        class_name="Input4MIPsDatabaseEntryFileRaw",
        class_docstring="Raw data model for a file entry in the input4MIPs database",
        class_attributes=(
            ALL_KNOWN_ATTRIBUTES[k] for k in ["Conventions", "grid_label", "grid"]
        ),
    )

    file_raw_database = FileToWrite(
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
        class_attributes=(ALL_KNOWN_ATTRIBUTES[k] for k in ["grid_label"]),
    )

    return [file_raw_database]


def main() -> None:
    """
    Write our auto-generated classes
    """
    files_to_write = get_files_to_write()

    for file in files_to_write:
        file.write()


if __name__ == "__main__":
    typer.run(main)
