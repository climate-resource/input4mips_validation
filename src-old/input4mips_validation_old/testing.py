"""
Testing related functions
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any


def get_call_kwargs(
    paras: tuple[tuple[str, Any]],
    extra_kwargs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Get kwargs used to call a callable.

    Useful when you want to test the default values of a function

    Parameters
    ----------
    paras
        Input parameters to test. Each element is the parameter's name and its
        value. If the value is ``None``, it is not included in the output.

    extra_kwargs
        Extra keyword arguments to the callable

    Returns
    -------
        Dictionary that can be used as the keyword arguments

    Examples
    --------
    >>> get_call_kwargs((("a", 3), ("b", None)))
    {'a': 3}
    >>> get_call_kwargs((("a", 3), ("b", "hello")))
    {'a': 3, 'b': 'hello'}
    >>> get_call_kwargs((("a", None), ("b", (1, 2))), extra_kwargs={"extra": 45})
    {'b': (1, 2), 'extra': 45}
    >>> # You have to be a bit careful with extra_kwargs because it can override things
    >>> get_call_kwargs((("a", None), ("b", (1, 2))), extra_kwargs={"b": 3})
    {'b': 3}
    """
    call_kwargs = {}

    for name, para in paras:
        if para is not None:
            call_kwargs[name] = para

    if extra_kwargs is not None:
        call_kwargs = call_kwargs | extra_kwargs

    return call_kwargs
