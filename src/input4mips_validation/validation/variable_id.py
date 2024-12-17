"""
Validation of the `variable_id` attribute
"""

from __future__ import annotations

from collections.abc import Sequence

from input4mips_validation.validation.allowed_characters import (
    ALPHANUMERIC_AND_UNDERSCORES,
    ALPHANUMERIC_AND_UNDERSCORES_AND_HYPYHENS,
    check_only_allowed_characters,
)


def validate_variable_id(variable_id: str, ds_variables: str | Sequence[str]) -> None:
    """
    Validate the variable ID value

    Parameters
    ----------
    variable_id
        Variable ID value to validate.

    ds_variables
        Variable(s) that appear in the dataset.

    Raises
    ------
    ValueError
        `variable_id`'s value is incorrect
    """
    if isinstance(ds_variables, str) or len(ds_variables) == 1:
        allowed_characters = ALPHANUMERIC_AND_UNDERSCORES

        if isinstance(ds_variables, str):
            ds_variable = ds_variables
        else:
            ds_variable = ds_variables[0]

        if variable_id != ds_variable:
            msg = (
                f"The `variable_id` attribute "
                f"must match the variable name ({ds_variable!r}) exactly. "
                f"Received {variable_id=!r}."
            )
            raise ValueError(msg)

    else:
        allowed_characters = ALPHANUMERIC_AND_UNDERSCORES_AND_HYPYHENS

        if not variable_id.startswith("multiple"):
            msg = (
                "There is more than one variable in the dataset, "
                "hence the `variable_id` attribute "
                "must start with 'multiple'. "
                f"Received {variable_id=!r}."
            )
            raise ValueError(msg)

    try:
        check_only_allowed_characters(variable_id, allowed_characters)
    except ValueError as exc:
        msg = f"The `variable_id` attribute contains invalid characters. {exc}"
        raise ValueError(msg) from exc
