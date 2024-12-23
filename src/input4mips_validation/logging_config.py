"""
Logging configuration store
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict, Union

from typing_extensions import TypeAlias

if TYPE_CHECKING:
    from loguru import HandlerConfig


class ConfigLike(TypedDict):
    """
    Configuration-like to use with loguru
    """

    handlers: list[HandlerConfig]


LoggingConfigLike: TypeAlias = Union[ConfigLike, None]

LOGGING_CONFIG: LoggingConfigLike = None
"""
Logging configuration being used

We provide this as a global variable
so it can perhaps be used to help with configuring logging during parallel processing.
It's not clear if this is the right pattern, but we're keeping it for now.
"""
