# Built-in imports
from pathlib import Path
from typing import Literal

# Third-party imports
from psutil import disk_partitions


def get_filesystem_type(path: str | Path) -> str | None:
    path = Path(path).resolve()

    best_part = max(
        (part for part in disk_partitions(all=True) if path.as_posix().startswith(part.mountpoint)),
        key=lambda part: len(part.mountpoint),
        default=None,
    )

    return best_part.fstype if best_part else None


def looks_like_a_ram_directory(path: str | Path) -> bool:
    return get_filesystem_type(path) in ["tmpfs", "devtmpfs", "ramfs"]
