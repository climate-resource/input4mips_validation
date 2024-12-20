from __future__ import annotations

import datetime as dt

import xarray as xr

class datetime:
    def __init__(
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
    def __sub__(self, other: dt.timedelta) -> datetime: ...
    @property
    def format(self) -> str: ...
    @property
    def day(self) -> int: ...
    @property
    def month(self) -> int: ...
    def isoformat(self) -> str: ...
    def strftime(self, format: str | None = None) -> str: ...

def num2date(
    times: float | xr.DataArray, units: str, calendar: str = "standard"
) -> datetime: ...
