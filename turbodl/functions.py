# Built-in imports
from os import PathLike
from pathlib import Path

# Third-party imports
from psutil import disk_partitions, disk_usage


def get_filesystem_type(path: str | Path) -> str | None:
    """
    Get the type of filesystem at the given path.

    Args:
        path (str | Path): The path to get the filesystem type for.

    Returns:
        str | None: The type of filesystem at the path, or None if the path is invalid.
    """

    # Convert path to Path object
    path = Path(path).resolve()

    # Find the partition that the path is on, based on the mountpoint
    best_part = max(
        (part for part in disk_partitions(all=True) if path.as_posix().startswith(part.mountpoint)),
        key=lambda part: len(part.mountpoint),
        default=None,
    )

    # Return the filesystem type of the partition
    return best_part.fstype if best_part else None


def has_available_space(path: str | PathLike, required_size: int, minimum_space: int = 1) -> bool:
    """
    Check if there is sufficient space available at the specified path.

    Args:
        path (str | PathLike): The file or directory path to check for available space.
        required_size (int): The size of the file or data to be stored, in bytes.
        minimum_space (int): The minimum additional space to ensure, in gigabytes. Defaults to 1.

    Returns:
        bool: True if there is enough available space, False otherwise.
    """

    # Convert path to Path object
    path = Path(path)

    # Calculate the total required space including the minimum space buffer
    required_space = required_size + (minimum_space * 1024 * 1024 * 1024)

    # Get the disk usage statistics for the appropriate path (parent if it's a file or doesn't exist)
    disk_usage_obj = disk_usage(path.parent.as_posix() if path.is_file() or not path.exists() else path.as_posix())

    # Return True if there is enough free space, False otherwise
    return bool(disk_usage_obj.free >= required_space)


def looks_like_a_ram_directory(path: str | Path) -> bool:
    """
    Check if a path is a temporary RAM-backed filesystem.

    Args:
        path (str | Path): The path to check.

    Returns:
        bool: True if the path is a temporary RAM-backed filesystem, False otherwise.
    """

    # Get the filesystem type of the path
    filesystem_type = get_filesystem_type(path)

    # Check if the filesystem type is a known RAM-backed filesystem
    return filesystem_type in {"tmpfs", "devtmpfs", "ramfs"}
