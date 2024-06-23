"""
Handling of comparison with controlled vocabularies
"""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING

from input4mips_validation.controlled_vocabularies.handling.input4MIPs import (
    load_source_ids,
)

if TYPE_CHECKING:
    from typing import Any, Callable

    import attr


@functools.cache
def get_controlled_vocabulary_options_default(
    key: str,
) -> tuple[str, ...]:
    """
    Get options defined by the controlled vocabulary, default implementation.

    Parameters
    ----------
    key
        Key for which to retrieve the options (e.g. "source_id").

    Returns
    -------
        Options for that key acccording to the controlled vocabulary.
    """
    if key == "source_id":
        options = tuple([v.source_id for v in load_source_ids()])

    else:
        raise NotImplementedError(key)

    return options


def assert_value_matches_controlled_vocabulary(
    value: str,
    key: str,
    get_controlled_vocabulary_options: Callable[[str], tuple[str, ...]] | None = None,
) -> None:
    """
    Assert that a value matches the controlled vocabulary

    Parameters
    ----------
    value
        Value to check

    key
        Key (e.g. "institution_id") used to refer to these values
        in the controlled vocabulary.

    get_controlled_vocabulary_options
        Get options for the controlled vocabulary.
        If not supplied, we use :func:`get_controlled_vocabulary_options_default`.

    Raises
    ------
    AssertionError
        ``value`` does not match the controlled vocabulary for ``key``.
    """
    if get_controlled_vocabulary_options is None:
        get_controlled_vocabulary_options = get_controlled_vocabulary_options_default

    cv_options = get_controlled_vocabulary_options(key)

    if value not in cv_options:
        msg = (
            f"{key} is {value}. "
            f"This is not in the controlled vocabulary for {key}. "
            f"{cv_options=}"
        )
        raise AssertionError(msg)


def assert_attribute_being_set_matches_controlled_vocabulary(
    attribute: attr.Attribute[Any],
    value: str,
    **kwargs: Any,
) -> None:
    """
    Assert that an attribute being set matches the controlled vocabulary

    Parameters
    ----------
    attribute
        Attribute being set

    value
        Value to check

    **kwargs
        Passed to :func:`assert_value_matches_controlled_vocabulary`
    """
    assert_value_matches_controlled_vocabulary(
        value=value,
        key=attribute.name,
        **kwargs,
    )
