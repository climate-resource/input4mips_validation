class datetime:
    def __init__(  # noqa: PLR0913
        self,
        year: int,
        month: int,
        day: int,
        hour: int = 0,
        minute: int = 0,
        second: int = 0,
        microsecond: int = 0,
        dayofwk: int = -1,
        dayofyr: int = -1,
        calendar: str = "standard",
        has_year_zero: bool | None = None,
    ) -> None: ...
    @property
    def format(self) -> str: ...
    def strftime(self, format: str | None = None) -> str: ...
