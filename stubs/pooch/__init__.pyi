from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

class DownloaderLike(Protocol):
    def __call__(
        self, url: str, output_file: str | Path, pooch: Pooch, check_only: bool = False
    ) -> bool | None: ...

class Pooch:
    @property
    def path(self) -> str: ...
    def fetch(
        self,
        fname: str,
        processor: Callable[[str, str, Pooch], str] | None = None,
        downloader: DownloaderLike | None = None,
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
    processor: Callable[[str, str, Pooch], str] | None = None,
    downloader: DownloaderLike | None = None,
    progressbar: bool = False,
) -> str: ...
def file_hash(file: Path) -> str: ...
def create(path: Path, base_url: str, registry: dict[str, str]) -> Pooch: ...

class HTTPDownloader:
    def __init__(
        self, progressbar: bool = False, chunk_size: int = 1024, **kwargs: Any
    ): ...
    def __call__(
        self, url: str, output_file: str | Path, pooch: Pooch, check_only: bool = False
    ) -> bool | None: ...
