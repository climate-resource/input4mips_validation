"""
Tools for catching errors in validation without stopping
"""

from __future__ import annotations

import traceback
from functools import wraps
from typing import Any, Callable, Protocol, TypeVar, Union

import attr
from attrs import define, field
from loguru import logger
from typing_extensions import ParamSpec

from input4mips_validation.deprecation import raise_deprecation_warning
from input4mips_validation.logging import (
    LOG_LEVEL_INFO_INDIVIDUAL_CHECK,
    LOG_LEVEL_INFO_INDIVIDUAL_CHECK_ERROR,
)

P = ParamSpec("P")
T = TypeVar("T")


def exception_info_consistent_with_passed(
    instance: ValidationResult,
    attribute: attr.Attribute[Any],
    value: Union[Any, None],
) -> None:
    """
    Check the exception information is consistent with the passed status

    Parameters
    ----------
    instance
        Instance to check

    attribute
        Attribute being set

    value
        Value being set

    Raises
    ------
    ValueError
        `value` is inconsistent with `instance.passed`.
    """
    if instance.passed and value is not None:
        msg = (
            "If the validation passed, "
            f"{attribute.name} must be `None`. "
            f"Received exception={value}"
        )
        raise ValueError(msg)

    if not instance.passed and value is None:
        msg = (
            "If the validation didn't pass, "
            f"you must provide {attribute.name}. "
            f"Received exception={value}"
        )
        raise ValueError(msg)


@define
class ValidationResult:
    """
    The result of a validation operation

    This is basically a result class,
    similar to what is often used in railway oriented programming.
    """

    description: str
    """Description of the validation operation"""

    passed: bool
    """Whether the validation passed or not"""

    result: Any = field(default=None)
    """If the validation passed, the result of the function that was called."""

    exception: Union[Exception, None] = field(
        default=None, validator=exception_info_consistent_with_passed
    )
    """If the validation failed, the exception that was raised."""

    exception_info: Union[str, None] = field(
        default=None, validator=exception_info_consistent_with_passed
    )

    """
    If the validation failed, the exception information.

    This is typically created with `traceback.format_exc`.
    """

    @property
    def failed(self) -> bool:
        """Whether the validation failed or not"""
        return not self.passed


class ValidationResultsStoreError(ValueError):
    """
    Raised to signal that an error occured during validation

    Specifically, that a
    [`ValidationResultsStore`][input4mips_validation.validation.error_catching.ValidationResultsStore]
    object contains failed validation results.
    """

    def __init__(self, vrs: ValidationResultsStore) -> None:
        """
        Initialise the error

        Parameters
        ----------
        vrs
            The validation results store that contains failures.
        """
        error_msg_l: list[str] = [
            f"Checks passing: {vrs.checks_summary_str(passing=True)}",
            f"Checks failing: {vrs.checks_summary_str(passing=False)}",
        ]

        checks_failing = vrs.checks_failing
        if checks_failing:
            error_msg_l.append("")
            error_msg_l.append("Failing checks details")
            for gcf in checks_failing:
                error_msg_l.append("")
                error_msg_l.append(
                    f"{gcf.description} ({type(gcf.exception).__name__})"
                )
                if gcf.exception_info is None:
                    msg = "Should have an exception here"
                    raise AssertionError(msg)

                error_msg_l.extend(gcf.exception_info.splitlines())

        error_msg = "\n".join(error_msg_l)

        super().__init__(error_msg)


@define
class ValidationResultsStore:
    """
    Store for validation results
    """

    validation_results: list[ValidationResult] = field(factory=list)
    """Stored validation results"""

    @property
    def all_passed(self) -> bool:
        """Whether all the validation steps passed or not"""
        return all(v.passed for v in self.validation_results)

    @property
    def checks_passing(self) -> tuple[ValidationResult, ...]:
        """Checks that passed"""
        return tuple(v for v in self.validation_results if v.passed)

    @property
    def checks_failing(self) -> tuple[ValidationResult, ...]:
        """Checks that failed"""
        return tuple(v for v in self.validation_results if v.failed)

    def wrap(
        self, func_to_call: Callable[P, T], func_description: str
    ) -> Callable[P, ValidationResult]:
        """
        Wrap a validation function

        The results of calling the validation function will be stored by `self`.

        Parameters
        ----------
        func_to_call
            Function to call

        func_description
            A description of `func_to_call`.

            This helps us create clearer messages when processing validation results.

        Returns
        -------
        :
            The wrapped function.

            The wrapped function is altered so it always returns a result,
            irrespective of whether `func_to_call` raised an error not.
        """

        @wraps(func_to_call)
        def decorated(*args: P.args, **kwargs: P.kwargs) -> ValidationResult:
            try:
                res_func = func_to_call(*args, **kwargs)
                res = ValidationResult(
                    description=func_description,
                    passed=True,
                    result=res_func,
                )
                logger.log(
                    LOG_LEVEL_INFO_INDIVIDUAL_CHECK.name,
                    f"{func_description} ran without error",
                )

            except Exception as exc:
                logger.log(
                    LOG_LEVEL_INFO_INDIVIDUAL_CHECK_ERROR.name,
                    f"{func_description} raised an error ({type(exc).__name__})",
                )
                res = ValidationResult(
                    description=func_description,
                    passed=False,
                    exception=exc,
                    exception_info=traceback.format_exc(),
                )

            self.validation_results.append(res)

            return res

        return decorated

    def raise_if_errors(self) -> None:
        """
        Raise a `ValidationError` if any of the validation steps failed

        Raises
        ------
        ValidationError
            One of the validation steps in `self.validation_results` failed.
        """
        if not self.all_passed:
            raise ValidationResultsStoreError(self)

    def checks_summary_str(self, passing: bool) -> str:
        """
        Get a summary of the checks we have performed

        Parameters
        ----------
        passing
            Should we return the summary as the number of checks
            which are passing (`True`) or failing (`False`)?

        Returns
        -------
        :
            Summary of the checks
        """
        denominator = len(self.validation_results)
        if passing:
            numerator = len(self.checks_passing)

        else:
            numerator = len(self.checks_failing)

        pct = numerator / denominator * 100
        return f"{pct:.2f}% ({numerator} / {denominator})"


class CatchErrorDecoratorLike(Protocol):
    """
    A callable like what we return from `get_catch_error_decorator`

    See [`get_catch_error_decorator`][input4mips_validation.validation.error_catching.get_catch_error_decorator]
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

    /// danger | Deprecated
    `get_catch_error_decorator` was deprecated in v0.12.0.
    It will be removed in v0.14.0.
    Please use [`ValidationResultsStore`][input4mips_validation.validation.error_catching.ValidationResultsStore]
    instead because it provides greater control.
    ///

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
    """  # noqa: E501
    raise_deprecation_warning(
        "get_catch_error_decorator",
        removed_in="0.14.0",
        use_instead="`ValidationResultStore`",
    )

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
