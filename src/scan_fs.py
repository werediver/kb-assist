from pathlib import Path
from typing import Callable, Iterable


def scan_fs(dir: Path, path_filter: Callable[[Path], bool] | None = None) -> Iterable:
    dirs = [dir]
    while dirs:
        d = dirs.pop(0)
        for f in d.iterdir():
            if path_filter is None or path_filter(f):
                if f.is_file():
                    yield f
                elif f.is_dir():
                    dirs.append(f)
