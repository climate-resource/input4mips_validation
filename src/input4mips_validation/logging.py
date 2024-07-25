"""
Logging for the command-line interface
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Optional

from loguru import logger

# Type ignore while we wait for
# https://github.com/erezinman/loguru-config/pull/2
from loguru_config import LoguruConfig  # type: ignore

LOG_LEVEL_INFO_FILE: int = 15
"""
Logging level that gives information at the file level

This is between DEBUG and INFO
"""

LOG_LEVEL_INFO_INDIVIDUAL_CHECK: int = 14
"""
Logging level that gives information at the level of individual checks

This is between DEBUG and LOG_LEVEL_INFO_FILE
"""


DEFAULT_LOGGING_CONFIG = dict(
    handlers=[
        dict(
            sink=sys.stderr,
            level=LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
            colorize=True,
            format=" - ".join(
                [
                    "<green>{time:!UTC}</>",
                    "<lvl>{level}</>",
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
    config: Optional[Path, dict[str, Any]] = None,
    log_level: Optional[int] = None,
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
        # Not sure what is going on with type hints, one for another day
        config = DEFAULT_LOGGING_CONFIG
        if log_level is not None:
            config["handlers"][0]["level"] = log_level

        logger.configure(**config)  # type: ignore

    elif isinstance(config, dict):
        logger.configure(**config)

    else:
        config = LoguruConfig.load(config, configure=True)

    logger.enable("input4mips_validation")
