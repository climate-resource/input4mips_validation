"""
Handling of comparison with controlled vocabularies

Single source of truth is https://github.com/PCMDI/mip-cmor-tables/tree/main

Or maybe it should be https://github.com/PCMDI/input4MIPs_CVs?
TODO: Ask Paul
"""
from __future__ import annotations

import functools
from typing import TYPE_CHECKING

import requests

if TYPE_CHECKING:
    from typing import Any, Callable

    import attr


# Could also use pooch to store or something fancier for this caching, to be discussed
@functools.cache
def get_controlled_vocabulary_raw_default(
    key: str, timeout: int = 10
) -> dict[str, Any]:
    """
    Get raw controlled vocabulary JSON, default implementation

    Parameters
    ----------
    key
        Key for which to retrieve the options (e.g. "dataset_category").

    timeout
        How long to let requests run before a time out error is raised.

    Returns
    -------
        Raw JSON
    """
    # TODO: remove this huge hack once we work out where this is meant to come from
    if key == "institution_id":
        return ("PCMDI",)

    # TODO: remove this huge hack once we work out where this is meant to come from
    if key == "grid_label":
        return ("placeholder",)

    url_template = "https://raw.githubusercontent.com/PCMDI/input4MIPs_CVs/main/input4MIPs_{key}.json"
    url_to_hit = url_template.format(key=key)
    res = requests.get(url_to_hit, timeout=timeout)
    res.raise_for_status()

    return res.json()


@functools.cache
def get_controlled_vocabulary_options_default(
    key: str,
    get_controlled_vocabulary_raw: Callable[[str], dict[str, Any]] | None = None,
) -> tuple[str, ...]:
    """
    Get options defined by the controlled vocabulary, default implementation.

    Parameters
    ----------
    key
        Key for which to retrieve the options (e.g. "dataset_category").

    get_controlled_vocabulary_raw
        Function to use to get the raw JSON for the controlled vocabulary.

    Returns
    -------
        Options for that key acccording to the controlled vocabulary.
    """
    if get_controlled_vocabulary_raw is None:
        get_controlled_vocabulary_raw = get_controlled_vocabulary_raw_default

    raw = get_controlled_vocabulary_raw(key)

    # Have to make responses uniform on the CVs side,
    # can't have a different set of handling required for every key.
    if key == "activity_id":
        return tuple(raw.keys())

    if key == "target_mip":
        return tuple(raw.keys())

    if key == "source_id":
        return tuple(raw["source_id"].keys())

    return tuple(raw)


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


def get_controlled_vocabulary_target_mip_options(
    key: str, mip_era: str
) -> tuple[str, ...]:
    """
    Get options for target_mip from the controlled vocabulary

    The options are conditional on the mip_era, hence why it is an input.

    Parameters
    ----------
    key
        Metadata key.
        This is only used as a double check
        that the CV is being retrieved for target_mip.

    mip_era
        MIP era (restricts the options for target_mip).

    Returns
    -------
        Options for target_mip, given the value of mip_era
    """
    if key != "target_mip":
        raise AssertionError(key)

    raw = get_controlled_vocabulary_raw_default(key)

    return tuple(raw[mip_era])


def assert_target_mip_matches_controlled_vocabulary(
    value: str,
    key: str,
    mip_era: str,
    get_controlled_vocabulary_options: Callable[[str], tuple[str, ...]] | None = None,
) -> None:
    """
    Assert that the target_mip attribute matches the controlled vocabulary

    The options are conditional on the mip_era, hence why it is an input.

    Parameters
    ----------
    value
        Value to check

    key
        Metadata key.
        This is only used as a double check
        that the CV is being retrieved for target_mip.

    mip_era
        MIP era (restricts the options for target_mip).

    get_controlled_vocabulary_options
        Callable to use to retrieve the controlled vocabulary options.
        If not supplied, we use :func:`get_controlled_vocabulary_target_mip_options`
    """
    if get_controlled_vocabulary_options is None:
        get_controlled_vocabulary_options = functools.partial(
            get_controlled_vocabulary_target_mip_options, mip_era=mip_era
        )

    assert_value_matches_controlled_vocabulary(
        value, key, get_controlled_vocabulary_options=get_controlled_vocabulary_options
    )


def assert_target_mip_attribute_matches_controlled_vocabulary(
    instance: Any,  # TODO: tighten type hint up
    attribute: attr.Attribute[Any],
    value: str,
    **kwargs: Any,
):
    """
    Assert that the target_mip attribute matches the controlled vocabulary

    Parameters
    ----------
    instance
        Instance being initialised

    attribute
        Attribute being set

    value
        Value to check

    **kwargs
        Passed to :func:`assert_value_matches_controlled_vocabulary`
    """
    assert_target_mip_matches_controlled_vocabulary(
        value=value,
        key=attribute.name,
        mip_era=instance.mip_era,
        **kwargs,
    )
