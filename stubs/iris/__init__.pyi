from pathlib import Path
from typing import Any

import iris.cube

class Future:
    save_split_attrs: bool

FUTURE: Future

def save(cubes: iris.cube.CubeList, out_path: str | Path, **kwargs: Any) -> None: ...
