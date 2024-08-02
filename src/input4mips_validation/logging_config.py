"""
Logging configuration store
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any, Union

from loguru import logger
from typing_extensions import TypeAlias

LoggingConfigType: TypeAlias = Union[dict[str, list[dict[str, Any]]], None]
LoggingConfigSerialisedType: TypeAlias = Union[
    dict[str, list[dict[str, Union[str, Path]]]], None
]

LOGGING_CONFIG: LoggingConfigType = None
"""
Logging configuration being used

We provide this as a global variable
so it can be passed to parallel processes.
It's not clear if this is the right pattern,
but we're trying it.
"""


def serialise_logging_config(config: LoggingConfigType) -> LoggingConfigSerialisedType:
    """
    Serialise logging configuration

    This allows us to pass logging configuration from the main process
    to parallel process workers.
    We're not sure if this is the right pattern, but it is working for now.
    However, we don't know what all the edge cases are here, so bugs are likely.
    If you find one, please raise an issue.

    Parameters
    ----------
    config
        Configuration to serialise

    Returns
    -------
    :
        Serialised configuration
    """
    if config is None:
        res = None

    else:
        new_handlers_l = []
        for handler in config["handlers"]:
            new_handler = {k: v for k, v in handler.items() if k != "sink"}

            if isinstance(handler["sink"], (str, Path)):
                new_handler["sink"] = handler["sink"]

            elif handler["sink"] == sys.stderr:
                new_handler["sink"] = "stderr"

            elif handler["sink"] == sys.stderr:
                new_handler["sink"] = "stderr"

            else:
                logger.warning(
                    f"Not sure how to serialise {handler['sink']=}, "
                    "your parallel processes may explode"
                )
                new_handler["sink"] = handler["sink"]

            new_handlers_l.append(new_handler)

        res = {k: v for k, v in config.items() if k != "handlers"}
        res["handlers"] = new_handlers_l

    logger.debug(f"Serialised {config} to {res}")
    return res


def deserialise_logging_config(
    config: LoggingConfigSerialisedType,
) -> LoggingConfigType:
    """
    Deserialise logging configuration

    This allows us to load logging configuration from the main process
    in parallel process workers.
    We're not sure if this is the right pattern, but it is working for now.
    However, we don't know what all the edge cases are here, so bugs are likely.
    If you find one, please raise an issue.

    Parameters
    ----------
    config
        Serialised configuration to deserialise

    Returns
    -------
    :
        Deserialised configuration
    """
    if config is None:
        res: LoggingConfigType = None

    else:
        new_handlers_l = []
        for handler in config["handlers"]:
            new_handler: dict[str, Union[str, Path, io.TextIOWrapper, Any]] = {
                k: v for k, v in handler.items() if k != "sink"
            }

            if handler["sink"] == "stderr":
                logger.debug(f"Deserialising {handler['sink']=} to sys.stderr")
                new_handler["sink"] = sys.stderr

            elif handler["sink"] == "stdout":
                logger.debug(f"Deserialising {handler['sink']=} to sys.stdout")
                new_handler["sink"] = sys.stdout

            else:
                logger.debug(f"Deserialising {handler['sink']=} as is")
                new_handler["sink"] = handler["sink"]

            new_handlers_l.append(new_handler)

        res = {k: v for k, v in config.items() if k != "handlers"}
        res["handlers"] = new_handlers_l

    logger.debug(f"Deserialised {config} to {res}")
    return res
