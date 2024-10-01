"""
Logging
"""

from __future__ import annotations

import io
import sys
from pathlib import Path
from typing import Any, Optional, Union

from loguru import logger

import input4mips_validation.logging_config

# Ensure that the logger knows about our levels
# For emojis: https://www.iemoji.com/view/emoji/766/objects/right-pointing-magnifying-glass
LOG_LEVEL_INFO_FILE = logger.level(
    name="INFO_FILE", no=15, color="<fg #3c5ffa>", icon="\u2139"
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
    name="INFO_INDIVIDUAL_CHECK", no=12, color="<fg #5db7de>", icon="\U0001f50e"
)
"""
Logging level that gives information at the level of individual checks

This is between DEBUG and LOG_LEVEL_INFO_FILE
"""

LOG_LEVEL_INFO_INDIVIDUAL_CHECK_ERROR = logger.level(
    name="INFO_INDIVIDUAL_CHECK_ERROR",
    no=LOG_LEVEL_INFO_INDIVIDUAL_CHECK.no + 1,
    color="<fg #e3494f><bold>",
    icon="\u274c",
)
"""
Logging level that gives information about a failure at the individual check level

One level higher than
[LOG_LEVEL_INFO_INDIVIDUAL_CHECK][input4mips_validation.logging.LOG_LEVEL_INFO_INDIVIDUAL_CHECK].
"""

LOG_LEVEL_INFO_DB_ENTRY = logger.level(
    name="INFO_DB_ENTRY", no=17, color="<fg #1139ed>", icon="\U0001f5c4"
)
"""
Logging level that gives information at the database entry level

This is between DEBUG and INFO
"""

LOG_LEVEL_INFO_DB_ENTRY_ERROR = logger.level(
    name="INFO_DB_ENTRY_ERROR",
    no=LOG_LEVEL_INFO_DB_ENTRY.no + 1,
    color="<fg #ff5f00><bold>",
    icon="\U0001f5c4",
)
"""
Logging level that gives information about a failure at the database entry level

One level higher than
[LOG_LEVEL_INFO_DB_ENTRY][input4mips_validation.logging.LOG_LEVEL_INFO_DB_ENTRY].
"""


def get_default_config(
    level: str = LOG_LEVEL_INFO_INDIVIDUAL_CHECK.name,
) -> dict[str, list[dict[str, Union[Union[io.TextIOWrapper, Any], str, bool]]]]:
    """
    Get default logging configuration

    Parameters
    ----------
    level
        Level to apply to the logging

    Returns
    -------
    :
        Default logging configuration
    """
    return dict(
        handlers=[
            dict(
                sink=sys.stderr,
                level=level,
                colorize=True,
                format=" - ".join(
                    [
                        "{process}",
                        "{thread}",
                        "<green>{time:!UTC}</>",
                        # "{level.icon} <lvl>{level}</>",
                        "<level>{level}</>",
                        "<cyan>{name}:{file}:{line}</>",
                        "<level>{message}</>",
                    ]
                ),
            )
        ],
    )


def setup_logging(
    enable: bool,
    logging_config: Optional[
        Union[Path, input4mips_validation.logging_config.LoggingConfigType]
    ] = None,
    logging_level: Optional[str] = None,
) -> None:
    """
    Early setup for logging.

    Parameters
    ----------
    enable
        Whether to enable the logger.

        If `False`, we explicitly disable logging,
        ignoring the value of all other arguments.

    logging_config
        If a `dict`, passed to :meth:`loguru.logger.configure`.
        If not passed, :const:`DEFAULT_LOGGING_CONFIG` is used.
        Otherwise, we try and load this from disk using
        [`loguru_config.LoguruConfig`](https://github.com/erezinman/loguru-config).

        This takes precedence over `log_level`.

    logging_level
        Log level to apply to the default config.
    """
    if not enable:
        logger.disable("input4mips_validation")
        return

    if logging_config is None:
        if logging_level is not None:
            config = get_default_config(level=logging_level)
        else:
            config = get_default_config()

        # Not sure what is going on with type hints, one for another day
        logger.configure(handlers=config["handlers"])
        input4mips_validation.logging_config.LOGGING_CONFIG = config

    elif isinstance(logging_config, dict):
        # mypy not happy about kwargs being passed here,
        # fair enough I guess
        logger.configure(**logging_config)  # type: ignore
        input4mips_validation.logging_config.LOGGING_CONFIG = logging_config

    else:
        # Type ignore while we wait for new release of logging-config
        try:
            from loguru_config import LoguruConfig  # type: ignore
        except ImportError:
            msg = (
                "[loguru-config](https://github.com/erezinman/loguru-config) "
                "is required to load config from disk. "
                "Run `pip install loguru-config` "
                "or `mamba install -c conda-forge loguru-config` "
                "or `conda install -c conda-forge loguru-config` "
                "(depending on which environment manager you're using). "
                "If that doesn't work, see installation instructions here: "
                "https://github.com/erezinman/loguru-config#installation"
            )
            print(msg)

            raise

        loguru_configurer = LoguruConfig.load(logging_config, configure=False)
        loguru_configurer.load()
        input4mips_validation.logging_config.LOGGING_CONFIG = dict(
            handlers=loguru_configurer.handlers,
            levels=loguru_configurer.levels,
            extra=loguru_configurer.extra,
            patcher=loguru_configurer.patcher,
            activation=loguru_configurer.activation,
        )

    logger.enable("input4mips_validation")

    if logging_config is not None and logging_level is not None:
        logger.warning("`logging_level` is ignored if `logging_config` is supplied")
