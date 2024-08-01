"""
Tools for catching errors in validation without stopping
"""

from __future__ import annotations

from functools import wraps
from typing import Callable, Protocol, TypeVar

from loguru import logger
from typing_extensions import ParamSpec

from input4mips_validation.logging import (
    LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
    LOG_LEVEL_INFO_INDIVIDUAL_CHECK_ERROR,
)

P = ParamSpec("P")
T = TypeVar("T")


class CatchErrorDecoratorLike(Protocol):
    """
    A callable like what we return from [`get_catch_error_decorator`][input4mips_validation.validation.get_catch_error_decorator]
    """  # noqa: E501

    def __call__(
        self, func_to_call: Callable[P, T], call_purpose: str
    ) -> Callable[P, T | None]:
        """
        Get wrapped version of a function
        """


def get_catch_error_decorator(
    error_container: list[tuple[str, Exception]],
    checks_performed_container: list[str],
) -> CatchErrorDecoratorLike:
    """
    Get a decorator which can be used to collect errors without stopping the program

    Parameters
    ----------
    error_container
        The list in which to store the things being run and the caught errors

    checks_performed_container
        List which stores the checks that were performed

    Returns
    -------
    :
        Decorator which can be used to collect errors
        that occur while calling callables.
    """

    def catch_error_decorator(
        func_to_call: Callable[P, T], call_purpose: str
    ) -> Callable[P, T | None]:
        """
        Decorate a callable such that any raised errors are caught

        This allows the program to keep running even if errors occur.

        If the function raises no error,
        a confirmation that it ran successfully is logged.

        Parameters
        ----------
        func_to_call
            Function to call

        call_purpose
            A description of the purpose of the call.
            This helps us create clearer error messages for the steps which failed.

        Returns
        -------
        :
            Decorated function
        """

        @wraps(func_to_call)
        def decorated(*args: P.args, **kwargs: P.kwargs) -> T | None:
            try:
                checks_performed_container.append(call_purpose)
                res = func_to_call(*args, **kwargs)

            except Exception as exc:
                logger.log(
                    LOG_LEVEL_INFO_INDIVIDUAL_CHECK_ERROR.name,
                    f"{call_purpose} raised an error ({type(exc).__name__})",
                )
                error_container.append((call_purpose, exc))
                return None

            logger.log(
                LOG_LEVEL_INFO_INDIVIDUAL_CHECK.name,
                f"{call_purpose} ran without error",
            )

            return res

        return decorated

    return catch_error_decorator
