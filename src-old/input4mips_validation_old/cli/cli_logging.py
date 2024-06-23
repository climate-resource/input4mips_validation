"""
Root for the command-line interface
"""
from __future__ import annotations

import sys
from typing import Any

import typer
from loguru import logger

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


def setup_logging(config: dict[str, Any] | None = None) -> None:
    """
    Early setup for logging.

    Parameters
    ----------
    config
        Passed to :meth:`loguru.logger.configure`. If not passed,
        :const:`DEFAULT_LOGGING_CONFIG` is used.
    """
    if config is None:
        config = DEFAULT_LOGGING_CONFIG

    logger.configure(**config)
    logger.enable("fgen")
