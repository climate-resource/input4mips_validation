"""
Exceptions used throughout
"""
import re


class DoesNotMatchRegexpError(AssertionError):
    """
    Raised when metadata does not match some expected regular expression
    """

    def __init__(self, high_level_msg: str, regexp: re.Pattern[str]):
        """
        Initialise the error

        Parameters
        ----------
        high_level_msg
            High-level message which describes the issue.

        regexp
            Regular expression we expected the value to meet.
        """
        msg = (
            f"{high_level_msg}. "
            f"(Specifically, the value does not match this regexp: {regexp})"
        )

        super().__init__(msg)
