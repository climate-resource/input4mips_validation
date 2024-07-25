"""
Logging for the command-line interface
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Union

import typer
from loguru import logger

# Type ignore while we wait for
# https://github.com/erezinman/loguru-config/pull/2
from loguru_config import LoguruConfig  # type: ignore

app = typer.Typer()

DEFAULT_LOGGING_CONFIG = dict(
    handlers=[
        dict(
            sink=sys.stderr,
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
    enable: bool, config: Union[Path, dict[str, Any]] | None = None
) -> None:
    """
    Early setup for logging.

    Parameters
    ----------
    enable
        Whether to enable the logger.

        If `False`, we explicitly disable logging.

    config
        If a `dict`, passed to :meth:`loguru.logger.configure`.
        If not passed, :const:`DEFAULT_LOGGING_CONFIG` is used.
        Otherwise, we try and load this from disk using
        [`loguru_config.LoguruConfig`][https://github.com/erezinman/loguru-config].
    """
    if not enable:
        logger.disable("input4mips_validation")
        return

    if config is None:
        # Not sure what is going on with type hints, one for another day
        logger.configure(**DEFAULT_LOGGING_CONFIG)  # type: ignore

    elif isinstance(config, dict):
        logger.configure(**config)

    else:
        config = LoguruConfig.load(config, configure=True)

    logger.enable("input4mips_validation")
