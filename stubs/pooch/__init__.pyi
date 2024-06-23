from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

class Pooch:
    @property
    def path(self) -> str: ...
    def fetch(
        self,
        fname: str,
        processor: None | Callable[[], str] = None,
        downloader: None | Callable[[], None] = None,
        progressbar: bool = False,
    ) -> str: ...

class Unzip:
    def __init__(
        self, members: list[str] | None = None, extract_dir: str | None = None
    ): ...
    def __call__(self, fname: str, action: str, pooch: Pooch) -> list[Path]: ...

def retrieve(
    url: str,
    known_hash: str | None,
    fname: str | None = None,
    path: Path | None = None,
    processor: None | Callable[[str, str, Pooch], str] = None,
    progressbar: bool = False,
) -> str: ...
def file_hash(file: Path) -> str: ...
