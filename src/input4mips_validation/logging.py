"""
Logging
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional, Union

from loguru import logger

# Type ignore while we wait for
# https://github.com/erezinman/loguru-config/pull/2
from loguru_config import LoguruConfig  # type: ignore

# Ensure that the logger knows about our levels
# For emojis: https://www.iemoji.com/view/emoji/766/objects/right-pointing-magnifying-glass
LOG_LEVEL_INFO_FILE = logger.level(
    name="INFO_FILE", no=15, color="<blue><bold>", icon="\u2139"
)
"""
Logging level that gives information at the file level

This is between DEBUG and INFO
"""

LOG_LEVEL_INFO_FILE_ERROR = logger.level(
    name="INFO_FILE_ERROR",
    no=LOG_LEVEL_INFO_FILE.no + 1,
    color="<red><bold>",
    icon="\u274c",
)
"""
Logging level that gives information about a failure at the file level

One level higher than
[LOG_LEVEL_INFO_FILE][input4mips_validation.logging.LOG_LEVEL_INFO_FILE].
"""

LOG_LEVEL_INFO_INDIVIDUAL_CHECK = logger.level(
    name="INFO_INDIVIDUAL_CHECK", no=12, color="<light-blue>", icon="\U0001f50e"
)
"""
Logging level that gives information at the level of individual checks

This is between DEBUG and LOG_LEVEL_INFO_FILE
"""

LOG_LEVEL_INFO_INDIVIDUAL_CHECK_ERROR = logger.level(
    name="INFO_INDIVIDUAL_CHECK_ERROR",
    no=LOG_LEVEL_INFO_INDIVIDUAL_CHECK.no + 1,
    color="<red>",
    icon="\u274c",
)
"""
Logging level that gives information about a failure at the individual check level

One level higher than
[LOG_LEVEL_INFO_INDIVIDUAL_CHECK][input4mips_validation.logging.LOG_LEVEL_INFO_INDIVIDUAL_CHECK].
"""

DEFAULT_LOGGING_CONFIG = dict(
    handlers=[
        dict(
            sink=sys.stderr,
            level=LOG_LEVEL_INFO_INDIVIDUAL_CHECK.name,
            colorize=True,
            format=" - ".join(
                [
                    "<green>{time:!UTC}</>",
                    "{level.icon} <lvl>{level}</>",
                    "<cyan>{name}:{file}:{line}</>",
                    "<lvl>{message}</>",
                ]
            ),
        )
    ],
)
"""Default configuration used with :meth:`loguru.logger.configure`"""


def setup_logging(
    enable: bool,
    config: Optional[Union[Path, dict[str, Any]]] = None,
    log_level: Optional[str] = None,
) -> None:
    """
    Early setup for logging.

    Parameters
    ----------
    enable
        Whether to enable the logger.

        If `False`, we explicitly disable logging,
        ignoring the value of all other arguments.

    config
        If a `dict`, passed to :meth:`loguru.logger.configure`.
        If not passed, :const:`DEFAULT_LOGGING_CONFIG` is used.
        Otherwise, we try and load this from disk using
        [`loguru_config.LoguruConfig`][https://github.com/erezinman/loguru-config].

        This takes precedence over `log_level`.

    log_level
        Log level to apply to the default config.
    """
    if not enable:
        logger.disable("input4mips_validation")
        return

    if config is None:
        config = DEFAULT_LOGGING_CONFIG
        if log_level is not None:
            config["handlers"][0]["level"] = log_level

        # Not sure what is going on with type hints, one for another day
        logger.configure(**config)  # type: ignore

    elif isinstance(config, dict):
        logger.configure(**config)

    else:
        config = LoguruConfig.load(config, configure=True)

    logger.enable("input4mips_validation")
